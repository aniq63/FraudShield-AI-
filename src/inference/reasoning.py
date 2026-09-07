import os
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from utils.logging import logger
from utils.exception import FraudShieldException


# ── System prompt ──────────────────────────────────────────────────────────
# The LLM receives the raw transaction fields and the ML prediction result.
# It must return ONLY a structured reasoning block — no small talk.

SYSTEM_PROMPT = """You are FraudShield AI, an expert fraud analyst at a major bank.

A machine learning model has scored the following financial transaction.
Your job is to explain the decision in plain English that a bank analyst
or customer can understand.

=== TRANSACTION DETAILS ===
{transaction_row}

=== MODEL PREDICTION ===
{model_predictions}

Write a concise fraud analysis report using EXACTLY this structure:

DECISION: [APPROVED / BLOCKED]
FRAUD PROBABILITY: [e.g. 94.3%]

RISK FACTORS IDENTIFIED:
- [factor 1 — be specific, e.g. "Transaction amount of $8,400 is 12x above this user's average of $700"]
- [factor 2]
- [factor 3 — add more if genuinely relevant, omit if not]

REASONING:
[2-4 sentences explaining why this combination of factors led to the decision.
Be specific about which features drove the score up or down.]

RECOMMENDED ACTION:
[One clear sentence: what the bank should do next — approve, block, request OTP, flag for manual review, etc.]

Rules:
- Never invent data that is not in the transaction details.
- If the decision is APPROVED, still explain why the transaction looks legitimate.
- Keep the whole response under 200 words.
- No preamble, no sign-off, no markdown headers — just the structure above.
"""


class FraudReasoningAI:
    """
    Wraps a Groq-hosted LLM to generate human-readable fraud reasoning
    for a transaction + ML prediction result pair.

    Usage
    -----
    reasoner = FraudReasoningAI()
    explanation = reasoner.explain(transaction_dict, prediction_dict)
    """

    def __init__(self, model_name: str = None):
        try:
            # ── 1. Load env and verify key ─────────────────────────────
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY", "").strip()

            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY not found. Add it to your .env file."
                )

            # ── 2. Resolve model name ──────────────────────────────────
            # Priority: constructor arg > env var > hardcoded default
            self.model_name = (
                model_name
                or os.getenv("GROQ_MODEL_NAME", "").strip()
                or "llama-3.3-70b-versatile"
            )

            logger.info(f"FraudReasoningAI initialising with model: {self.model_name}")

            # ── 3. Build LangChain chain ───────────────────────────────
            self.prompt = PromptTemplate(
                template=SYSTEM_PROMPT,
                input_variables=["transaction_row", "model_predictions"],
            )

            self.llm = ChatGroq(
                model=self.model_name,
                api_key=api_key,
                temperature=0.2,      # low temp = consistent, factual output
                # GPT-OSS uses part of the completion budget for internal
                # reasoning before emitting the visible explanation.
                max_tokens=800,
            )

            # prompt → LLM → plain string
            self.chain = self.prompt | self.llm | StrOutputParser()

            logger.info("FraudReasoningAI ready.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain(self, transaction: dict, prediction: dict) -> str:
        """
        Generate a fraud reasoning report.

        Parameters
        ----------
        transaction : dict
            Raw transaction dict from TransactionGenerator
            (simulation_mode already stripped by predictor is fine,
             but this method handles it safely either way).

        prediction : dict
            Output dict from FraudPredictor.predict(), containing:
                fraud_probability, decision, threshold

        Returns
        -------
        str — structured reasoning report from the LLM
        """
        try:
            transaction_row = self._format_reasoning_transaction(transaction)
            model_predictions = self._format_prediction(prediction)

            logger.info(
                f"Requesting LLM reasoning for decision={prediction.get('decision')} "
                f"prob={prediction.get('fraud_probability')}"
            )

            prompt_values = {
                "transaction_row": transaction_row,
                "model_predictions": model_predictions,
            }
            reasoning = ""
            for _ in range(2):
                reasoning = self.chain.invoke(prompt_values)
                if reasoning and reasoning.strip():
                    break

            if not reasoning or not reasoning.strip():
                logger.warning("LLM returned empty reasoning; using risk summary.")
                return self._fallback_reasoning(transaction, prediction)

            logger.info("LLM reasoning received.")
            return reasoning.strip()

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def explain_batch(
        self, transactions: list[dict], predictions: list[dict]
    ) -> list[str]:
        """
        Generate reasoning for a batch.
        transactions[i] pairs with predictions[i].
        """
        try:
            if len(transactions) != len(predictions):
                raise ValueError(
                    "transactions and predictions lists must be the same length."
                )

            logger.info(f"Generating reasoning for {len(transactions)} transactions.")

            return [
                self.explain(txn, pred)
                for txn, pred in zip(transactions, predictions)
            ]

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _format_transaction(self, transaction: dict) -> str:
        """
        Convert transaction dict to a clean key: value block.
        Strips simulator-only and internal keys for cleaner LLM input.
        """
        skip_keys = {"simulation_mode", "_id", "id"}

        lines = []
        for k, v in transaction.items():
            if k in skip_keys:
                continue
            lines.append(f"  {k}: {v}")

        return "\n".join(lines) if lines else "(no transaction data)"

    def _format_reasoning_transaction(self, transaction: dict) -> str:
        """Keep the fraud explanation prompt focused on model-relevant fields."""
        keys = (
            "transaction_amount",
            "category",
            "transaction_hour",
            "buyer_age",
            "distance_km",
            "is_night_transaction",
            "buyer_gender",
        )
        focused = {key: transaction.get(key) for key in keys if key in transaction}
        return self._format_transaction(focused)

    def _fallback_reasoning(self, transaction: dict, prediction: dict) -> str:
        """Keep blocked alerts useful when the provider returns no content."""
        factors = []
        if transaction.get("is_night_transaction") or transaction.get("transaction_hour", 12) >= 22 or transaction.get("transaction_hour", 12) <= 3:
            factors.append("late-night activity")
        if transaction.get("transaction_amount", 0) >= 400:
            factors.append("elevated transaction amount")
        if transaction.get("distance_km", 0) >= 100:
            factors.append("unusual geographic distance")
        factor_text = ", ".join(factors) or "the combined transaction risk signals"
        return (
            f"Automated risk summary: transaction blocked with a "
            f"{prediction.get('fraud_probability', 0) * 100:.1f}% fraud probability. "
            f"Risk factors: {factor_text}."
        )

    def _format_prediction(self, prediction: dict) -> str:
        """
        Render the ML prediction result as a readable block.
        """
        prob_pct = round(prediction.get("fraud_probability", 0) * 100, 2)
        decision = prediction.get("decision", "UNKNOWN")
        threshold = prediction.get("threshold", 0.50)

        return (
            f"  Decision:          {decision}\n"
            f"  Fraud Probability: {prob_pct}%\n"
            f"  Threshold used:    {threshold}\n"
            f"  (Scores >= {threshold * 100:.0f}% are blocked)"
        )
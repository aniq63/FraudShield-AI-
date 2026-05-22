import sys
import time
import threading
import queue

from src.simulator.transaction_generator import TransactionGenerator
from src.inference.predictor import FraudPredictor
from src.inference.reasoning import FraudReasoningAI
from src.utils.logging import logger
from src.utils.exception import FraudShieldException


# Shared in-memory queue — producer puts, consumer gets
TRANSACTION_QUEUE: queue.Queue = queue.Queue()


# ══════════════════════════════════════════════════════════════════════════
# PRODUCER
# ══════════════════════════════════════════════════════════════════════════

class TransactionProducer:
    """
    Generates transactions via TransactionGenerator and pushes them
    onto the shared in-memory queue. Does not wait for predictions.
    """

    def __init__(self, collection_name: str = "transactions_data"):
        try:
            self.generator = TransactionGenerator(collection_name)
            logger.info("TransactionProducer ready.")
        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def produce(self, num_transactions: int, mode: str = "normal") -> None:
        """
        Generate `num_transactions` transactions in the given mode
        and push each onto the queue. Returns immediately.

        Parameters
        ----------
        num_transactions : int   e.g. 10, 100
        mode             : str   "normal" | "stolen_card" | "geo_attack" | "velocity_burst"
                                 (spaces also accepted — generator normalises internally)
        """
        try:
            logger.info(
                f"Producing {num_transactions} transactions | mode={mode}"
            )

            transactions = self.generator.generate_transactions(
                num_transactions, mode
            )

            for txn in transactions:
                TRANSACTION_QUEUE.put(txn)

            logger.info(
                f"All {num_transactions} transactions queued."
            )

        except Exception as e:
            raise FraudShieldException(str(e), sys)


# ══════════════════════════════════════════════════════════════════════════
# CONSUMER
# ══════════════════════════════════════════════════════════════════════════

class FraudPipelineConsumer:
    """
    Background thread that drains the queue one transaction at a time,
    runs ML prediction + LLM reasoning, then fires result_callback.

    Usage
    -----
    consumer = FraudPipelineConsumer(result_callback=my_fn)
    consumer.start()
    # ... producer pushes transactions ...
    consumer.stop()
    """

    def __init__(
        self,
        result_callback=None,
        s3_model_key: str = "models/best_model.pkl",
        s3_preprocessor_key: str = "models/preprocessor.pkl",
    ):
        try:
            # Predictor loads both model + preprocessor from S3
            self.predictor = FraudPredictor(
                s3_model_key=s3_model_key,
                s3_preprocessor_key=s3_preprocessor_key,
            )

            self.reasoner = FraudReasoningAI()

            # Callback is called with the final result dict after each transaction
            self.result_callback = result_callback or (lambda r: None)

            self._running = False
            self._thread: threading.Thread | None = None

            logger.info("FraudPipelineConsumer ready.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ── lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the consumer loop in a daemon background thread."""
        self._running = True
        self._thread = threading.Thread(
            target=self._consume_loop,
            daemon=True,
            name="fraud-consumer",
        )
        self._thread.start()
        logger.info("Consumer thread started.")

    def stop(self) -> None:
        """Signal the consumer to stop and wait for it to finish."""
        logger.info("Stopping consumer...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Consumer stopped.")

    # ── core loop ──────────────────────────────────────────────────────────

    def _consume_loop(self) -> None:
        logger.info("Listening on in-memory transaction queue...")

        while self._running:
            try:
                # Block up to 1 s waiting for a transaction
                transaction = TRANSACTION_QUEUE.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                result = self._process(transaction)
                self.result_callback(result)
            except Exception as e:
                # Log but never crash the consumer — next transaction must still run
                logger.error(f"Error processing transaction: {e}")
            finally:
                TRANSACTION_QUEUE.task_done()

    # ── per-transaction pipeline ───────────────────────────────────────────

    def _process(self, transaction: dict) -> dict:
        """
        Full pipeline for one transaction:
            raw dict → ML prediction → LLM reasoning (BLOCKED only) → result
        """
        start = time.time()

        # ── ML prediction ──────────────────────────────────────────────
        prediction = self.predictor.predict(transaction)

        # ── LLM reasoning — only for blocked transactions ──────────────
        # Approved transactions don't need an explanation, and calling
        # the LLM for every approval wastes latency and API quota.
        reasoning = None
        if prediction["decision"] == "BLOCKED":
            try:
                reasoning = self.reasoner.explain(transaction, prediction)
            except Exception as llm_err:
                logger.warning(f"LLM reasoning failed: {llm_err}")
                reasoning = "Reasoning unavailable."

        latency_ms = round((time.time() - start) * 1000, 1)

        result = {
            # ── shown on dashboard ─────────────────────────────────────
            "transaction_id":    prediction["transaction_id"],
            "decision":          prediction["decision"],
            "fraud_probability": prediction["fraud_probability"],
            "reasoning":         reasoning,

            # ── full transaction for the live feed table ───────────────
            "transaction":       transaction,

            # ── meta ───────────────────────────────────────────────────
            "simulation_mode":   transaction.get("simulation_mode", "unknown"),
            "latency_ms":        latency_ms,
        }

        logger.info(
            f"[{result['simulation_mode']}] "
            f"{result['decision']} | "
            f"prob={result['fraud_probability']} | "
            f"{latency_ms}ms"
        )

        return result
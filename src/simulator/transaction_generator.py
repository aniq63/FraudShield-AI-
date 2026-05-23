import sys
import random
import numpy as np
import pandas as pd

from src.components.data_ingestion import DataIngestion
from src.utils.logging import logger
from src.utils.exception import FraudShieldException


# ── Fraud distribution facts from investigate_model.py ────────────────────
#
# is_night_transaction : fraud=80.5%  normal=22.8%   importance=42.5%
# transaction_amount   : fraud p50=$317  p90=$1002    importance=29.1%
# buyer_age            : fraud mean=59.8 normal=45.5   importance=5.7%
# category (fraud)     : grocery_pos=34% gas_transport=17% shopping_pos=7%
#                        shopping_net=22% misc_net=10% misc_pos=2%
#
# Simulator was sending: amounts $2000-$9500 (above p90=$1002, never seen
# as fraud by model), categories shopping_net/travel/misc_net (low fraud
# rate in training), no night flag forced.
# That's why everything was approved.
# ─────────────────────────────────────────────────────────────────────────

# Hours the model associates with fraud (is_night_transaction = 1: 22-23 or 0-3)
_NIGHT_HOURS = [22, 23, 0, 1, 2, 3]

# Top fraud categories from training data (weighted by actual frequency)
_FRAUD_CATEGORIES = [
    "grocery_pos",    # 34.1% of fraud
    "shopping_net",   # 22.0%
    "gas_transport",  # 17.1%
    "misc_net",       #  9.8%
    "shopping_pos",   #  7.3%
    "misc_pos",       #  2.4%
]

_FRAUD_CATEGORY_WEIGHTS = [0.341, 0.220, 0.171, 0.098, 0.073, 0.024]

# Amount ranges calibrated to training fraud distribution
# fraud p50=$317  p90=$1002  max=$1251
# We stay within the distribution the model was trained on.
_FRAUD_AMOUNT_LOW  = (50,   400)   # common fraud — below p50
_FRAUD_AMOUNT_MID  = (400,  1000)  # typical fraud — p50–p90
_FRAUD_AMOUNT_HIGH = (1000, 1250)  # high-end fraud — above p90 but within range


def _pick_fraud_amount(tier: str = "mixed") -> float:
    """
    Pick a transaction amount within the fraud distribution the model knows.
    tier: "low" | "mid" | "high" | "mixed"
    """
    if tier == "low":
        return round(random.uniform(*_FRAUD_AMOUNT_LOW), 2)
    elif tier == "mid":
        return round(random.uniform(*_FRAUD_AMOUNT_MID), 2)
    elif tier == "high":
        return round(random.uniform(*_FRAUD_AMOUNT_HIGH), 2)
    else:  # mixed — sample proportionally to training fraud
        r = random.random()
        if r < 0.50:   return round(random.uniform(*_FRAUD_AMOUNT_LOW), 2)
        elif r < 0.85: return round(random.uniform(*_FRAUD_AMOUNT_MID), 2)
        else:          return round(random.uniform(*_FRAUD_AMOUNT_HIGH), 2)


def _pick_fraud_category() -> str:
    return random.choices(_FRAUD_CATEGORIES, weights=_FRAUD_CATEGORY_WEIGHTS, k=1)[0]


def _pick_older_age(txn: dict) -> dict:
    """
    Fraud buyer_age mean=59.8. Push age upward if the sampled buyer is young.
    We only override if current age is below 50 to keep it realistic.
    """
    current_age = txn.get("buyer_age", 45)
    if current_age < 50:
        txn["buyer_age"] = random.randint(55, 80)
    return txn


class TransactionGenerator:
    """
    Generates realistic transactions for simulation using historical MongoDB data.

    All mutations are calibrated against the actual training fraud distribution
    found by investigate_model.py. The model's top signals are:
        1. is_night_transaction  (42.5% importance) — most mutations force night hours
        2. transaction_amount_log (29.1%)            — amounts stay within fraud range
        3. buyer_age              (5.7%)             — older buyers for fraud modes
        4. category               varies             — fraud-dominant categories used
    """

    def __init__(self, collection_name: str, limit: int = 10000):
        try:
            logger.info("Loading historical transactions...")
            ingestion = DataIngestion(collection_name, limit=limit)
            self.df = ingestion.fetch_data()
            logger.info(f"Loaded transactions base shape: {self.df.shape}")
        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ── timestamp helper ───────────────────────────────────────────────────

    def _apply_live_timestamps(self, txn: dict, force_night: bool = False) -> dict:
        """
        Update display-only date/time fields to now.
        Does NOT overwrite transaction_hour unless force_night=True.

        force_night=True: sets transaction_hour to a random night hour (22-3)
        and is_night_transaction=1, which is the #1 fraud signal.
        """
        now = pd.Timestamp.now()
        txn["transaction_date"] = now.strftime("%Y-%m-%d")
        txn["transaction_time"] = now.strftime("%H:%M:%S")
        txn["unix_time"]        = int(now.timestamp())

        if force_night:
            night_hour = random.choice(_NIGHT_HOURS)
            txn["transaction_hour"]      = night_hour
            txn["is_night_transaction"]  = 1   # pre-compute so it's clear in logs
        # else: transaction_hour stays as sampled from historical data

        return txn

    # ── mode mutators ──────────────────────────────────────────────────────

    def mutate_to_normal(self, txn: dict) -> dict:
        """
        Baseline — no mutations. Represents legitimate user behaviour.
        """
        txn["simulation_mode"] = "normal"
        return self._apply_live_timestamps(txn, force_night=False)

    def mutate_to_stolen_card(self, txn: dict) -> dict:
        """
        Stolen card pattern:
        - Night hour (80.5% of training fraud is at night)
        - Amount within training fraud distribution ($50–$1250)
        - Category from top fraud categories
        - Older buyer age (fraud mean=59.8)

        Previous bug: was sending $2000–$9500 which the model never
        associated with fraud (training fraud p90=$1002), and not
        forcing night hours (the #1 importance feature).
        """
        txn["transaction_amount"] = _pick_fraud_amount("mixed")
        txn["category"]           = _pick_fraud_category()
        txn["simulation_mode"]    = "stolen_card"
        txn = _pick_older_age(txn)
        return self._apply_live_timestamps(txn, force_night=True)

    def mutate_to_geo_attack(self, txn: dict) -> dict:
        """
        Geographic anomaly — merchant location is far from buyer home.
        Also forces night hour and fraud-range amount for compound signal.

        distance_km has low importance (0.77%) on its own, but combined
        with night + amount it contributes to the decision boundary.
        """
        lat_offset  = random.choice([-1, 1]) * random.uniform(35.0, 75.0)
        long_offset = random.choice([-1, 1]) * random.uniform(70.0, 140.0)

        txn["merchant_lat"]  = float(np.clip(
            txn.get("buyer_lat", 0.0) + lat_offset, -90.0, 90.0
        ))
        txn["merchant_long"] = float(np.clip(
            txn.get("buyer_long", 0.0) + long_offset, -180.0, 180.0
        ))

        # Add amount + category signal on top of geo anomaly
        txn["transaction_amount"] = _pick_fraud_amount("mid")
        txn["category"]           = _pick_fraud_category()
        txn["simulation_mode"]    = "geo_attack"
        txn = _pick_older_age(txn)
        return self._apply_live_timestamps(txn, force_night=True)

    def mutate_to_velocity_burst(self, txn: dict) -> dict:
        """
        Rapid late-night transactions — night hour is the primary signal.
        Amount mid-range, gas_transport/grocery_pos most common for this pattern.
        """
        txn["transaction_amount"] = _pick_fraud_amount("mid")
        txn["category"]           = random.choice(["gas_transport", "grocery_pos", "misc_pos"])
        txn["simulation_mode"]    = "velocity_burst"
        txn = _pick_older_age(txn)

        # force_night here instead of manually setting hour after
        return self._apply_live_timestamps(txn, force_night=True)

    # ── batch generation ───────────────────────────────────────────────────

    def generate_transactions(
        self,
        num_transactions: int,
        mode: str = "normal",
    ) -> list[dict]:
        """
        Generate a batch of transactions in the given mode.
        Samples entire batch in one pass.
        """
        try:
            clean_mode = mode.lower().replace(" ", "_")
            logger.info(
                f"Generating {num_transactions} transactions in mode: {clean_mode}"
            )

            mutator_map = {
                "normal":         self.mutate_to_normal,
                "stolen_card":    self.mutate_to_stolen_card,
                "geo_attack":     self.mutate_to_geo_attack,
                "velocity_burst": self.mutate_to_velocity_burst,
            }

            if clean_mode not in mutator_map:
                raise ValueError(f"Unknown simulation mode: {mode!r}")

            mutator  = mutator_map[clean_mode]
            sampled  = (
                self.df.sample(n=num_transactions, replace=True)
                .to_dict(orient="records")
            )
            transactions = [mutator(txn) for txn in sampled]

            logger.info("Transaction generation complete.")
            return transactions

        except Exception as e:
            raise FraudShieldException(str(e), sys)
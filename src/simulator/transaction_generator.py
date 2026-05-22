import sys
import random
import numpy as np
import pandas as pd

from src.components.data_ingestion import DataIngestion
from src.utils.logging import logger
from src.utils.exception import FraudShieldException


class TransactionGenerator:
    """
    Generates realistic transactions for simulation using historical MongoDB data.
    Optimized for high-throughput batch generation and downstream model alignment.
    """

    def __init__(self, collection_name: str, limit: int = 10000):
        try:
            logger.info("Loading historical transactions...")
            ingestion = DataIngestion(collection_name, limit=limit)
            self.df = ingestion.fetch_data()
            
            logger.info(f"Loaded transactions base shape: {self.df.shape}")
        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def _apply_live_timestamps(self, txn: dict) -> dict:
        """
        Updates historical records with the current live system time
        so streaming visual tools and features mirror a real live feed.
        """
        now = pd.Timestamp.now()
        txn["transaction_date"] = now.strftime("%Y-%m-%d")
        txn["transaction_time"] = now.strftime("%H:%M:%S")
        txn["transaction_hour"] = now.hour
        txn["unix_time"] = int(now.timestamp())
        return txn

    def mutate_to_normal(self, txn: dict) -> dict:
        txn["simulation_mode"] = "normal"
        return self._apply_live_timestamps(txn)

    def mutate_to_stolen_card(self, txn: dict) -> dict:
        """Simulates high-value card testing anomalies."""
        txn["transaction_amount"] = round(random.uniform(2000.0, 9500.0), 2)
        
        # Aligned with valid categories tracked in predictor.py
        txn["category"] = random.choice(["shopping_net", "travel", "misc_net"])
        txn["simulation_mode"] = "stolen_card"
        
        return self._apply_live_timestamps(txn)

    def mutate_to_geo_attack(self, txn: dict) -> dict:
        """Simulates a rapid distance anomaly relative to the buyer's home base."""
        # Intentionally offset coords far away from home base instead of dropping into oceans
        lat_offset = random.choice([-1, 1]) * random.uniform(35.0, 75.0)
        long_offset = random.choice([-1, 1]) * random.uniform(70.0, 140.0)
        
        txn["merchant_lat"] = float(np.clip(txn.get("buyer_lat", 0.0) + lat_offset, -90.0, 90.0))
        txn["merchant_long"] = float(np.clip(txn.get("buyer_long", 0.0) + long_offset, -180.0, -180.0))
        txn["simulation_mode"] = "geo_attack"
        
        return self._apply_live_timestamps(txn)

    def mutate_to_velocity_burst(self, txn: dict) -> dict:
        """Simulates high frequency late-night transactions."""
        txn["transaction_amount"] = round(random.uniform(450.0, 3500.0), 2)
        txn["simulation_mode"] = "velocity_burst"
        
        txn = self._apply_live_timestamps(txn)
        # Explicitly force an irregular high-risk early morning hour
        txn["transaction_hour"] = random.choice([0, 1, 2, 3])
        return txn

    def generate_transactions(self, num_transactions: int, mode: str = "normal") -> list[dict]:
        """
        Generate multiple transactions optimized via vectorized single-pass sampling.
        """
        try:
            clean_mode = mode.lower().replace(" ", "_")
            logger.info(f"Generating {num_transactions} transactions in mode: {clean_mode}")

            # Optimization: Sample the entire batch in one pass rather than running loops
            sampled_records = (
                self.df.sample(n=num_transactions, replace=True)
                .to_dict(orient="records")
            )

            # Map configuration methods directly to avoid long conditional branches
            mutator_map = {
                "normal": self.mutate_to_normal,
                "stolen_card": self.mutate_to_stolen_card,
                "geo_attack": self.mutate_to_geo_attack,
                "velocity_burst": self.mutate_to_velocity_burst
            }

            if clean_mode not in mutator_map:
                raise ValueError(f"Unknown execution simulation mode: {mode}")

            mutator = mutator_map[clean_mode]
            
            # Process records in-place
            transactions = [mutator(txn) for txn in sampled_records]

            logger.debug("Transaction transformation batch complete.")
            return transactions

        except Exception as e:
            raise FraudShieldException(str(e), sys)
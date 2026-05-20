import sys
import random
import pandas as pd

from src.components.data_ingestion import DataIngestion
from src.utils.logging import logger
from src.utils.exception import FraudShieldException


class TransactionGenerator:
    """
    Generates realistic transactions for simulation
    using historical MongoDB transaction data.
    """

    def __init__(self, collection_name: str, limit: int = 10000):

        try:
            logger.info(
                "Loading historical transactions..."
            )

            ingestion = DataIngestion(
                collection_name,
                limit=limit
            )

            self.df = ingestion.fetch_data()

            logger.info(
                f"Loaded transactions: {self.df.shape}"
            )

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def sample_real_transaction(self):

        """
        Randomly sample one real transaction.
        """

        try:

            transaction = (
                self.df.sample(1)
                .to_dict(orient="records")[0]
            )

            return transaction

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def generate_normal_transaction(self):

        txn = self.sample_real_transaction()

        txn["simulation_mode"] = "normal"

        return txn

    def generate_stolen_card_transaction(self):

        txn = self.sample_real_transaction()

        # unusually high amount
        txn["transaction_amount"] = round(
            random.uniform(2000, 10000),
            2
        )

        txn["category"] = random.choice([
            "shopping_pos",
            "travel",
            "electronics"
        ])

        txn["simulation_mode"] = "stolen_card"

        return txn

    def generate_geo_attack_transaction(self):

        txn = self.sample_real_transaction()

        # unrealistic merchant location
        txn["merchant_lat"] = random.uniform(
            -90,
            90
        )

        txn["merchant_long"] = random.uniform(
            -180,
            180
        )

        txn["simulation_mode"] = "geo_attack"

        return txn

    def generate_velocity_burst_transaction(self):

        txn = self.sample_real_transaction()

        # rapid repeated transaction
        txn["transaction_amount"] = round(
            random.uniform(500, 5000),
            2
        )

        txn["transaction_hour"] = random.choice([
            0, 1, 2, 3
        ])

        txn["simulation_mode"] = (
            "velocity_burst"
        )

        return txn

    def generate_transaction(
        self,
        mode: str = "normal"
    ):

        """
        Generate single transaction
        based on attack mode.
        """

        try:

            mode = mode.lower()

            if mode == "normal":

                return (
                    self.generate_normal_transaction()
                )

            elif mode == "stolen card":

                return (
                    self.generate_stolen_card_transaction()
                )

            elif mode == "geo attack":

                return (
                    self.generate_geo_attack_transaction()
                )

            elif mode == "velocity burst":

                return (
                    self.generate_velocity_burst_transaction()
                )

            else:

                raise ValueError(
                    f"Unknown mode: {mode}"
                )

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def generate_transactions(
        self,
        num_transactions: int,
        mode: str = "normal"
    ):

        """
        Generate multiple transactions.
        """

        try:

            logger.info(
                f"Generating {num_transactions} "
                f"transactions in mode: {mode}"
            )

            transactions = []

            for _ in range(num_transactions):

                txn = self.generate_transaction(
                    mode
                )

                transactions.append(txn)

            logger.info(
                "Transaction generation completed."
            )

            return transactions

        except Exception as e:
            raise FraudShieldException(str(e), sys)
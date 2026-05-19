import sys
import pandas as pd
import numpy as np

from src.utils.logging import logger
from src.utils.exception import FraudShieldException

import warnings
warnings.filterwarnings("ignore")

class DataTransformer:
    """
    Handles data cleaning + feature engineering for FraudShield AI.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def drop_columns(self):
        try:
            drop_cols = [
                "trans_num",
                "first",
                "last",
                "street",
                "Unnamed: 0"
            ]

            self.df.drop(columns=drop_cols, inplace=True, errors="ignore")
            logger.info("Irrelevant columns dropped successfully.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def handle_missing_values(self):
        try:
            before = self.df.shape[0]
            self.df.dropna(inplace=True)
            after = self.df.shape[0]

            logger.info(f"Missing values handled. Rows: {before} -> {after}")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def remove_duplicates(self):
        try:
            before = self.df.shape[0]
            self.df.drop_duplicates(inplace=True)
            after = self.df.shape[0]

            logger.info(f"Duplicates removed. Rows: {before} -> {after}")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def process_datetime(self):
        try:
            if "trans_date_trans_time" in self.df.columns:
                self.df["trans_date_trans_time"] = pd.to_datetime(
                    self.df["trans_date_trans_time"]
                )

                self.df["transaction_date"] = self.df["trans_date_trans_time"].dt.date
                self.df["transaction_time"] = self.df["trans_date_trans_time"].dt.strftime('%H:%M:%S')

                self.df.drop("trans_date_trans_time", axis=1, inplace=True)
            else:
                logger.info("trans_date_trans_time not present. Skipping datetime extraction.")

            logger.info("Datetime processing completed.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def rename_columns(self):
        try:
            self.df.rename(
                columns={
                    "cc_num": "credit_card_number",
                    "amt": "transaction_amount",
                    "lat": "buyer_lat",
                    "long": "buyer_long",
                    "city": "buyer_city",
                    "state": "buyer_state",
                    "zip": "buyer_zip",
                    "job": "buyer_job",
                    "dob": "buyer_date_of_birth",
                    "city_pop": "buyer_city_pop",
                    "merch_lat": "merchant_lat",
                    "merch_long": "merchant_long",
                    "gender": "buyer_gender",
                    "is_fraud": "transaction_is_fraud"
                },
                inplace=True
            )

            logger.info("Columns renamed successfully.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def convert_types(self):
        try:
            self.df["transaction_date"] = pd.to_datetime(self.df["transaction_date"])
            self.df["buyer_date_of_birth"] = pd.to_datetime(self.df["buyer_date_of_birth"])
            self.df["transaction_is_fraud"] = self.df["transaction_is_fraud"].astype(int)

            logger.info("Type conversion completed.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def feature_engineering(self):
        try:
            # Transaction hour
            self.df["transaction_hour"] = self.df["transaction_time"].str[:2].astype(int)

            # Buyer age
            self.df["buyer_age"] = (
                (self.df["transaction_date"] - self.df["buyer_date_of_birth"])
                .dt.days // 365
            )

            logger.info("Feature engineering completed.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def transform(self) -> pd.DataFrame:
        """
        Full transformation pipeline
        """
        try:
            logger.info("Starting transformation pipeline...")

            self.drop_columns()
            self.handle_missing_values()
            self.remove_duplicates()
            self.process_datetime()
            self.rename_columns()
            self.convert_types()
            self.feature_engineering()

            logger.info(f"Transformation completed. Final shape: {self.df.shape}")

            return self.df

        except Exception as e:
            raise FraudShieldException(str(e), sys)
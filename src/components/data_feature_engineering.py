import sys
import numpy as np
import pandas as pd

from src.utils.logging import logger
from src.utils.exception import FraudShieldException


class FeatureEngineer:
    """
    Handles feature engineering for FraudShield AI.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def convert_datetime_columns(self):
        """
        Convert date-related columns into datetime format.
        """

        try:
            logger.info("Converting datetime columns...")

            self.df["transaction_date"] = pd.to_datetime(
                self.df["transaction_date"]
            )

            self.df["buyer_date_of_birth"] = pd.to_datetime(
                self.df["buyer_date_of_birth"]
            )

            logger.info("Datetime conversion completed.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def create_distance_feature(self):
        """
        Create geographical distance feature using Haversine formula.
        """

        try:
            logger.info("Creating distance_km feature...")

            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371.0

                lat1, lon1, lat2, lon2 = map(
                    np.radians,
                    [lat1, lon1, lat2, lon2]
                )

                dlat = lat2 - lat1
                dlon = lon2 - lon1

                a = (
                    np.sin(dlat / 2) ** 2
                    + np.cos(lat1)
                    * np.cos(lat2)
                    * np.sin(dlon / 2) ** 2
                )

                c = 2 * np.arcsin(np.sqrt(a))

                return R * c

            self.df["distance_km"] = haversine_distance(
                self.df["buyer_lat"],
                self.df["buyer_long"],
                self.df["merchant_lat"],
                self.df["merchant_long"]
            )

            logger.info("distance_km feature created.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def transform_transaction_amount(self):
        """
        Apply log transformation to reduce skewness.
        """

        try:
            logger.info("Creating log-transformed transaction amount...")

            self.df["transaction_amount_log"] = np.log1p(
                self.df["transaction_amount"]
            )

            logger.info("transaction_amount_log created.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def create_night_transaction_flag(self):
        """
        Flag suspicious night transactions.
        """

        try:
            logger.info("Creating is_night_transaction feature...")

            self.df["is_night_transaction"] = self.df[
                "transaction_hour"
            ].apply(
                lambda x: 1 if x >= 22 or x <= 3 else 0
            )

            logger.info("Night transaction feature created.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def drop_unused_columns(self):
        """
        Drop irrelevant columns after feature engineering.
        """

        try:
            logger.info("Dropping unused columns...")

            drop_cols = [
                "merchant",
                "credit_card_number",
                "buyer_city",
                "buyer_state",
                "buyer_zip",
                "buyer_city_pop"
            ]

            self.df.drop(
                columns=drop_cols,
                axis=1,
                inplace=True,
                errors="ignore"
            )

            logger.info("Unused columns dropped.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def engineer_features(self) -> pd.DataFrame:
        """
        Complete feature engineering pipeline.
        """

        try:
            logger.info("Starting feature engineering pipeline...")

            self.convert_datetime_columns()

            self.create_distance_feature()

            self.transform_transaction_amount()

            self.create_night_transaction_flag()

            self.drop_unused_columns()

            logger.info(
                f"Feature engineering completed. Shape: {self.df.shape}"
            )

            return self.df

        except Exception as e:
            raise FraudShieldException(str(e), sys)


import sys
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

from src.utils.logging import logger
from src.utils.exception import FraudShieldException


class DataPreparation:
    """
    Prepares feature-engineered data
    for machine learning training.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def drop_unnecessary_columns(self):
        """
        Remove columns not needed for modeling.
        """

        try:
            logger.info("Dropping unnecessary columns...")

            cols_to_drop = [
                "unix_time",
                "buyer_lat",
                "buyer_long",
                "merchant_lat",
                "merchant_long",
                "transaction_amount",
                "buyer_job",
                "transaction_date",
                "buyer_date_of_birth",
                "transaction_time"
            ]

            self.df.drop(
                columns=cols_to_drop,
                inplace=True,
                errors="ignore"
            )

            logger.info("Columns dropped successfully.")

            return self.df

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def split_features_target(self):
        """
        Split dataframe into features and target.
        """

        try:
            logger.info("Splitting features and target...")

            X = self.df.drop(
                columns=["transaction_is_fraud"]
            )

            y = self.df["transaction_is_fraud"]

            logger.info("Feature-target split completed.")

            return X, y

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def train_test_split_data(self, X, y):
        """
        Create train-test split.
        """

        try:
            logger.info("Performing train-test split...")

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=0.2,
                random_state=42,
                stratify=y
            )

            logger.info("Train-test split completed.")

            return X_train, X_test, y_train, y_test

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def encode_and_scale_features(self, X_train, X_test):
        """
        Apply OneHotEncoding + Feature Scaling.
        """

        try:
            logger.info("Applying OneHotEncoding and Scaling...")

            categorical_cols = [
                "buyer_gender",
                "category"
            ]

            numeric_cols = [
                col for col in X_train.columns
                if col not in categorical_cols
            ]

            # Preprocessing pipeline
            preprocessor = ColumnTransformer(
                transformers=[
                    (
                        "cat",
                        OneHotEncoder(handle_unknown="ignore"),
                        categorical_cols
                    ),
                    (
                        "num",
                        StandardScaler(),
                        numeric_cols
                    )
                ]
            )

            X_train_processed = preprocessor.fit_transform(X_train)
            X_test_processed = preprocessor.transform(X_test)

            logger.info("Encoding and scaling completed.")

            return (
                X_train_processed,
                X_test_processed,
                preprocessor
            )

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def prepare_data(self):
        """
        Complete data preparation pipeline.
        """

        try:
            logger.info("Starting data preparation pipeline...")

            self.drop_unnecessary_columns()

            X, y = self.split_features_target()

            X_train, X_test, y_train, y_test = (
                self.train_test_split_data(X, y)
            )

            (
                X_train_processed,
                X_test_processed,
                preprocessor
            ) = self.encode_and_scale_features(
                X_train,
                X_test
            )

            logger.info("Data preparation completed successfully.")

            return (
                X_train_processed,
                X_test_processed,
                y_train,
                y_test,
                preprocessor
            )

        except Exception as e:
            raise FraudShieldException(str(e), sys)
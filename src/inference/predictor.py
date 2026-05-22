import io
import sys
import joblib
import numpy as np
import pandas as pd

from src.cloud.s3_manager import S3Manager
from src.utils.logging import logger
from src.utils.exception import FraudShieldException


FRAUD_THRESHOLD = 0.50

# Columns added by simulator — model never saw these
_SIMULATOR_COLS = ["simulation_mode"]

# Target column — present in training data but never at inference
_TARGET_COL = "transaction_is_fraud"


class FraudPredictor:
    """
    Loads model + preprocessor from S3 (in-memory, no local disk).
    Applies the exact same preprocessing pipeline as training:

        FeatureEngineer steps
            → DataPreparation.drop_unnecessary_columns()
            → preprocessor.transform()   ← sklearn ColumnTransformer
                                            (OHE + StandardScaler fitted on training data)
            → model.predict_proba()

    No manual OHE. No manual scaling. The saved preprocessor handles
    both exactly as it did during training.
    """

    # S3 keys — match what ModelTrainer uploads
    _DEFAULT_MODEL_KEY       = "models/best_model.pkl"
    _DEFAULT_PREPROCESSOR_KEY = "models/preprocessor.pkl"

    def __init__(
        self,
        s3_model_key: str = _DEFAULT_MODEL_KEY,
        s3_preprocessor_key: str = _DEFAULT_PREPROCESSOR_KEY,
    ):
        try:
            s3 = S3Manager()

            # ── load model ────────────────────────────────────────────
            logger.info(f"Loading model from S3: {s3_model_key}")
            self.model = joblib.load(
                io.BytesIO(s3.load_object(s3_model_key))
            )
            logger.info("Model loaded from S3 successfully.")

            # ── load preprocessor ─────────────────────────────────────
            # This is the sklearn ColumnTransformer fitted on training data.
            # It holds the exact OHE categories and StandardScaler mean/std
            # from the training distribution — critical for correct inference.
            logger.info(f"Loading preprocessor from S3: {s3_preprocessor_key}")
            self.preprocessor = joblib.load(
                io.BytesIO(s3.load_object(s3_preprocessor_key))
            )
            logger.info("Preprocessor loaded from S3 successfully.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def predict(self, transaction: dict) -> dict:
        """
        Full inference on one raw transaction dict from TransactionGenerator.

        Returns
        -------
        {
            transaction_id    : str,
            fraud_probability : float,
            decision          : "APPROVED" | "BLOCKED",
            threshold         : float,
            raw_transaction   : dict
        }
        """
        try:
            df = pd.DataFrame([transaction])
            X  = self._preprocess(df)

            proba    = float(self.model.predict_proba(X)[0][1])
            decision = "BLOCKED" if proba >= FRAUD_THRESHOLD else "APPROVED"

            logger.info(
                f"Prediction → {decision} "
                f"(fraud_probability={proba:.4f})"
            )

            return {
                "transaction_id":    str(
                    transaction.get("id") or transaction.get("_id") or ""
                ),
                "fraud_probability": round(proba, 4),
                "decision":          decision,
                "threshold":         FRAUD_THRESHOLD,
                "raw_transaction":   transaction,
            }

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    def predict_batch(self, transactions: list[dict]) -> list[dict]:
        """Run predict() over a list; preserves order."""
        try:
            logger.info(
                f"Batch prediction on {len(transactions)} transactions."
            )
            return [self.predict(txn) for txn in transactions]
        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    # Preprocessing  — mirrors ml_pipeline.py exactly
    # ──────────────────────────────────────────────────────────────────────

    def _preprocess(self, df: pd.DataFrame) -> np.ndarray:
        """
        Step-by-step mirror of the training pipeline:

        1. Strip simulator cols + target
        2. FeatureEngineer: datetime parse, haversine, log-amount, night flag,
                            drop post-engineering irrelevant cols
        3. DataPreparation: drop_unnecessary_columns()
        4. preprocessor.transform()  ← OHE + StandardScaler from training
        """
        df = df.copy()

        # ── 1. strip simulator / target columns ───────────────────────
        df.drop(
            columns=_SIMULATOR_COLS + [_TARGET_COL],
            errors="ignore",
            inplace=True,
        )

        # ── 2. FeatureEngineer steps (same order as engineer_features) ─

        # 2a. datetime parsing
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"], errors="coerce"
        )
        df["buyer_date_of_birth"] = pd.to_datetime(
            df["buyer_date_of_birth"], errors="coerce"
        )

        # 2b. haversine distance buyer ↔ merchant
        df["distance_km"] = _haversine(
            df["buyer_lat"].values,
            df["buyer_long"].values,
            df["merchant_lat"].values,
            df["merchant_long"].values,
        )

        # 2c. log-transform raw transaction amount
        df["transaction_amount_log"] = np.log1p(
            df["transaction_amount"].fillna(0).astype(float)
        )

        # 2d. night-transaction flag (22:00–03:00 inclusive)
        df["is_night_transaction"] = (
            df["transaction_hour"]
            .apply(lambda h: 1 if h >= 22 or h <= 3 else 0)
        )

        # 2e. drop columns FeatureEngineer.drop_unused_columns() removes
        df.drop(
            columns=[
                "merchant",
                "credit_card_number",
                "buyer_city",
                "buyer_state",
                "buyer_zip",
                "buyer_city_pop",
            ],
            errors="ignore",
            inplace=True,
        )

        # ── 3. DataPreparation.drop_unnecessary_columns() ─────────────
        df.drop(
            columns=[
                "unix_time",
                "buyer_lat",
                "buyer_long",
                "merchant_lat",
                "merchant_long",
                "transaction_amount",    # raw; log version is kept
                "buyer_job",
                "transaction_date",
                "buyer_date_of_birth",
                "transaction_time",
            ],
            errors="ignore",
            inplace=True,
        )

        # safety net — drop target if it survived
        df.drop(columns=[_TARGET_COL], errors="ignore", inplace=True)

        # ── 4. Apply training preprocessor (OHE + StandardScaler) ─────
        # preprocessor expects buyer_gender + category as object columns
        # and all numeric columns in the order it was fitted on.
        # Passing the same DataFrame structure guarantees this.
        X = self.preprocessor.transform(df)

        return X


# ──────────────────────────────────────────────────────────────────────────
# Module-level helper (pure function, no state)
# ──────────────────────────────────────────────────────────────────────────

def _haversine(
    lat1: np.ndarray,
    lon1: np.ndarray,
    lat2: np.ndarray,
    lon2: np.ndarray,
) -> np.ndarray:
    """Vectorised haversine distance in km."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )
    return R * 2 * np.arcsin(np.sqrt(a))
import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from utils.logging import logger
from utils.exception import FraudShieldException
from utils.mlflow_setup import (
    init_mlflow,
    EXPERIMENT_NAME,
    MODEL_NAME,
    PREPROCESSOR_ARTIFACT_PATH,
)


FRAUD_THRESHOLD = 0.50

_SIMULATOR_COLS = ["simulation_mode"]
_TARGET_COL     = "transaction_is_fraud"


class FraudPredictor:
    """
    Loads model + preprocessor straight from the MLflow Model Registry
    (hosted on DagsHub) — no S3, no local disk copy.

    The preprocessor always lives as an artifact inside the SAME run as the
    model it was fitted alongside (see ModelTrainer + ModelRegistryAndDeploy),
    so we resolve it via the Production model version's run_id rather than a
    separate registered name. This guarantees the two never drift apart.

    Critical fix retained from the S3 version: enforces the exact column
    order the preprocessor was fitted on using preprocessor.feature_names_in_.
    Without this, StandardScaler applies wrong mean/std to wrong columns
    → model receives garbage → everything scores near zero.
    """

    def __init__(self, stage: str = "Production"):
        try:
            init_mlflow()

            self.stage      = stage
            self.model_name = MODEL_NAME
            self.model_uri  = f"models:/{self.model_name}/{self.stage}"

            logger.info(f"Loading model from MLflow registry: {self.model_uri}")
            self.model = mlflow.sklearn.load_model(self.model_uri)
            logger.info("Model loaded from MLflow successfully.")

            # Resolve the run_id behind this Production version, so we can
            # pull the preprocessor that was logged alongside it.
            client   = MlflowClient()
            versions = [
                version
                for version in client.search_model_versions(
                    f"name = '{self.model_name}'"
                )
                if version.current_stage == self.stage
            ]
            versions.sort(key=lambda version: int(version.version), reverse=True)
            if not versions:
                raise FraudShieldException(
                    f"No model version found in stage '{self.stage}' for "
                    f"'{self.model_name}'. Run the ML pipeline at least once.",
                    sys,
                )
            run_id = versions[0].run_id

            preprocessor_uri = f"runs:/{run_id}/{PREPROCESSOR_ARTIFACT_PATH}"

            # MLflow 3 stores models logged with log_model as LoggedModel
            # resources. Resolve the preprocessor's models:/ URI first;
            # retain the runs:/ URI for older MLflow artifact layouts.
            experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
            if experiment is not None and hasattr(client, "search_logged_models"):
                logged_models = client.search_logged_models(
                    experiment_ids=[experiment.experiment_id],
                    max_results=100,
                )
                matching_models = [
                    model
                    for model in logged_models
                    if model.name == PREPROCESSOR_ARTIFACT_PATH
                    and model.source_run_id == run_id
                    and getattr(getattr(model, "status", None), "value", None) == "READY"
                ]
                if matching_models:
                    preprocessor_uri = matching_models[-1].model_uri

            logger.info(f"Loading preprocessor from MLflow run: {preprocessor_uri}")
            self.preprocessor = mlflow.sklearn.load_model(preprocessor_uri)
            logger.info("Preprocessor loaded from MLflow successfully.")

            # ── resolve the exact column order the preprocessor expects ──
            # feature_names_in_ is set by sklearn ≥ 1.0 when fit() receives a DataFrame.
            # This is the ground truth for column order — use it every time.
            if hasattr(self.preprocessor, "feature_names_in_"):
                self._expected_columns = list(self.preprocessor.feature_names_in_)
                logger.info(
                    f"Preprocessor expects {len(self._expected_columns)} columns: "
                    f"{self._expected_columns}"
                )
            else:
                # sklearn < 1.0 fallback: reconstruct from transformers
                self._expected_columns = self._infer_column_order()
                logger.warning(
                    f"feature_names_in_ not available — inferred column order: "
                    f"{self._expected_columns}"
                )

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def predict(self, transaction: dict) -> dict:
        try:
            df = pd.DataFrame([transaction])
            X  = self._preprocess(df)

            proba    = float(self.model.predict_proba(X)[0][1])
            decision = "BLOCKED" if proba >= FRAUD_THRESHOLD else "APPROVED"

            logger.info(
                f"Prediction → {decision} (fraud_probability={proba:.4f})"
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
        try:
            logger.info(f"Batch prediction on {len(transactions)} transactions.")
            return [self.predict(txn) for txn in transactions]
        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    # Preprocessing — mirrors ml_pipeline.py exactly, then enforces col order
    # ──────────────────────────────────────────────────────────────────────

    def _preprocess(self, df: pd.DataFrame) -> np.ndarray:
        df = df.copy()

        # ── 1. strip simulator / target columns ───────────────────────
        df.drop(
            columns=_SIMULATOR_COLS + [_TARGET_COL],
            errors="ignore",
            inplace=True,
        )

        # ── 2. FeatureEngineer steps ───────────────────────────────────

        # 2a. datetime parsing
        # These dates are removed before the model transform. Simulator
        # payloads may omit them, so missing values should not reject a
        # transaction that still contains the trained model features.
        df["transaction_date"] = pd.to_datetime(
            df.get("transaction_date", pd.Series(pd.NaT, index=df.index)),
            errors="coerce",
        )
        df["buyer_date_of_birth"] = pd.to_datetime(
            df.get("buyer_date_of_birth", pd.Series(pd.NaT, index=df.index)),
            errors="coerce",
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
                "transaction_amount",
                "buyer_job",
                "transaction_date",
                "buyer_date_of_birth",
                "transaction_time",
            ],
            errors="ignore",
            inplace=True,
        )

        df.drop(columns=[_TARGET_COL], errors="ignore", inplace=True)

        # ── 4. CRITICAL: reorder columns to match training order ───────
        # The ColumnTransformer was fitted on columns in a specific order.
        # Raw input may come in a different order than training data.
        # If we pass columns in the wrong order, StandardScaler applies
        # the wrong mean/std to the wrong feature → garbage predictions.
        df = self._align_columns(df)

        # ── 5. Apply training preprocessor (OHE + StandardScaler) ─────
        X = self.preprocessor.transform(df)
        return X

    def _align_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reorder df to exactly match self._expected_columns.
        Logs any missing or extra columns so you can debug mismatches.
        """
        missing = [c for c in self._expected_columns if c not in df.columns]
        extra   = [c for c in df.columns if c not in self._expected_columns]

        if missing:
            logger.warning(f"Columns missing at inference (will be filled with 0): {missing}")
            for col in missing:
                df[col] = 0

        if extra:
            logger.warning(f"Extra columns dropped at inference: {extra}")
            df.drop(columns=extra, inplace=True)

        # reorder to match training
        return df[self._expected_columns]

    def _infer_column_order(self) -> list[str]:
        """
        Fallback for sklearn < 1.0: reconstruct column order from transformers.
        ColumnTransformer processes categorical cols first, then numeric.
        """
        cols = []
        for _, _, transformer_cols in self.preprocessor.transformers_:
            if isinstance(transformer_cols, list):
                cols.extend(transformer_cols)
        return cols


# ──────────────────────────────────────────────────────────────────────────

def _haversine(
    lat1: np.ndarray,
    lon1: np.ndarray,
    lat2: np.ndarray,
    lon2: np.ndarray,
) -> np.ndarray:
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )
    return R * 2 * np.arcsin(np.sqrt(a))
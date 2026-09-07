import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mlflow
from mlflow.tracking import MlflowClient

from utils.logging import logger
from utils.exception import FraudShieldException
from utils.mlflow_setup import (
    init_mlflow,
    EXPERIMENT_NAME,
    MODEL_NAME,
    MODEL_ARTIFACT_PATH,
)


class ModelRegistryAndDeploy:
    """
    Registers the best-performing run's model into the MLflow Model Registry
    (hosted on DagsHub), then promotes it through Staging → Production if it
    beats the current Production model.

    The preprocessor (ColumnTransformer) is NOT registered separately — it
    was logged as an artifact ("preprocessor") inside the *same* MLflow run
    as the winning model (see ModelTrainer), so it always travels in lockstep
    with whichever model version is Production. At prediction time, the
    preprocessor is loaded via `runs:/{run_id}/preprocessor`, where run_id
    comes straight off the Production ModelVersion.

    Selection metric: recall (fraud detection cares more about catching
    fraud than being conservative — this matches ModelTrainer's own
    best-model selection during training).
    """

    def __init__(self, metric: str = "recall"):
        init_mlflow()
        self.client      = MlflowClient()
        self.model_name  = MODEL_NAME
        self.metric      = metric

    # ──────────────────────────────────────────────────────────────────────
    def get_best_run(self):
        """Find the run with the highest `self.metric` across the experiment."""
        try:
            experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
            if experiment is None:
                raise ValueError(f"Experiment '{EXPERIMENT_NAME}' not found.")

            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{self.metric} DESC"],
                max_results=1,
            )

            if runs.empty:
                raise ValueError("No finished runs found to register.")

            best_run_id = runs.iloc[0]["run_id"]
            best_metric = runs.iloc[0][f"metrics.{self.metric}"]

            logger.info(
                f"Best run so far: {best_run_id} "
                f"({self.metric}={best_metric:.4f})"
            )
            return best_run_id, best_metric

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    def register_model(self, run_id: str):
        try:
            experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
            model_uri = f"runs:/{run_id}/{MODEL_ARTIFACT_PATH}"

            # MLflow 3 stores models logged with log_model as LoggedModel
            # resources. Resolve that URI first; older MLflow versions use
            # the legacy runs:/ URI below.
            if experiment is not None and hasattr(self.client, "search_logged_models"):
                logged_models = self.client.search_logged_models(
                    experiment_ids=[experiment.experiment_id],
                    max_results=100,
                )
                matching_models = [
                    model
                    for model in logged_models
                    if model.name == MODEL_ARTIFACT_PATH
                    if model.source_run_id == run_id
                    and getattr(model, "status", None).value == "READY"
                ]
                if matching_models:
                    model_uri = matching_models[-1].model_uri

            logger.info(f"Registering model from {model_uri} as '{self.model_name}'...")

            result = mlflow.register_model(model_uri, self.model_name)
            logger.info(f"Registered '{self.model_name}' version {result.version}.")
            return result

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    def move_to_staging(self, version: str):
        try:
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=version,
                stage="Staging",
                archive_existing_versions=False,
            )
            logger.info(f"Version {version} moved to Staging.")
        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    def _metric_for_version(self, version) -> float:
        """Fetch the tracked metric value for a given ModelVersion's run."""
        run = self.client.get_run(version.run_id)
        return run.data.metrics.get(self.metric, 0.0)

    def compare_staging_vs_production(self) -> bool:
        """Return True if the current Staging version beats current Production."""
        try:
            staging = self.client.get_latest_versions(self.model_name, stages=["Staging"])
            production = self.client.get_latest_versions(self.model_name, stages=["Production"])

            if not staging:
                logger.warning("No model in Staging — nothing to compare.")
                return False

            staging_metric = self._metric_for_version(staging[0])

            if not production:
                logger.info(
                    f"No current Production model — promoting Staging "
                    f"(version {staging[0].version}, {self.metric}={staging_metric:.4f}) by default."
                )
                return True

            production_metric = self._metric_for_version(production[0])

            logger.info(
                f"Staging {self.metric}={staging_metric:.4f} vs "
                f"Production {self.metric}={production_metric:.4f}"
            )
            return staging_metric > production_metric

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    def promote_to_production(self):
        try:
            staging = self.client.get_latest_versions(self.model_name, stages=["Staging"])
            if not staging:
                logger.warning("No Staging model to promote.")
                return

            version = staging[0].version
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=version,
                stage="Production",
                archive_existing_versions=True,
            )
            logger.info(f"Version {version} promoted to PRODUCTION.")

        except Exception as e:
            raise FraudShieldException(str(e), sys)

    # ──────────────────────────────────────────────────────────────────────
    def run_deployment_pipeline(self):
        """
        Full flow: find best run this training cycle → register →
        Staging → compare vs Production → promote if better.
        """
        try:
            best_run_id, best_metric = self.get_best_run()
            registered = self.register_model(best_run_id)
            self.move_to_staging(registered.version)

            if self.compare_staging_vs_production():
                self.promote_to_production()
                logger.info(
                    f"New model (version {registered.version}, "
                    f"{self.metric}={best_metric:.4f}) is now PRODUCTION. "
                    f"It will be loaded directly from the MLflow registry at prediction time."
                )
            else:
                logger.info(
                    "Current Production model still performs better — retained. "
                    "New candidate remains in Staging only."
                )

            return registered

        except Exception as e:
            logger.error("Model registry/deployment step failed.")
            raise FraudShieldException(str(e), sys)

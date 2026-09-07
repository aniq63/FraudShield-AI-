import os
from dotenv import load_dotenv

import mlflow
import dagshub

from utils.logging import logger

load_dotenv()

DAGSHUB_REPO_OWNER = os.getenv("DAGSHUB_REPO_OWNER", "aniqramzan5758")
DAGSHUB_REPO_NAME  = os.getenv("DAGSHUB_REPO_NAME", "FraudShield-AI-")

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    f"https://dagshub.com/{DAGSHUB_REPO_OWNER}/{DAGSHUB_REPO_NAME}.mlflow",
)
MLFLOW_TRACKING_USERNAME = os.getenv("MLFLOW_TRACKING_USERNAME")
MLFLOW_TRACKING_PASSWORD = os.getenv("MLFLOW_TRACKING_PASSWORD") or os.getenv("DAGSHUB_TOKEN")

EXPERIMENT_NAME    = "FraudShield_AI"
MODEL_NAME         = "FraudShieldModel"
PREPROCESSOR_ARTIFACT_PATH = "preprocessor"
MODEL_ARTIFACT_PATH        = "model"

_initialized = False


def init_mlflow():
    """
    Configure MLflow to track against the DagsHub-hosted server for this repo.
    Safe to call multiple times — only runs dagshub.init() once per process.

        import dagshub
        dagshub.init(repo_owner='aniqramzan5758', repo_name='FraudShield-AI-', mlflow=True)
        import mlflow
        with mlflow.start_run():
            mlflow.log_param('parameter name', 'value')
            mlflow.log_metric('metric name', 1)
    """
    global _initialized

    if MLFLOW_TRACKING_USERNAME and MLFLOW_TRACKING_PASSWORD:
        os.environ["MLFLOW_TRACKING_USERNAME"] = MLFLOW_TRACKING_USERNAME
        os.environ["MLFLOW_TRACKING_PASSWORD"] = MLFLOW_TRACKING_PASSWORD
        os.environ["DAGSHUB_TOKEN"]            = MLFLOW_TRACKING_PASSWORD

    if not _initialized:
        try:
            dagshub.init(
                repo_owner=DAGSHUB_REPO_OWNER,
                repo_name=DAGSHUB_REPO_NAME,
                mlflow=True,
            )
            _initialized = True
        except Exception as e:
            logger.warning(
                f"dagshub.init() failed ({e}) — falling back to plain "
                f"mlflow.set_tracking_uri(). Metrics/artifacts still work as "
                f"long as MLFLOW_TRACKING_USERNAME/PASSWORD are set."
            )

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    logger.info(f"MLflow tracking URI set to: {MLFLOW_TRACKING_URI}")

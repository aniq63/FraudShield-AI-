import os
import sys
from pathlib import Path
import joblib
import mlflow
import mlflow.sklearn

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score
)

from utils.logging import logger
from utils.exception import FraudShieldException
from utils.mlflow_setup import (
    init_mlflow,
    MODEL_ARTIFACT_PATH,
    PREPROCESSOR_ARTIFACT_PATH,
)

import warnings
warnings.filterwarnings("ignore")


class ModelTrainer:

    def __init__(self, X_train, X_test, y_train, y_test, preprocessor=None):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.preprocessor = preprocessor

    def get_models(self):

        # class imbalance handling
        negative_count = len(self.y_train[self.y_train == 0])
        positive_count = len(self.y_train[self.y_train == 1])

        if positive_count == 0:
            logger.warning(
                "No positive samples found in y_train. "
                "Using scale_pos_weight=1 for XGBoost."
            )
            scale_pos_weight_value = 1
        else:
            scale_pos_weight_value = negative_count / positive_count

        models = {
            "Logistic Regression": LogisticRegression(
                class_weight="balanced",
                max_iter=1000
            ),

            "Decision Tree": DecisionTreeClassifier(
                class_weight="balanced",
                max_depth=10
            ),

            "Random Forest": RandomForestClassifier(
                class_weight="balanced",
                n_estimators=100,
                n_jobs=-1
            ),

            "XGBoost": XGBClassifier(
                scale_pos_weight=scale_pos_weight_value,
                eval_metric="logloss"
            )
        }

        return models

    def evaluate_model(self, model):

        y_pred = model.predict(self.X_test)

        return {
            "f1_score": f1_score(self.y_test, y_pred),
            "precision": precision_score(self.y_test, y_pred),
            "recall": recall_score(self.y_test, y_pred)
        }

    def train_models(self):

        try:
            logger.info("Starting training pipeline...")

            init_mlflow()

            models = self.get_models()

            best_model = None
            best_model_name = None
            best_run_id = None
            best_recall = 0

            os.makedirs("artifacts", exist_ok=True)

            results = []

            for name, model in models.items():

                logger.info(f"Training {name}")

                with mlflow.start_run(run_name=name) as run:

                    model.fit(self.X_train, self.y_train)

                    metrics = self.evaluate_model(model)

                    # log metrics
                    mlflow.log_metrics(metrics)

                    # NOTE: artifact path is always "model" (not the model's
                    # display name) so downstream registry/prediction code
                    # can always find it at runs:/{run_id}/model regardless
                    # of which algorithm ended up winning.
                    # serialization_format="cloudpickle": MLflow 3.x defaults
                    # to "skops", which refuses to (de)serialize XGBoost's
                    # Booster/XGBClassifier as "untrusted types". cloudpickle
                    # has no such restriction and is what earlier MLflow
                    # versions used by default anyway.
                    mlflow.sklearn.log_model(
                        model,
                        MODEL_ARTIFACT_PATH,
                        serialization_format="cloudpickle",
                    )

                    results.append({
                        "Model": name,
                        **metrics
                    })

                    logger.info(
                        f"{name} -> Recall: {metrics['recall']:.4f}"
                    )

                    # select best by recall
                    if metrics["recall"] > best_recall:
                        best_recall = metrics["recall"]
                        best_model = model
                        best_model_name = name
                        best_run_id = run.info.run_id

            # save best model locally under a consistent path (handy for
            # quick local debugging; the source of truth is now MLflow)
            model_path = "artifacts/best_model.pkl"
            joblib.dump(best_model, model_path)

            logger.info(f"Best model saved: {model_path} (selected: {best_model_name})")

            # save preprocessor artifact locally, and log it into the SAME
            # MLflow run as the winning model — this keeps model and
            # preprocessor permanently in lockstep. At prediction time the
            # preprocessor is loaded via runs:/{run_id}/preprocessor, where
            # run_id comes off whichever model version is in Production.
            preprocessor_path = None
            if self.preprocessor is not None:
                preprocessor_path = "artifacts/preprocessor.pkl"
                joblib.dump(self.preprocessor, preprocessor_path)
                logger.info(f"Preprocessor saved: {preprocessor_path}")

                if best_run_id is not None:
                    with mlflow.start_run(run_id=best_run_id):
                        mlflow.sklearn.log_model(
                            self.preprocessor,
                            PREPROCESSOR_ARTIFACT_PATH,
                            serialization_format="cloudpickle",
                        )
                    logger.info(
                        f"Preprocessor logged into winning run {best_run_id} "
                        f"(artifact path: '{PREPROCESSOR_ARTIFACT_PATH}')."
                    )

            logger.info(f"Winning run for this training cycle: {best_run_id}")

            return best_model, results

        except Exception as e:
            logger.error("Training failed")
            raise FraudShieldException(str(e), sys)
import os
import sys
import joblib
import mlflow
import mlflow.sklearn

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score
)

from src.utils.logging import logger
from src.utils.exception import FraudShieldException
from src.cloud.s3_manager import S3Manager

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

            models = self.get_models()

            best_model = None
            best_model_name = None
            best_recall = 0

            os.makedirs("artifacts", exist_ok=True)

            mlflow.set_experiment("FraudShield_AI")

            results = []

            for name, model in models.items():

                logger.info(f"Training {name}")

                with mlflow.start_run(run_name=name):

                    model.fit(self.X_train, self.y_train)

                    metrics = self.evaluate_model(model)

                    # log metrics
                    mlflow.log_metrics(metrics)

                    mlflow.sklearn.log_model(model, name)

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

            # save best model locally under a consistent path
            model_path = "artifacts/best_model.pkl"
            joblib.dump(best_model, model_path)

            logger.info(f"Best model saved: {model_path} (selected: {best_model_name})")

            # save preprocessor artifact, if available
            preprocessor_path = None
            if self.preprocessor is not None:
                preprocessor_path = "artifacts/preprocessor.pkl"
                joblib.dump(self.preprocessor, preprocessor_path)
                logger.info(f"Preprocessor saved: {preprocessor_path}")

            # upload to S3 using the generic best_model path
            try:
                s3 = S3Manager()
                s3_path = s3.upload_file(
                    model_path,
                    "models/best_model.pkl"
                )
                logger.info(f"Model uploaded to S3: {s3_path}")

                if preprocessor_path is not None:
                    preprocessor_s3_path = s3.upload_file(
                        preprocessor_path,
                        "models/preprocessor.pkl"
                    )
                    logger.info(
                        f"Preprocessor uploaded to S3: {preprocessor_s3_path}"
                    )
            except Exception as s3_err:
                logger.warning(
                    f"S3 upload failed ({s3_err}). "
                    "Proceeding with the locally saved artifacts."
                )

            return best_model, results

        except Exception as e:
            logger.error("Training failed")
            raise FraudShieldException(str(e), sys)
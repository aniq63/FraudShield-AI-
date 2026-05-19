import os
import sys
import joblib
import mlflow
import mlflow.sklearn

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.model_selection import GridSearchCV

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from src.utils.logging import logger
from src.utils.exception import FraudShieldException
from src.cloud.s3_manager import S3Manager


class ModelTrainer:

    def __init__(
        self,
        X_train,
        X_test,
        y_train,
        y_test
    ):

        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

        self.models = {

            "LogisticRegression": {
                "model": LogisticRegression(),
                "params": {
                    "C": [0.1, 1, 10]
                }
            },

            "DecisionTree": {
                "model": DecisionTreeClassifier(),
                "params": {
                    "max_depth": [5, 10]
                }
            },

            "RandomForest": {
                "model": RandomForestClassifier(),
                "params": {
                    "n_estimators": [50, 100],
                    "max_depth": [10, 20]
                }
            },

            "XGBoost": {
                "model": XGBClassifier(
                    eval_metric="logloss"
                ),

                "params": {
                    "n_estimators": [50, 100],
                    "max_depth": [3, 5],
                    "learning_rate": [0.01, 0.1]
                }
            }
        }

    def evaluate_model(self, model):

        predictions = model.predict(
            self.X_test
        )

        return {

            "accuracy": accuracy_score(
                self.y_test,
                predictions
            ),

            "precision": precision_score(
                self.y_test,
                predictions
            ),

            "recall": recall_score(
                self.y_test,
                predictions
            ),

            "f1_score": f1_score(
                self.y_test,
                predictions
            )
        }

    def train_models(self):

        try:

            logger.info(
                "Starting model training..."
            )

            best_model = None
            best_model_name = None
            best_recall = 0

            os.makedirs(
                "artifacts",
                exist_ok=True
            )

            mlflow.set_experiment(
                "FraudShield_AI"
            )

            for model_name, model_info in self.models.items():

                logger.info(
                    f"Training {model_name}"
                )

                with mlflow.start_run(
                    run_name=model_name
                ):

                    grid_search = GridSearchCV(
                        estimator=model_info["model"],
                        param_grid=model_info["params"],
                        cv=3,
                        scoring="recall",
                        n_jobs=-1
                    )

                    grid_search.fit(
                        self.X_train,
                        self.y_train
                    )

                    best_estimator = (
                        grid_search.best_estimator_
                    )

                    metrics = self.evaluate_model(
                        best_estimator
                    )

                    # MLflow Logging
                    mlflow.log_params(
                        grid_search.best_params_
                    )

                    mlflow.log_metrics(
                        metrics
                    )

                    mlflow.sklearn.log_model(
                        best_estimator,
                        model_name
                    )

                    logger.info(
                        f"{model_name} Recall: "
                        f"{metrics['recall']:.4f}"
                    )

                    # Best Model Selection
                    if metrics["recall"] > best_recall:

                        best_recall = (
                            metrics["recall"]
                        )

                        best_model = (
                            best_estimator
                        )

                        best_model_name = (
                            model_name
                        )

            # Save best model locally
            model_path = (
                f"artifacts/"
                f"{best_model_name}.pkl"
            )

            joblib.dump(
                best_model,
                model_path
            )

            logger.info(
                f"Model saved locally: "
                f"{model_path}"
            )

            # Upload to S3
            s3_manager = S3Manager()

            s3_path = s3_manager.upload_file(
                model_path,
                f"models/{best_model_name}.pkl"
            )

            logger.info(
                f"Model uploaded to S3: "
                f"{s3_path}"
            )

            return best_model

        except Exception as e:

            raise FraudShieldException(
                str(e),
                sys
            )
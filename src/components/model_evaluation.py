import sys

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_auc_score,
    precision_recall_curve,
    auc
)

from src.utils.logging import logger
from src.utils.exception import FraudShieldException


class ModelEvaluation:

    def __init__(
        self,
        model,
        X_test,
        y_test
    ):

        self.model = model
        self.X_test = X_test
        self.y_test = y_test

    def evaluate(self):

        try:

            logger.info(
                "Starting model evaluation..."
            )

            predictions = self.model.predict(
                self.X_test
            )

            probabilities = (
                self.model.predict_proba(
                    self.X_test
                )[:, 1]
            )

            report = classification_report(
                self.y_test,
                predictions
            )

            matrix = confusion_matrix(
                self.y_test,
                predictions
            )

            roc_auc = roc_auc_score(
                self.y_test,
                probabilities
            )

            precision, recall, _ = (
                precision_recall_curve(
                    self.y_test,
                    probabilities
                )
            )

            pr_auc = auc(
                recall,
                precision
            )

            logger.info(
                "Model evaluation completed."
            )

            return {

                "classification_report": report,

                "confusion_matrix": matrix,

                "roc_auc_score": roc_auc,

                "pr_auc_score": pr_auc
            }

        except Exception as e:

            raise FraudShieldException(
                str(e),
                sys
            )
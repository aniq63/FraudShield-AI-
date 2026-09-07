import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import logger
from utils.exception import FraudShieldException

from src.components.data_ingestion import (
    DataIngestion,
    TRAIN_DATA_FILE,
    TEST_DATA_FILE
)
from src.components.data_transformation import DataTransformer
from src.components.data_feature_engineering import FeatureEngineer
from src.components.data_preparation import DataPreparation
from src.components.model_trainer import ModelTrainer
from src.components.model_evaluation import ModelEvaluation
from src.components.model_registry_and_deploy import ModelRegistryAndDeploy


class MLPipeline:
    """
    End-to-end ML pipeline for FraudShield AI.

    Training data is loaded from datasource/train_sampled.csv and the model
    is evaluated on datasource/test_sampled.csv.
    """

    def __init__(
        self,
        train_file: str = None,
        test_file: str = None,
        limit: int = None
    ):
        self.train_file = train_file or TRAIN_DATA_FILE
        self.test_file = test_file or TEST_DATA_FILE
        self.limit = limit

    def run_pipeline(self):

        try:
            logger.info("========== ML PIPELINE STARTED ==========")

            # ---------------------------
            # 1. DATA EXTRACTION
            # ---------------------------
            logger.info("STEP 1: Data Extraction from datasource")

            train_df = DataIngestion(
                file_path=self.train_file,
                limit=self.limit
            ).fetch_data()

            test_df = DataIngestion(
                file_path=self.test_file
            ).fetch_data()

            logger.info(f"Train data extracted: {train_df.shape}")
            logger.info(f"Test data extracted: {test_df.shape}")

            # ---------------------------
            # 2. TRANSFORMATION (ETL CLEANING)
            # ---------------------------
            logger.info("STEP 2: Data Transformation")

            train_df = DataTransformer(train_df).transform()
            test_df = DataTransformer(test_df).transform()

            logger.info(
                f"After transformation: "
                f"train={train_df.shape}, test={test_df.shape}"
            )

            # ---------------------------
            # 3. FEATURE ENGINEERING
            # ---------------------------
            logger.info("STEP 3: Feature Engineering")

            train_df = FeatureEngineer(train_df).engineer_features()
            test_df = FeatureEngineer(test_df).engineer_features()

            logger.info(
                f"After feature engineering: "
                f"train={train_df.shape}, test={test_df.shape}"
            )

            # ---------------------------
            # 4. DATA PREPARATION
            # ---------------------------
            logger.info("STEP 4: Data Preparation")

            prep = DataPreparation(train_df, test_df=test_df)

            (
                X_train,
                X_test,
                y_train,
                y_test,
                preprocessor
            ) = prep.prepare_data()

            logger.info("Data preparation completed")

            # ---------------------------
            # 5. MODEL TRAINING
            # ---------------------------
            logger.info("STEP 5: Model Training")

            trainer = ModelTrainer(
                X_train,
                X_test,
                y_train,
                y_test,
                preprocessor=preprocessor
            )

            best_model, results = trainer.train_models()

            # ---------------------------
            # 6. MODEL EVALUATION
            # ---------------------------
            logger.info("STEP 6: Model Evaluation")

            evaluator = ModelEvaluation(
                best_model,
                X_test,
                y_test
            )

            evaluation = evaluator.evaluate()

            # ---------------------------
            # 7. MODEL REGISTRY & DEPLOYMENT
            # ---------------------------
            logger.info("STEP 7: Registering & Deploying Best Model (MLflow/DagsHub)")

            registry = ModelRegistryAndDeploy(metric="recall")
            registry.run_deployment_pipeline()

            logger.info("Pipeline completed successfully")

            return best_model, results, evaluation

        except Exception as e:
            logger.error("Pipeline failed")
            raise FraudShieldException(str(e), sys)

# ----------------------------------
# CLI Testing
# ----------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the FraudShield ML pipeline")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of training rows for a quick run",
    )
    args = parser.parse_args()

    MLPipeline(limit=args.limit).run_pipeline()
import sys

from src.utils.logging import logger
from src.utils.exception import FraudShieldException

from src.components.data_ingestion import DataIngestion
from src.ETL.load import DataLoader
from src.ETL.transformation import DataTransformer

from src.components.data_feature_engineering import FeatureEngineer
from src.components.data_preparation import DataPreparation
from src.components.model_trainer import ModelTrainer


class MLPipeline:
    """
    End-to-end ML pipeline for FraudShield AI
    """

    def __init__(self, mongo_collection_name: str, limit: int = None):
        self.mongo_collection_name = mongo_collection_name
        self.limit = limit

    def run_pipeline(self):

        try:
            logger.info("========== ML PIPELINE STARTED ==========")

            # ---------------------------
            # 1. DATA EXTRACTION
            # ---------------------------
            logger.info("STEP 1: Data Extraction from MongoDB")

            extractor = DataIngestion(
                collection_name=self.mongo_collection_name,
                limit=self.limit
            )

            df = extractor.fetch_data()

            logger.info(f"Data extracted: {df.shape}")

            # ---------------------------
            # 2. TRANSFORMATION (ETL CLEANING)
            # ---------------------------
            logger.info("STEP 2: Data Transformation")

            transformer = DataTransformer(df)
            df = transformer.transform()

            logger.info(f"After transformation: {df.shape}")

            # ---------------------------
            # 3. FEATURE ENGINEERING
            # ---------------------------
            logger.info("STEP 3: Feature Engineering")

            fe = FeatureEngineer(df)
            df = fe.engineer_features()

            logger.info(f"After feature engineering: {df.shape}")

            # ---------------------------
            # 4. DATA PREPARATION
            # ---------------------------
            logger.info("STEP 4: Data Preparation")

            prep = DataPreparation(df)

            (
                X_train,
                X_test,
                y_train,
                y_test,
                _
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
                y_test
            )

            best_model, results = trainer.train_models()

            logger.info("Pipeline completed successfully")

            return best_model, results

        except Exception as e:
            logger.error("Pipeline failed")
            raise FraudShieldException(str(e), sys)
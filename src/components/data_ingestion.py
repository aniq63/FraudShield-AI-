# Data Ingestion
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from utils.logging import logger
from utils.exception import FraudShieldException


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DATASOURCE_DIR = os.path.join(PROJECT_ROOT, "datasource")

TRAIN_DATA_FILE = os.path.join(DATASOURCE_DIR, "train_sampled.csv")
TEST_DATA_FILE = os.path.join(DATASOURCE_DIR, "test_sampled.csv")


class DataIngestion:
    """
    Loads raw transaction data from CSV files in the datasource directory
    and returns it as a pandas DataFrame.
    """

    def __init__(self, file_path: str = None, limit: int = None):
        self.file_path = file_path or TRAIN_DATA_FILE
        self.limit = limit

    def fetch_data(self) -> pd.DataFrame:
        """
        Load a CSV file into a pandas DataFrame (with optional row limit).
        """

        try:
            logger.info(f"Starting data ingestion from CSV: {self.file_path}")

            df = pd.read_csv(self.file_path)

            if self.limit:
                logger.info(f"Ingesting up to {self.limit} records...")
                df = df.head(self.limit)

            if df.empty:
                raise ValueError(f"No records found in file: {self.file_path}")

            logger.info(
                f"Data ingestion completed successfully. Shape: {df.shape}"
            )

            return df

        except Exception as e:
            logger.error("Data ingestion failed")
            raise FraudShieldException(str(e), sys)
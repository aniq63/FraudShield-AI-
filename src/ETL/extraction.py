import os
import pandas as pd
import sys

from src.utils.logging import logger
from src.utils.exception import FraudShieldException


class DataExtractor:
    """
    Handles data ingestion from CSV source (initially notebook dataset).
    Designed to later support streaming ingestion (Kafka swap-ready).
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    def validate_file(self):
        """
        Validate if file exists and is accessible.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found at path: {self.file_path}")

        if not self.file_path.endswith(".csv"):
            raise ValueError("Only CSV files are supported for now.")

        logger.info(f"File validation successful: {self.file_path}")

    def load_data(self) -> pd.DataFrame:
        """
        Load CSV data into pandas DataFrame.
        """
        try:
            logger.info("Starting data extraction process...")

            # Step 1: Validate file
            self.validate_file()

            # Step 2: Read CSV
            df = pd.read_csv(self.file_path)

            # Step 3: Basic sanity check
            if df.empty:
                raise ValueError("Loaded dataset is empty.")

            logger.info(f"Data extraction completed. Shape: {df.shape}")

            return df

        except Exception as e:
            logger.error("Error occurred during data extraction.")
            raise FraudShieldException(
                str(e),
                sys
            )
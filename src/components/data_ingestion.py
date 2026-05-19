import sys
import pandas as pd

from src.db.mongo_connection import MongoDBClient
from src.utils.logging import logger
from src.utils.exception import FraudShieldException


class DataIngestion:
    """
    Fetches processed transaction data from MongoDB
    and returns it as a pandas DataFrame.
    """

    def __init__(self, collection_name: str, limit: int = None):
        self.mongo_client = MongoDBClient()
        self.collection = self.mongo_client.get_collection(collection_name)
        self.limit = limit

    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch documents from MongoDB collection
        and convert them into pandas DataFrame.
        """

        try:
            logger.info("Starting data ingestion from MongoDB...")

            # Fetch documents with optional limit
            if self.limit:
                logger.info(f"Ingesting up to {self.limit} records from MongoDB...")
                records = list(self.collection.find().limit(self.limit))
            else:
                logger.info("Ingesting all records from MongoDB...")
                records = list(self.collection.find())

            if not records:
                raise ValueError("No records found in MongoDB collection")

            # Convert to DataFrame
            df = pd.DataFrame(records)

            # Remove MongoDB internal ID
            if "_id" in df.columns:
                df.drop(columns=["_id"], inplace=True)

            logger.info(
                f"Data ingestion completed successfully. Shape: {df.shape}"
            )

            return df

        except Exception as e:
            logger.error("Data ingestion failed")
            raise FraudShieldException(str(e), sys)
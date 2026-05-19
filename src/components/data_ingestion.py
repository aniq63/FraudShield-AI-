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

    def __init__(self, collection_name: str):
        self.mongo_client = MongoDBClient()
        self.collection = self.mongo_client.get_collection(collection_name)

    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch all documents from MongoDB collection
        and convert them into pandas DataFrame.
        """

        try:
            logger.info("Starting data ingestion from MongoDB...")

            # Fetch documents
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
import sys
from src.utils.logging import logger
from src.utils.exception import FraudShieldException
from src.db.mongo_connection import MongoDBClient


class DataLoader:
    """
    Loads processed ETL data into MongoDB Atlas.
    """

    def __init__(self, collection_name : str):
        self.mongo_client = MongoDBClient()
        self.collection = self.mongo_client.get_collection(collection_name)

    def load_to_mongodb(self, df, batch_size: int = 500):
        try:
            logger.info("Starting MongoDB load process...")

            if df is None or df.empty:
                raise ValueError("Empty DataFrame cannot be loaded")

            records = df.to_dict(orient="records")
            total = len(records)

            for i in range(0, total, batch_size):
                batch = records[i:i + batch_size]

                try:
                    self.collection.insert_many(batch, ordered=False)
                    logger.info(f"Inserted batch {i} → {i + len(batch)}")

                except Exception as batch_error:
                    logger.error(f"Batch failed at {i}: {str(batch_error)}")
                    # continue pipeline instead of killing everything
                    continue

            logger.info("MongoDB load completed successfully")

        except Exception as e:
            logger.error("MongoDB load failed completely")
            raise FraudShieldException(str(e), sys)
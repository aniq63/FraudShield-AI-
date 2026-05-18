import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


class MongoDBClient:
    """
    MongoDB connection handler for FraudShield AI.
    Designed for safe reuse across ETL pipeline.
    """

    def __init__(self):
        self.uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("DB_NAME", "fraud_shield")

        if not self.uri:
            raise ValueError("MONGO_URI not found in environment variables")

        self.client = None
        self.db = None

    def connect(self):
        if self.client is None:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]

        return self.db

    def get_collection(self, collection_name: str):
        db = self.connect()
        return db[collection_name]

    def ping(self):
        try:
            db = self.connect()
            db.command("ping")
            return True
        except Exception as e:
            return False
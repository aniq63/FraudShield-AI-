from src.ETL.extraction import DataExtractor
from src.ETL.transformation import DataTransformer
from src.ETL.load import DataLoader


class ETLPipeline:

    def __init__(self, file_path, collection_name):
        self.file_path = file_path
        self.collection_name = collection_name

    def run(self):

        # 1. Extract
        extractor = DataExtractor(self.file_path)
        raw_df = extractor.load_data()

        # 2. Transform
        transformer = DataTransformer(raw_df)
        clean_df = transformer.transform()

        # 3. Load
        loader = DataLoader(self.collection_name)
        loader.load_to_mongodb(clean_df)

        return clean_df
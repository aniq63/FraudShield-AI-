import os
import boto3

from dotenv import load_dotenv

load_dotenv()


class S3Manager:
    """
    Handles AWS S3 operations.
    """

    def __init__(self):

        self.bucket_name = os.getenv(
            "AWS_BUCKET_NAME"
        )

        self.s3_client = boto3.client(
            "s3",

            aws_access_key_id=os.getenv(
                "AWS_ACCESS_KEY_ID"
            ),

            aws_secret_access_key=os.getenv(
                "AWS_SECRET_ACCESS_KEY"
            ),

            region_name=os.getenv(
                "AWS_DEFAULT_REGION"
            )
        )

    def upload_file(
        self,
        local_file_path,
        s3_file_name
    ):

        self.s3_client.upload_file(
            local_file_path,
            self.bucket_name,
            s3_file_name
        )

        return (
            f"s3://{self.bucket_name}/"
            f"{s3_file_name}"
        )
"""AWS S3 Connector to load bytes objects to S3"""

import os
import boto3

from esims_router.constants import S3Const as s3_c
from esims_router.logger import logger


class S3Connector:
    """AWS S3 Connector to load bytes objects to S3"""

    def __init__(self) -> None:
        """Initialize S3Connector"""
        self.bucket = os.getenv(s3_c.AWS_BUCKET)
        self.s3 = boto3.client(s3_c.S3)

    def load_data(self, data: bytes, key: str) -> str:
        """Loads bytes object to S3

        Args:
            data (bytes): Bytes object to load.
            key (str): key to load.

        Returns:
            str: S3 object URL.
        """
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)
        logger.info("Data loaded to S3: %s", key)
        return s3_c.OBJECT_URL.format(self.bucket, key)

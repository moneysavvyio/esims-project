"""AWS S3 Connector to load bytes objects to S3"""

import os
import json
import boto3

from esims_router.constants import AWSConst as aws_c
from esims_router.logger import logger


class S3Connector:
    """AWS S3 Connector to load bytes objects to S3"""

    def __init__(self) -> None:
        """Initialize S3Connector"""
        self.bucket = os.getenv(aws_c.AWS_BUCKET)
        self.s3 = boto3.client(aws_c.S3)

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
        return aws_c.OBJECT_URL.format(self.bucket, key)


class SQSConnector:
    """SQS Connector"""

    def __init__(self) -> None:
        """Initiate a SQS connection"""
        self.queue_name = os.getenv(aws_c.QUEUE_NAME)
        self.host = os.getenv(aws_c.QUEUE_HOST)
        self.queue_url = f"{self.host}/{self.queue_name}"
        self.runtime = boto3.client(aws_c.SQS)

    def publish(self, message: dict) -> None:
        """Publish given message to the queue.

        Args:
            message (dict): message to be published.
        """
        self.runtime.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message),
        )
        logger.info("Published message to invoke Lambda.")

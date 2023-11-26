"""AWS Services Connectors"""

import os
import boto3

from esimslib.connectors.constants import AWSConst as aws_c
from esimslib.util.logger import logger


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
        return self.s3.generate_presigned_url(
            ClientMethod=aws_c.CLIENT_METHOD,
            Params={
                aws_c.BUCKET: self.bucket,
                aws_c.KEY: key,
            },
            ExpiresIn=600,
        )


class SSMConnector:
    """AWS SSM Connector to load bytes objects to S3"""

    def __init__(self) -> None:
        """Initialize SSMConnector"""
        self.ssm = boto3.client(aws_c.SSM)

    def get_parameter(self, key: str) -> str:
        """Get parameter from SSM

        Args:
            key (str): key to get.

        Returns:
            str: parameter value.
        """
        response = self.ssm.get_parameter(Name=key, WithDecryption=True)
        return response.get(aws_c.PARAMETER).get(aws_c.VALUE)

    def update_parameter(self, key: str, value: str) -> None:
        """Set parameter in SSM

        Args:
            key (str): key to set.
            value (str): value to set.
        """
        self.ssm.put_parameter(
            Name=key,
            Value=value,
            Type=aws_c.PARAMETER_TYPE,
            Overwrite=True,
        )

"""AWS Services Connectors"""

import boto3

from refresh_dropbox.constants import AWSConst as aws_c


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

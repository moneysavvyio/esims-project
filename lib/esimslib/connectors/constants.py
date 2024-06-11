"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class DropBoxConst:
    """DropBox Defines"""

    # Env Variables
    DROPBOX_TOKEN = "DROPBOX_TOKEN"  # nosec


class AWSConst:
    """AWS S3 Defines"""

    # Env Variables
    AWS_BUCKET = "AWS_BUCKET"

    # Services
    S3 = "s3"
    SSM = "ssm"

    # URL Generation
    CLIENT_METHOD = "get_object"
    BUCKET = "Bucket"
    KEY = "Key"
    SKIP_CHARACHTER = "/"

    # SSM
    PARAMETER = "Parameter"
    VALUE = "Value"
    SECURE_STRING_TYPE = "SecureString"
    STRING_TYPE = "String"

"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class RouterConst:
    """RouterConst"""

    ENTRIES = "ENTRIES"
    STATE_KEY = "LAMBDA_STATE_KEY"

    # Lambda states
    ON = "ON"
    OFF = "OFF"


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

    # SSM
    PARAMETER = "Parameter"
    VALUE = "Value"
    PARAMETER_TYPE = "String"


class AirTableConst:
    """AirTable Defines"""

    # Env Variables
    AIRTABLE_API_KEY = "AIRTABLE_API_KEY"  # nosec
    AIRTABLE_BASE_ID = "AIRTABLE_BASE_ID"
    AIRTABLE_TABLE_NAME = "AIRTABLE_TABLE_NAME"

    # fields
    SIM = "SIM"
    ATTACHMENT = "Attachment"

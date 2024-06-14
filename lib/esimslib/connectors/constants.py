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


class LayanTConst:
    """ Layan-T Constants """

    # Env Variables
    API_URL="https://api.layan-t.net/api/"
    CUSTOMER_NAME="app"

    WE_PACKAGE_ID="50dfa8f5-064c-4b48-1740-08d93984cc72"
    WE_PACKAGE_PRICE=30
    
    HOT_PACKAGE_ID="f74f8b57-f2c3-46a1-74fa-08dc2b1b7f70"
    HOT_PACKAGE_PRICE=40

    # auth
    LAYANT_USERNAME = "LAYANT_USERNAME"
    LAYANT_PASSWORD = "LAYANT_PASSWORD"
    LAYANT_TOKEN = "LAYANT_TOKEN"
   

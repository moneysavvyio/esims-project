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

    # SSM
    PARAMETER = "Parameter"
    VALUE = "Value"
    SECURE_STRING_TYPE = "SecureString"
    STRING_TYPE = "String"


class AirTableConst:
    """AirTable Defines"""

    # Env Variables
    AIRTABLE_API_KEY = "AIRTABLE_API_KEY"  # nosec
    AIRTABLE_BASE_ID = "AIRTABLE_BASE_ID"
    AIRTABLE_TABLE_NAME = "AIRTABLE_TABLE_NAME"

    # Table Variables
    FIELDS = "fields"
    ID = "id"
    DEFAULT_VIEW = "backend_service"

    # Attachment Table Fields
    SIM = "eSIM Provider"
    ATTACHMENT = "Attachments"


class ProvidersModelConst:
    """Providers Model Defines"""

    TABLE_NAME = "eSIM Providers"

    # Table Variables
    NAME = "Name"


class DonationsModelConst:
    """Donations Model Defines"""

    TABLE_NAME = "ESim Donations"

    # Table Variables
    ESIM_PROVIDER = "eSIM Provider"
    QR_CODE = "QR Codes"
    IN_USE_FLAG = "QR Code In Use"


class AttachmentModelConst:
    """Attachment Model Defines"""

    TABLE_NAME = "E-SIMs Linked"

    # Table Variables
    ESIM_PROVIDER = "eSIM Provider"
    ATTACHMENT = "Attachments"

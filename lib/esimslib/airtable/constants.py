"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class AirTableConst:
    """AirTable Defines"""

    # Env Variables
    AIRTABLE_API_KEY = "AIRTABLE_API_KEY"  # nosec
    AIRTABLE_BASE_ID = "AIRTABLE_BASE_ID"
    AIRTABLE_TABLE_NAME = "AIRTABLE_TABLE_NAME"

    # Table Variables
    DEFAULT_VIEW = "backend_service"


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

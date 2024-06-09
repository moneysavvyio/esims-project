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
    QR_TEXT = "qr_text"
    STOCK_ERR = "stocking_err"
    RENEWABLE = "Renewable"


class DonationsModelConst:
    """Donations Model Defines"""

    TABLE_NAME = "ESim Donations"

    # Table Variables
    ESIM_PROVIDER = "eSIM Provider"
    QR_CODE = "QR Codes"
    IN_USE_FLAG = "QR Code In Use"
    DONOR_ERROR = "Donor Error"
    INVALID_TYPE = "Invalid Type"
    MISSING_QR = "Missing QR Code"
    PROVIDER_MISMATCH = "Provider Mismatch"
    EMAIL = "Email"
    DUPLICATE = "Duplicate"
    ORIGINAL = "Original Donation"
    DIFF_EMAIL = "Different Email"

    # QR Codes Keys
    URL = "url"
    SHA = "sha"

    # Set Values
    YES = "Yes"


class AttachmentModelConst:
    """Attachment Model Defines"""

    TABLE_NAME = "E-SIMs Linked"

    # Table Variables
    ESIM_PROVIDER = "eSIM Provider"
    DONOR = "Linked Donation"
    ATTACHMENT = "Attachments"
    QR_SHA = "QR SHA"
    ORDER_ID = "ID"
    ESIM_PHONE_NUMBER = "eSIM Phone Number"


class InventoryConst:
    """Airtable Defines"""

    TABLE_NAME = "Inventory Check"

    # Field Names
    PROVIDER_GEO = "Provider_Geo"
    PROVIDER = "Provider"
    GEO = "Geo"
    LOW_FLAG = "Low Inventory"
    IN_STOCK = "In Stock"

    # wecom ID
    WECOM_ID = "recfYIKXh1IydF3G2"

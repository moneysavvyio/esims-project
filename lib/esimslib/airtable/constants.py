"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class AirTableConst:
    """AirTable Defines"""

    # Env Variables
    AIRTABLE_API_KEY = "AIRTABLE_API_KEY"  # nosec
    AIRTABLE_BASE_ID = "AIRTABLE_BASE_ID"
    AIRTABLE_TABLE_NAME = "AIRTABLE_TABLE_NAME"

    # View Name
    DEFAULT_VIEW = "backend_service"


class EsimProviderConst:
    """eSIM Providers Constants."""

    TABLE_NAME = "eSIM Providers"

    # Field Names
    PROVIDER_GEO = "Provider_Geo"
    PROVIDER = "Provider"
    GEO = "Geo"
    STOCK_STATUS = "Stock Status"
    IN_STOCK = "In Stock"
    SMDP_DOMAIN = "smdp_domain"
    AUTOMATIC_RESTOCK = "Automatic Restock"
    RENEWABLE = "Renewable"
    PACKAGES = "eSIM Packages"


class EsimPackageConst:
    """eSIM Package Constants."""

    TABLE_NAME = "eSIM Packages"

    # Field Names
    PACKAGE = "Package"
    ESIM_PROVIDER = "eSIM Provider"
    STOCK_ERR = "stocking_err"


class EsimAssetConst:
    """eSIM Asset Constants"""

    TABLE_NAME = "eSIM Inventory"

    # Field Names
    ESIM_PACKAGE = "eSIM Package"
    QR_CODE = "QR Code"
    QR_SHA = "qr_sha"
    DONATION = "Donation Record"
    PHONE_NUMBER = "eSIM Phone Number"
    CHECKED_IN = "checked_in"


class EsimDonationConst:
    """eSIM Donations Constants"""

    TABLE_NAME = "eSIM Donations"

    # Field Names
    ESIM_PACKAGE = "eSIM Package"
    QR_CODES = "QR Codes"
    INGESTED_FLAG = "Ingested?"
    REJECTED_FLAG = "Rejected?"
    IS_INVALID_TYPE = "Is Invalid Type"
    MISSING_QR = "Missing QR Code"
    PROVIDER_MISMATCH = "Provider Mismatch"
    IS_DUPLICATE = "Is Duplicate"
    PROTOCOL_MISMATCH = "Protocol Mismatch"
    MISSING_PHONE_NUMBER = "Missing Phone Number"
    ORIGINAL_DONATION = "Original Donation"
    SEND_ERROR_EMAIL = "Send Error Email"

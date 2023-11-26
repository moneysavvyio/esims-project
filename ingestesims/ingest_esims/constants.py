"""Ingest eSIMs service defines"""

# pylint: disable=too-few-public-methods


class IngestSimsConst:
    """Ingest Sims Defines"""

    # Table Name
    TABLE_NAME = "ESim Donations"

    # Fields
    TARGET_FOLDER = "eSIM Provider Name"
    ATTACHMENTS = "QR Codes"
    FILE_NAME = "filename"
    URL = "url"

    # Root Folder
    DBX_PATH = "/ESims for Gaza/Fresh Sims to Load in Airtable/{}"

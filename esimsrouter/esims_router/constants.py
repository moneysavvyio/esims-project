"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class RouterConst:
    """RouterConst"""

    # Env Variables
    ENTRIES = "ENTRIES"
    STATE_KEY = "LAMBDA_STATE_KEY"

    # Lambda states
    ON = "ON"
    OFF = "OFF"

    # Table Names
    CARRIERS_TABLE_NAME = "CARRIERS_TABLE_NAME"
    ATTACHMENT_TABLE_NAME = "ATTACHMENT_TABLE_NAME"

    # Root Folder
    DBX_PATH = "/ESims for Gaza/Fresh Sims to Load in Airtable/{}"

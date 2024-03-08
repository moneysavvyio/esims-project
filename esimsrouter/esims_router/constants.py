"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class RouterConst:
    """RouterConst"""

    # Env Variables
    STATE_KEY = "LAMBDA_STATE_KEY"

    # Lambda states
    ON = "ON_{count}"
    OFF = "OFF"
    DELIMITER = "_"

    # Root Folder
    DBX_PATH = "/ESims for Gaza/Fresh Sims to Load in Airtable/{}"

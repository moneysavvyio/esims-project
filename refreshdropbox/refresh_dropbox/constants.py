"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class RefreshConst:
    """RouterConst"""

    # Env Variables
    APP_KEY = "APP_KEY"
    APP_SECRET = "APP_SECRET"
    REFRESH_TOKEN = "REFRESH_TOKEN"
    DROPBOX_TOKEN = "DROPBOX_TOKEN"


class RequestConst:
    """Request Defines"""

    REFRESH_URL = "https://api.dropbox.com/oauth2/token"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"
    REFRESH_TOKEN = "refresh_token"
    GRANT_TYPE = "grant_type"
    ACCESS_TOKEN = "access_token"


class AWSConst:
    """AWS Defines"""

    # Services
    SSM = "ssm"

    # SSM
    PARAMETER = "Parameter"
    VALUE = "Value"
    PARAMETER_TYPE = "SecureString"

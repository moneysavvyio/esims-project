"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class RefreshConst:
    """RouterConst"""

    # Env Variables
    APP_KEY = "APP_KEY"
    APP_SECRET = "APP_SECRET"  # nosec
    REFRESH_TOKEN = "REFRESH_TOKEN"  # nosec
    DROPBOX_TOKEN = "DROPBOX_TOKEN"  # nosec


class RequestConst:
    """Request Defines"""

    REFRESH_URL = "https://api.dropbox.com/oauth2/token"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"  # nosec
    REFRESH_TOKEN = "refresh_token"  # nosec
    GRANT_TYPE = "grant_type"
    ACCESS_TOKEN = "access_token"  # nosec


class AWSConst:
    """AWS Defines"""

    # Services
    SSM = "ssm"

    # SSM
    PARAMETER = "Parameter"
    VALUE = "Value"
    PARAMETER_TYPE = "SecureString"

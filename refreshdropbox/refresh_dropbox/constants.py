"""Dropbox Connector Defines"""

# pylint: disable=too-few-public-methods


class RefreshConst:
    """RouterConst"""

    # Env Variables
    APP_KEY = "APP_KEY"
    APP_SECRET = "APP_SECRET"
    REFRESH_TOKEN = "REFRESH_TOKEN"

    # Request
    REFRESH_URL = "https://api.dropbox.com/oauth2/token"
    GRANT_TYPE = "refresh_token"


class AWSConst:
    """AWS Defines"""

    # Services
    SSM = "ssm"

    # SSM
    PARAMETER = "Parameter"
    VALUE = "Value"
    PARAMETER_TYPE = "SecureString"

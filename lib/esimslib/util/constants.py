"""Utils Constants"""

import re

# pylint: disable=too-few-public-methods


class QRCodeConst:
    """QR Code Processor constants."""

    UTF8 = "utf-8"
    UINT8 = "uint8"
    PSM = "--psm 11"
    PHONE_PATTERN = re.compile(r"\b(?:055|051|053)\d{7}\b")
    LPA = "LPA:1$"

"""Helper library to support logging"""

import os
import logging
import sys

DEBUG = os.getenv("DEBUG", "")

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
if DEBUG == "TRUE":
    logger.setLevel(logging.DEBUG)
    handler.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
    handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# control logging for boto3
logging.getLogger("botocore").setLevel(logging.INFO)

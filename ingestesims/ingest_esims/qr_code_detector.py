"""QR Code Detector"""

import requests
import cv2
import numpy as np

from pyzbar.pyzbar import decode

from esimslib.util.logger import logger

# pylint: disable=no-member


class QRCodeDetector:
    """QR Code Detector"""

    def __init__(self, url: str) -> None:
        """QR Code Detector

        Args:
            url (str): Image URL to detect QR Code.
        """
        self.url = url

    def _read_image(self) -> np.ndarray:
        """Format Image from url

        Returns:
            np.ndarry: Image array from URL
        """
        try:
            response = requests.get(self.url, timeout=30)
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to read image: %s", exc)
            raise exc
        image = np.asarray(bytearray(response.content), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image

    def detect(self) -> bool:
        """Detect QR Code

        Returns:
            bool: True if QR Codel is detected, False otherwise.
        """
        return bool(decode(self._read_image()))

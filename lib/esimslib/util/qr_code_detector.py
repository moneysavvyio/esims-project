"""QR Code Detector"""

import requests
import cv2
import numpy as np

from pyzbar.pyzbar import decode, ZBarSymbol

from esimslib.util.logger import logger
from esimslib.util.constants import QRConst as qr_c

# pylint: disable=no-member


class QRCodeDetector:
    """QR Code Detector"""

    def __init__(self, url: str) -> None:
        """QR Code Detector

        Args:
            url (str): Image URL to detect QR Code.
        """
        self.url = url
        self.qr_code: str = ""

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
        image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
        return image

    def _detect_fall_back(self) -> bool:
        """Detect QR Code

        Returns:
            bool: True if QR Codel is detected, False otherwise.
        """
        _, image = cv2.threshold(
            self._read_image(),
            127,
            255,
            cv2.THRESH_OTSU,
        )
        qr_code = decode(image, symbols=[ZBarSymbol.QRCODE])
        if bool(qr_code):
            self.qr_code = qr_code[0].data.decode(qr_c.UTF8)
        return bool(qr_code)

    def detect(self) -> bool:
        """Detect QR Code

        Returns:
            bool: True if QR Codel is detected, False otherwise.
        """
        try:
            qr_code = decode(self._read_image(), symbols=[ZBarSymbol.QRCODE])
            if bool(qr_code):
                self.qr_code = qr_code[0].data.decode(qr_c.UTF8)
                return True
        except TypeError:
            logger.warning("Failed to read image type: %s", self.url)
            return False
        return self._detect_fall_back()

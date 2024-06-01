"""QR Code Detector"""

import hashlib
import requests
import cv2
import numpy as np

from pyzbar.pyzbar import decode, ZBarSymbol

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
        self._qr_code: str = ""

    @property
    def qr_code(self) -> str:
        """QR Code

        Returns:
            str: QR Code
        """
        return self._qr_code

    @qr_code.setter
    def qr_code(self, value: bytes) -> None:
        """Set QR Code from bytes.

        Args:
            value (bytes): QR Code info in bytes
        """
        self._qr_code = value.decode("utf-8")
        self.qr_sha = hashlib.sha256(value).hexdigest()

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
            self.qr_code = qr_code[0].data
        return bool(qr_code)

    def detect(self) -> bool:
        """Detect QR Code

        Returns:
            bool: True if QR Code is detected, False otherwise.
        """
        try:
            qr_code = decode(self._read_image(), symbols=[ZBarSymbol.QRCODE])
            if bool(qr_code):
                self.qr_code = qr_code[0].data
                return True
        except TypeError:
            logger.warning("Failed to read image type: %s", self.url)
            return False
        return self._detect_fall_back()

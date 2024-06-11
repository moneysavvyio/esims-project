"""QR Code Processor

Manages all QR code operations.
- QR Code Detection.
- Data extraction.
- QR SHA generation.
- QR code generation from text.
- Image Captioner.
- Phone number extraction.

"""

from typing import List

import hashlib
import requests
import cv2
import numpy as np
import pytesseract

from cached_property import cached_property
from pyzbar.pyzbar import decode, ZBarSymbol

from esimslib.util.logger import logger
from esimslib.util.constants import QRCodeConst as qr_c


# pylint: disable=no-member


class QRCodeProcessor:
    """QR Code Processor"""

    def __init__(self, url: str) -> None:
        """QR Code Detector

        Args:
            url (str): Image URL to detect QR Code.
        """
        self.url = url
        self._qr_code: str = ""
        self._phone_number: str = ""

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
        self._qr_code = value.decode(qr_c.UTF8)
        self.qr_sha = hashlib.sha256(value).hexdigest()

    @property
    def phone_number(self) -> str:
        """Phone Number

        Returns:
            str: Phone Number
        """
        return self._phone_number

    @cached_property
    def image(self) -> np.ndarray:
        """Image

        Returns:
            np.ndarray: Image array from URL
        """
        return self._read_image()

    def _read_image(self) -> np.ndarray:
        """Format Image from url

        Returns:
            np.ndarry: Image array from URL
        """
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to read image: %s", exc)
            raise exc
        image = np.asarray(bytearray(response.content), dtype=qr_c.UINT8)
        image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
        return image

    def _detect_qr_fall_back(self) -> bool:
        """Detect QR Code fall back helper method.

        Returns:
            bool: True if QR Code is detected, False otherwise.
        """
        _, image = cv2.threshold(
            self.image,
            127,
            255,
            cv2.THRESH_OTSU,
        )
        qr_code = decode(image, symbols=[ZBarSymbol.QRCODE])
        if bool(qr_code):
            self.qr_code = qr_code[0].data
        return bool(qr_code)

    def detect_qr(self) -> bool:
        """Detect QR Code

        Returns:
            bool: True if QR Code is detected, False otherwise.
        """
        try:
            qr_code = decode(self.image, symbols=[ZBarSymbol.QRCODE])
            if bool(qr_code):
                self.qr_code = qr_code[0].data
                return True
        except TypeError:
            logger.warning("Failed to read image type: %s", self.url)
            return False
        return self._detect_qr_fall_back()

    def detect_phone_number(self) -> bool:
        """Detect Phone Number

        Returns:
            bool: True if Phone Number is detected, False otherwise.
        """
        try:
            _, image = cv2.threshold(
                self.image,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            )
            image_text = pytesseract.image_to_string(image, config=qr_c.PSM)
            # Find phone numbers in
            phone_numbers = qr_c.PHONE_PATTERN.findall(image_text)

            if not bool(phone_numbers):
                return False

            self._phone_number = phone_numbers[0]
            return True
        except TypeError:
            logger.warning("Failed to read image type: %s", self.url)
            return False

    def validate_qr_code_protocol(self) -> bool:
        """Validate QR Code is an eSIM with the protocol set to LPA.

        Returns:
            bool: True if QR Code is an eSIM, False otherwise.
        """
        if self._qr_code.startswith(qr_c.LPA):
            return True
        return False

    def validate_smdp_domain(self, smdp_domains: List[str]) -> bool:
        """Validate qr content against the given smdp domain.

        Args:
            smdp_domains (List[str]): list of smdp domains.

        Returns:
            bool: True if qr content matches smdp domain, False otherwise.
        """
        if any(v in self._qr_code for v in smdp_domains):
            return True
        return False

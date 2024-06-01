"""Image Phone Number Reader"""

from esimslib.util.logger import logger
import requests
import pytesseract
from PIL import Image
import re
from io import BytesIO

# pylint: disable=no-member

class ImagePhoneNumberReader:
    """Image Phone Number Reader"""

    def __init__(self, url: str) -> None:
        """Image Phone Number Reader

        Args:
            url (str): Image URL to detect phone number
        """
        self.url = url
        self._phone_number: str = ""

    @property
    def phone_number(self) -> str:
        """Phone Number

        Returns:
            str: Phone Number
        """
        return self._phone_number


    def _read_image(self) -> Image.Image:
        """Format Image from url

        Returns:
            Image.Image: PIL Binary image object
        """
        try:
            response = requests.get(self.url, timeout=30)
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to read image: %s", exc)
            raise exc
        
        img = Image.open(BytesIO(response.content))
        img = img.convert('L')  # Convert to grayscale
        img = img.point(lambda x: 0 if x < 140 else 255)  # Binarize image
        return img

    def extract_text_from_image(self) -> str:
        """Get all text from the image

        Returns:
            Image.Image:: PIL Image object
        """
        image = self._read_image()
        text = pytesseract.image_to_string(image)
        return text

    def read_phone_number(self) -> bool:
        """Read phone number

        Returns:
            bool: True if phone number is read, False otherwise.
        """
        try:
            image_text = self.extract_text_from_image()

            pattern = re.compile(r'\b(?:055|051)\d{7}\b')
            # Find phone numbers in 
            phone_numbers = pattern.findall(image_text)
            
            if not bool(phone_numbers):
                return False
            
            self._phone_number = phone_numbers[0]
            return True
        except TypeError:
            logger.warning("Failed to read image type: %s", self.url)
            return False

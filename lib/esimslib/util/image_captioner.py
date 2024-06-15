""" Add captions to images from URL """

from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

from esimslib.util import logger

class ImageWithCaption:
    def __init__(self, image_url: str, title: str, text_line_1: str, text_line_2: str, text_line_3: str, text_line_4: str) -> None:
        self.image_url = image_url
        self.title = title
        self.text_line_1 = text_line_1
        self.text_line_2 = text_line_2
        self.text_line_3 = text_line_3
        self.text_line_4 = text_line_4
        self.image_bytes = None

    def create_image(self) -> BytesIO:
        """
        Creates the image with captions and returns image bytes
        """
        # Load the image from the URL
        response = requests.get(self.image_url)
        image = Image.open(BytesIO(response.content))

        # Define the dimensions and margins
        image_width, image_height = image.size
        margin_top = 40
        margin_bottom = 138
        margin_side = 124
        canvas_width = image_width + margin_side
        canvas_height = image_height + margin_top + margin_bottom

        # Create a new white background image
        final_image = Image.new('RGB', (canvas_width, canvas_height), 'white')
        
        # Paste the original image onto the white background with margins
        final_image.paste(image, (margin_side // 2, margin_top))

        # Prepare to draw text
        draw = ImageDraw.Draw(final_image)

        # Load a font that supports Arabic characters
        # TODO: ensure the font is in the correct location this will fail
        try:
            font = ImageFont.truetype("Noto_Naskh_Arabic/NotoNaskhArabic-VariableFont_wght.ttf", 22)
        except IOError:
            logger.error("Font file not found. Please make sure 'esimissuer/Noto_Naskh_Arabic/NotoNaskhArabic-VariableFont_wght.ttf' is in the working directory.")
            raise

        # Draw the title text on top
        title_y_position = margin_top - 15
        draw.text((canvas_width // 2, title_y_position), self.title, fill='black', font=font, anchor="mm")

        # Set the text properties
        text_y_position = image_height + margin_top + 28
        line_spacing = 28

        # Draw the text lines below the image
        draw.text((canvas_width // 2, text_y_position), self.text_line_1, fill='black', font=font, anchor="mm")
        text_y_position += line_spacing

        draw.text((canvas_width // 2, text_y_position), self.text_line_2, fill='black', font=font, anchor="mm")
        text_y_position += line_spacing

        draw.text((canvas_width // 2, text_y_position), self.text_line_3, fill='black', font=font, anchor="mm")
        text_y_position += line_spacing

        draw.text((canvas_width // 2, text_y_position), self.text_line_4, fill='black', font=font, anchor="mm")
        text_y_position += line_spacing

        # Save the final image to a bytes object
        image_bytes = BytesIO()
        final_image.save(image_bytes, format='PNG')
        image_bytes.seek(0)  # Reset the stream position to the beginning

        self.image_bytes = image_bytes
        return image_bytes
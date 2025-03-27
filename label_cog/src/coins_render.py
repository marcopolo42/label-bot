import os
from PIL import Image, ImageOps, ImageChops
import fitz # PyMuPDF

from label_cog.src.image_utils import create_image_with_text, add_text_in_middle_of_image, add_margins
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.assets import Assets
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)


def render_coins_image(coins):
    img_coin = Assets().get('coin.png').copy()
    if not img_coin:
        logger.critical("Coin image not found in assets")
        return None
    add_text_in_middle_of_image(img_coin, f"{coins}", 128)
    return img_coin


def add_price_icon(img, price):
    img_price = render_coins_image(price)
    img_price = add_margins(img_price, (0, 0, 0, 0), dpi=300, color=(0, 0, 0, 0))
    # allaways positive ratio
    ratio = abs(img.width / img_price.width)

    position = (img.width - img_price.width, 0)
    #because the original image is only grayscale we need to convert it to RGB so that the coin is colored after pasting
    img = img.convert("RGB")
    img.paste(img_price, position, img_price)
    return img

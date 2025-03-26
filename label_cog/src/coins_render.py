import os
from PIL import Image, ImageOps, ImageChops
import fitz # PyMuPDF

from label_cog.src.image_utils import create_image_with_text, add_text_in_middle_of_image
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.utils import get_cache_directory
from label_cog.src.assets import Assets
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)


def render_coins_image(coins): #todo change to return a PIL image instead of saving to disk
    img_coin = Assets().get('coin.png').copy()
    if not img_coin:
        logger.critical("Coin image not found in assets")
        return None
    add_text_in_middle_of_image(img_coin, f"{coins}", 128)
    return img_coin


def add_price_icon(img, price):
    img_price = render_coins_image(price)
    position = (img.width - img_price.width, 0)
    img.paste(img_price, position, img_price)
    return img

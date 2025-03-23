import os
from PIL import Image, ImageOps, ImageChops
import fitz # PyMuPDF

from label_cog.src.image_utils import create_image_with_text, add_text_in_middle_of_image
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.utils import get_cache_directory
from label_cog.src.assets import Assets
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)


def render_coins_image(coins):
    img_coin = Assets().get('coin.png')
    if not img_coin:
        logger.error("Coin image not found in assets")
        return None
    add_text_in_middle_of_image(img_coin, f"{coins}", 128)
    coin_img_path = os.path.join(get_cache_directory(), 'coin.png')
    img_coin.save(coin_img_path)
    return coin_img_path


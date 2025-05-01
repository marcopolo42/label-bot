import asyncio
import requests
from label_cog.src.template_backend_utils import fetch_one_meme
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.template_backend_utils import get_img_base64_with_size, save_img_from_url
logger = setup_logger(__name__)


async def process_data(data):
    meme_url = fetch_one_meme()
    if meme_url is None:
        logger.debug("Failed to fetch meme")
        return None
    else:
        logger.debug(f"Meme URL: {meme_url}")
        img = await save_img_from_url(meme_url)
        new_data = await asyncio.to_thread(get_img_base64_with_size, img)
        return new_data

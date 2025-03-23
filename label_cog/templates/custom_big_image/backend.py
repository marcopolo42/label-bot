import base64
import requests
from io import BytesIO
from PIL import Image
import mimetypes
import os


import asyncio
import aiofiles
from pathlib import Path

#for tests
import time

import datetime
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.image_utils import open_image_aio, convert_pil_to_base64_image, get_mime_type
from label_cog.src.template_backend_utils import get_maximum_size_for_paper
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)
CACHE_FOLDER = os.path.join(os.getcwd(), "label_cog", "cache")



async def process_data(data):
    user_id = data.get("user_id", "")

    img_path = data.get("img_path", None)
    logger.debug(f"File found: {img_path}")
    if img_path is None: # Timeout of 5 minutes
        logger.debug("img_path is None")
        return {}
    img = await open_image_aio(img_path)
    height, width = get_maximum_size_for_paper(img.size)
    mime_type = get_mime_type(img_path)
    img_base64 = convert_pil_to_base64_image(img, mime_type)
    new_data = {
        "img_base64": img_base64,
        "img_height": height,
        "img_width": width
    }
    return new_data


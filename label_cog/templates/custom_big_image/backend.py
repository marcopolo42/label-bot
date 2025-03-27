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
from label_cog.src.image_utils import convert_pil_to_base64_image
from label_cog.src.template_backend_utils import get_maximum_size_for_paper
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)


async def process_data(data):
    img_bytes = data.get("img_bytes", None)
    if img_bytes is None: # to handle the timeout of 5 minutes
        logger.debug("img_path is None")
        return {}
    img = Image.open(BytesIO(img_bytes))
    height, width = get_maximum_size_for_paper(img.size)
    img_base64 = convert_pil_to_base64_image(img)
    new_data = {
        "img_base64": img_base64,
        "img_height": height,
        "img_width": width
    }
    return new_data


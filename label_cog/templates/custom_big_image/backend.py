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
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)
CACHE_FOLDER = os.path.join(os.getcwd(), "label_cog", "cache")


# Convert an image to a Base64-encoded string with MIME prefix
def get_base64_image(img, mime_type):
    try:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:{mime_type};base64,{img_str}"
    except Exception as e:
        raise Exception(f"Error while converting image to base64: {e}")


async def get_image_from_cache(image_path):
    async with aiofiles.open(image_path, 'rb') as f:
        img_data = await f.read()
    img = Image.open(BytesIO(img_data))
    return img


def get_mime_type(img_name):
    mime_type, _ = mimetypes.guess_type(img_name)
    if mime_type is None:
        raise ValueError(f"Cannot determine MIME type for file: {img_name}")
    return mime_type


def get_maximum_size_for_paper(size):
    smaller_side = 62
    width, height = size
    logger.debug(f"Original size: {width}x{height}")
    if height < width:
        aspect_ratio = height / width
        logger.debug(f"Aspect ratio: {aspect_ratio}")
        width = smaller_side / aspect_ratio
        height = smaller_side
    else:
        aspect_ratio = width / height
        logger.debug(f"Aspect ratio: {aspect_ratio}")
        height = smaller_side / aspect_ratio
        width = smaller_side
    # round to no decimal places
    width = round(width)
    height = round(height)
    logger.debug(f"Page size in width: {width}mm and height: {height}mm")
    return height, width


async def process_data(data):
    user_id = data.get("user_id", "")

    img_path = data.get("img_path", None)
    logger.debug(f"File found: {img_path}")
    if img_path is None: # Timeout of 5 minutes
        logger.debug("img_path is None")
        return {}
    img = await get_image_from_cache(img_path)
    height, width = get_maximum_size_for_paper(img.size)
    mime_type = get_mime_type(img_path)
    img_base64 = get_base64_image(img, mime_type)
    new_data = {
        "img_base64": img_base64,
        "img_height": height,
        "img_width": width
    }
    return new_data


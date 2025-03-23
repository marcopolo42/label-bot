import base64
import requests
from io import BytesIO
from PIL import Image
import mimetypes
import os


import asyncio
import aiofiles
from pathlib import Path

import datetime
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.image_utils import open_image_aio, convert_pil_to_base64_image, get_mime_type
logger = setup_logger(__name__)


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
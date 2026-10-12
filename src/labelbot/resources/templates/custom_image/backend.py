import asyncio
import base64
import requests
from io import BytesIO
from PIL import Image
import mimetypes
import os


import aiofiles
from pathlib import Path

#for tests
import time

import datetime
from labelbot.logging import setup_logger
from labelbot.rendering.images import convert_pil_to_base64_image
from labelbot.rendering.backends import get_maximum_size_for_paper
from labelbot.rendering.backends import get_img_base64_with_size
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)


def process_data(data):
    img_bytes = data.get("img_bytes", None)
    if img_bytes is None: # to handle the timeout of 5 minutes
        logger.debug("img_path is None")
        return {}
    img = Image.open(BytesIO(img_bytes))
    new_data = get_img_base64_with_size(img)
    return new_data


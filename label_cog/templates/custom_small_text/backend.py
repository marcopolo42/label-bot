import base64
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import mimetypes
import os
import asyncio
import aiofiles
from pathlib import Path

#for tests
import time

import datetime
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.image_utils import create_image_with_text, convert_pil_to_base64_image
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)
CACHE_FOLDER = os.path.join(os.getcwd(), "label_cog", "cache")


async def process_data(data):
    text = data.get("text", "Error: No text provided")
    img = create_image_with_text(text, 256)
    img_base64 = convert_pil_to_base64_image(img)
    new_data = {
        "img_base64": img_base64,
    }
    return new_data


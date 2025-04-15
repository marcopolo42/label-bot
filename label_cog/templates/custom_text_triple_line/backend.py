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
from label_cog.src.image_utils import create_image_with_text, convert_pil_to_base64_image, join_images_vertically
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)


async def process_data(data):
    text = data.get("text", "Error: No text provided")
    text2 = data.get("text2", "Error: No text2 provided")
    text3 = data.get("text3", "Error: No text3 provided")
    img = create_image_with_text(text, 256)
    img2 = create_image_with_text(text2, 256)
    img3 = create_image_with_text(text3, 256)
    img = img.crop((0, 45, img.width, img.height))
    joined_img = join_images_vertically(img, img2, padding_between=10)
    joined_img = join_images_vertically(joined_img, img3, padding_between=10)
    img_base64 = convert_pil_to_base64_image(joined_img)
    new_data = {
        "img_base64": img_base64,
    }
    return new_data


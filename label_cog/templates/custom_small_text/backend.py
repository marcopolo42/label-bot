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
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)
CACHE_FOLDER = os.path.join(os.getcwd(), "label_cog", "cache")


def get_mime_type(img_name):
    mime_type, _ = mimetypes.guess_type(img_name)
    if mime_type is None:
        raise ValueError(f"Cannot determine MIME type for file: {img_name}")
    return mime_type


# Convert an image to a Base64-encoded string with MIME prefix
def convert_pil_to_base64_image(img, mime_type):
    try:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:{mime_type};base64,{img_str}"
    except Exception as e:
        raise Exception(f"Error while converting image to base64: {e}")


async def read_image(image_path):
    async with aiofiles.open(image_path, 'rb') as f:
        img_data = await f.read()
    img = Image.open(BytesIO(img_data))
    return img


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


#create a image with text inside it the size is defined by the font size
def create_image_with_text(text, font_size):
    # Load a font (Ensure the font file is accessible)
    # if dev fonts from macos and if prod fonts from linux
    if os.getenv("ENV") == "dev": #macos
        user_path = Path.home()
        font_path = os.path.join(user_path, "Library", "Fonts", "DejaVuSans.ttf") #the dev needs to install the font
    elif os.getenv("ENV") == "prod": #linux
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    else:
        raise ValueError("ENV is not defined")

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")

    # Get the font and calculate text size
    font = ImageFont.truetype(font_path, font_size)
    left, top, right, bottom = font.getbbox(text)
    text_width = right
    text_height = bottom

    logger.debug(f"Text size: {text_width}x{text_height}")
    # Add padding
    padding = 0
    image_width = int(text_width + (padding * 2))
    image_height = int(text_height + (padding * 2))

    # Create a white image
    img = Image.new('RGB', (image_width, image_height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw the text centered on the image
    text_x = padding
    text_y = padding
    draw.text((text_x, text_y), text, font=font, fill='black')
    logger.debug(f"imagesize: {img.size}")
    logger.debug(f"Created image with dimensions: {image_width}x{image_height}")
    return img


async def process_data(data):
    text = data.get("text", "Error: No text provided")
    img = create_image_with_text(text, 256)
    img_base64 = convert_pil_to_base64_image(img, "image/png")
    new_data = {
        "img_base64": img_base64,
    }
    return new_data


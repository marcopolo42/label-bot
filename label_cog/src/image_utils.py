import os
from PIL import Image, ImageOps
import fitz # PyMuPDF
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import mimetypes
import os
import asyncio
import aiofiles
from pathlib import Path

#for tests
import time

import datetime
from label_cog.src.logging_dotenv import setup_logger

from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)


def bytes_to_pil_image(img_bytes):
    img = Image.open(BytesIO(img_bytes))
    return img


def pil_to_BytesIO(img):
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io


async def open_image_aio(image_path): # todo maybe unused
    async with aiofiles.open(image_path, 'rb') as f:
        img_data = await f.read()
    img = Image.open(BytesIO(img_data))
    return img


def pdf_to_pil_img(raw_pdf):
    doc = fitz.open(stream=raw_pdf, filetype="pdf")  # we are using pymupdf because it is easier to install than pdf2image(poppler)
    page = doc.load_page(0)
    # get the pixmap of the page at 600 dpi
    pix = page.get_pixmap(alpha=False, dpi=600)  # todo does 600 instead of 300 work better ?
    img = pix.pil_image()
    doc.close()
    return img


def add_margins(img, margins_mm=(0, 0, 0, 0), dpi=300, color='white'):
    """
    Add margins to an image
    :param margins_mm:
    :param dpi:
    :param img: PIL image
    :param margins: tuple of margins in pixels (top, right, bottom, left)
    :return: PIL image with margins
    """
    # Convert mm to pixels
    margins = tuple(int((margin_mm / 25.4) * dpi) for margin_mm in margins_mm)
    if len(margins) != 4:
        raise ValueError("Margins must be a tuple of 4 integers")
    img_margins = ImageOps.expand(img, border=margins, fill=color)
    return img_margins


def convert_to_grayscale(img):
    img = ImageOps.grayscale(img)
    return img


def invert_image(img):
    img = ImageOps.invert(img)
    return img


def mirror_image(img):
    img = ImageOps.mirror(img)
    return img


def get_mime_type(img_name): # todo maybe unused
    mime_type, _ = mimetypes.guess_type(img_name)
    if mime_type is None:
        raise ValueError(f"Cannot determine MIME type for file: {img_name}")
    return mime_type


def convert_pil_to_base64_image(img):
    try:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        raise Exception(f"Error while converting image to base64: {e}")


def load_pil_font(font_size):
    # Load a font (Ensure the font file is accessible)
    # if dev get fonts from macos and if prod fonts from linux
    if os.getenv("ENV") == "dev":  # macos
        font_path = os.path.join(Path.home(), "Library", "Fonts", "DejaVuSans.ttf")  # the dev needs to install the font
    elif os.getenv("ENV") == "prod":  # linux
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    else:
        raise ValueError("ENV is not defined")

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")

    font = ImageFont.truetype(font_path, int(font_size))
    return font


def get_pil_font_size(font, text):
    left, top, right, bottom = font.getbbox(text)
    text_width = int(right)
    text_height = int(bottom)
    logger.debug(f"Text size: {text_width}x{text_height}")
    return text_width, text_height


def add_text_to_image(img, text, position, font_size): # todo maybe unused
    font = load_pil_font(font_size)
    draw = ImageDraw.Draw(img)
    draw.text(position, text, font=font, fill='black')
    return img


def add_text_in_middle_of_image(img, text, font_size):
    offset_y = 10 # to make the text a bit higher so that is in the middle of the image when written in lower case
    font = load_pil_font(font_size)
    text_width, text_height = get_pil_font_size(font, text)
    position = ((img.width - text_width) // 2, (img.height - text_height) // 2)
    position = (position[0], position[1] - offset_y)
    draw = ImageDraw.Draw(img)
    draw.text(position, text, font=font, fill='black')
    return img


def create_image_with_text(text, font_size, background_color='white'):
    font = load_pil_font(font_size)
    text_width, text_height = get_pil_font_size(font, text)
    # Create the background image
    img = Image.new('RGBA', (text_width, text_height), color=background_color)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, font=font, fill='black')
    logger.debug(f"Created create_image_with_text with dimensions: {text_width}x{text_height}")
    return img


def join_images_vertically(img1, img2, padding_between=0):
    # Create a new image with the height of both images and the width of the wider one
    new_width = max(img1.width, img2.width)
    new_height = img1.height + img2.height + padding_between
    new_img = Image.new('RGBA', (new_width, new_height), color='white')
    # Paste the images into the new image centered horizontally
    img1_x = (new_width - img1.width) // 2
    img1_y = 0
    img2_x = (new_width - img2.width) // 2
    img2_y = img1.height + padding_between
    new_img.paste(img1, (img1_x, img1_y))
    new_img.paste(img2, (img2_x, img2_y))
    return new_img

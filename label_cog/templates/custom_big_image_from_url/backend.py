import base64
import requests
from io import BytesIO
from PIL import Image
import mimetypes
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)

Image.MAX_IMAGE_PIXELS = None  # Increase pixel limit for the PIL dependency (8K)


# Convert an image to a Base64-encoded string with MIME prefix
# Guess the MIME type based on the file extension
def get_base64_image(img, mime_type):
    try:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:{mime_type};base64,{img_str}"
    except Exception as e:
        raise Exception(f"Error while converting image to base64: {e}")


def get_image_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        img = Image.open(BytesIO(response.content))
        img.verify()  # Verify that it is, indeed, an image
        return img
    except requests.exceptions.RequestException as req_err:
        raise Exception(f"Error while getting image from URL: {req_err}")
    except (IOError, SyntaxError) as img_err:
        raise Exception(f"Error while getting image from URL: {img_err}")


def get_mime_type(url):
    mime_type, _ = mimetypes.guess_type(url)
    if mime_type is None:
        raise ValueError(f"Cannot determine MIME type for file: {url}")
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
    image_url = data.get("image_url", "")
    try:
        img = get_image_from_url(image_url)
        height, width = get_maximum_size_for_paper(img.size)
        mime_type = get_mime_type(image_url)
        img_base64 = get_base64_image(img, mime_type)

    except Exception as e:
        raise Exception(f"Error while processing backend data of custom_big_image: {e}")
    new_data = {
        "img_base64": img_base64,
        "img_height": height,
        "img_width": width
    }
    return new_data


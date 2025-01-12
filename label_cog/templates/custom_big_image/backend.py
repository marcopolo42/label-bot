import base64
import requests
from io import BytesIO
from PIL import Image
import mimetypes
import os

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


def get_image_from_cache(image_name):
    path = os.path.join(os.getcwd(), "label_cog", "cache", image_name)
    img = Image.open(path)
    return img


def get_mime_type(url):
    mime_type, _ = mimetypes.guess_type(url)
    if mime_type is None:
        raise ValueError(f"Cannot determine MIME type for file: {url}")
    return mime_type


def get_maximum_size_for_paper(size):
    smaller_side = 62
    width, height = size
    print(f"Original size: {width}x{height}")
    if height < width:
        aspect_ratio = height / width
        print(f"Aspect ratio: {aspect_ratio}")
        width = smaller_side / aspect_ratio
        height = smaller_side
    else:
        aspect_ratio = width / height
        print(f"Aspect ratio: {aspect_ratio}")
        height = smaller_side / aspect_ratio
        width = smaller_side
    # round to no decimal places
    width = round(width)
    height = round(height)
    print(f"Page size in width: {width}mm and height: {height}mm")
    return height, width


def process_data(data):
    print("Data received in backend")
    print(data)
    image_name = data.get("image_name", "")
    img = get_image_from_cache(image_name)
    height, width = get_maximum_size_for_paper(img.size)
    mime_type = get_mime_type(image_name)
    img_base64 = get_base64_image(img, mime_type)
    new_data = {
        "img_base64": img_base64,
        "img_height": height,
        "img_width": width
    }
    return new_data


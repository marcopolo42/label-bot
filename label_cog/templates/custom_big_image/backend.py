import base64
import requests
from io import BytesIO
from PIL import Image
import mimetypes
import os


import asyncio
import aiofiles
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#for tests
import time

import datetime

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




class FileWaitHandler(FileSystemEventHandler):
    def __init__(self, substring, folder, event_loop):
        self.substring = substring
        self.folder = folder
        self.event_loop = event_loop
        self.event = asyncio.Event()
        self.found_file = None

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if self.substring in file_path.name:
            self.found_file = file_path.resolve()
            self.event.set()


async def wait_for_file(folder, substring):
    """Waits for a file containing 'substring' in its name to appear in 'folder'. Returns absolute path."""
    loop = asyncio.get_event_loop()
    event_handler = FileWaitHandler(substring, folder, loop)
    observer = Observer()
    observer.schedule(event_handler, folder, recursive=False)
    observer.start()
    try:
        print(f"Waiting for a file from the user '{substring}' in {folder}...")
        await asyncio.wait_for(event_handler.event.wait(), timeout=300)  # Wait for up to 5 minutes (300 seconds)
        if event_handler.found_file:
            return str(event_handler.found_file)
        else:
            raise None
    except asyncio.TimeoutError:
        print(f"Timeout while waiting for a file from the user '{substring}' in {folder}")
        return None
    finally:
        observer.stop()
        observer.join()


async def process_data(data):
    print("Data received in backend")
    print(data)
    user_id = data.get("user_id", "")

    img_path = await wait_for_file(CACHE_FOLDER, user_id)
    print(f"File found: {img_path}")
    if img_path is None: # Timeout of 5 minutes
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


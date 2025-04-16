import base64
import requests
from io import BytesIO
from PIL import Image
import mimetypes
import os
import random
from label_cog.src.image_utils import convert_pil_to_base64_image
import aiohttp

import asyncio
import aiofiles
from pathlib import Path

import datetime
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


async def save_img_from_url(url):
    async with aiohttp.ClientSession(headers={"Connection": "keep-alive"}) as session: # todo check if keep-alive is needed
        async with session.get(url) as r:
            if r.status != 200:
                logger.error(f"Error fetching file: {r.status}")
                return None
            file_bytes = await r.read()
            img = Image.open(BytesIO(file_bytes))
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


def get_img_base64_with_size(img):
    if img is None:
        return {}
    height, width = get_maximum_size_for_paper(img.size)
    img_base64 = convert_pil_to_base64_image(img)
    new_data = {
        "img_base64": img_base64,
        "img_height": height,
        "img_width": width
    }
    return new_data


'''
example response from the API:d
{
  "count": 2,
  "memes": [
    {
      "postLink": "https://redd.it/ji1riw",
      "subreddit": "wholesomememes",
      "title": "It makes me feel good.",
      "url": "https://i.redd.it/xuzd77yl8bv51.png",
      "nsfw": false,
      "spoiler": falsytf    
      "author": "polyesterairpods",
      "ups": 306,
      "preview": [
        "https://preview.redd.it/xuzd77yl8bv51.png?width=108&crop=smart&auto=webp&s=9a0376741fbda988ceeb7d96fdec3982f102313e",
        "https://preview.redd.it/xuzd77yl8bv51.png?width=216&crop=smart&auto=webp&s=ee2f287bf3f215da9c1cd88c865692b91512476d",
        "https://preview.redd.it/xuzd77yl8bv51.png?width=320&crop=smart&auto=webp&s=88850d9155d51f568fdb0ad527c94d556cd8bd70",
        "https://preview.redd.it/xuzd77yl8bv51.png?width=640&crop=smart&auto=webp&s=b7418b023b2f09cdc189a55ff1c57d531028bc3e"
      ]
    },
    {
      "postLink": "https://redd.it/jibifc",
      "subreddit": "wholesomememes",
      "title": "It really feels like that",
      "url": "https://i.redd.it/vvpbl29prev51.jpg",
      "nsfw": false,
      "spoiler": false,
      "author": "lolthebest",
      "ups": 188,
      "preview": [
        "https://preview.redd.it/vvpbl29prev51.jpg?width=108&crop=smart&auto=webp&s=cf64f01dfaca5f41c2e87651e4b0e321e28fa47c",
        "https://preview.redd.it/vvpbl29prev51.jpg?width=216&crop=smart&auto=webp&s=33acdf7ed7d943e1438039aa71fe9295ee2ff5a0",
        "https://preview.redd.it/vvpbl29prev51.jpg?width=320&crop=smart&auto=webp&s=6a0497b998bd9364cdb97876aa54c147089270da",
        "https://preview.redd.it/vvpbl29prev51.jpg?width=640&crop=smart&auto=webp&s=e68fbe686e92acb5977bcfc24dd57febd552afaf",
        "https://preview.redd.it/vvpbl29prev51.jpg?width=960&crop=smart&auto=webp&s=1ba690cfe8d49480fdd55c6daee6f2692e9292e7",
        "https://preview.redd.it/vvpbl29prev51.jpg?width=1080&crop=smart&auto=webp&s=44852004dba921a17ee4ade108980baab242805e"
      ]
    }
  ]
}
'''


def meme_api_call(endpoint, count):
    try:
        # Make a GET request to the API for many memes
        response = requests.get(f"{endpoint}/{count}")
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        # Parse the response as JSON
        data = response.json()

        return data

    except requests.exceptions.RequestException as e:
        logger.debug(f"Error fetching data from API: {e}")
        return None
    except ValueError as e:
        # Handle missing or malformed data errors
        return None


def fetch_one_meme(subreddit=None, blacklisted_words=None, pool=1):
    if subreddit is None:
        api_endpoint = f"https://meme-api.com/gimme"
    else:
        api_endpoint = f"https://meme-api.com/gimme/{subreddit}"

    data = meme_api_call(api_endpoint, pool)
    if data is None:
        return None
    logger.debug("All meme titles:")
    for meme in data["memes"]:
        logger.debug(meme["title"])

    # make a list of all the memes without the blacklisted words
    if blacklisted_words is not None:
        for meme in data["memes"]:
            if any(word in meme["title"].lower() for word in blacklisted_words):
                data["memes"].remove(meme)

    return random.choice(data["memes"])["url"]

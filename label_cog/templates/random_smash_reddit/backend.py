import requests
import random
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)

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


def api_call(endpoint, count):
    try:
        # Make a GET request to the API for many memes
        response = requests.get(f"{endpoint}/{count}")
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        # Parse the response as JSON
        data = response.json()

        # Return the meme URL to be used in the template
        return data

    except requests.exceptions.RequestException as e:
        # Handle request errors
        return None
    except ValueError as e:
        # Handle missing or malformed data errors
        return None


def fetch_meme():
    api_endpoint = "https://meme-api.com/gimme/SmashBrosUltimate"
    blacklisted_words = ["roster", "list", "tier"]
    count = 50

    data = api_call(api_endpoint, count)
    logger.debug("All meme titles:")
    for meme in data["memes"]:
        logger.debug(meme["title"])

    if data is None:
        return None
    # random out of count memes and check if it has blacklisted words if it has delete the meme the continue the loop
    for i in range(count):
        meme = random.choice(data["memes"])
        logger.debug("Random Meme:")
        logger.debug(meme["title"])
        if any(word in meme["title"].lower() for word in blacklisted_words):
            data["memes"].remove(meme)
            continue
        return meme["url"]
    return None


# Example usage:
async def process_data(data):
    meme_url = fetch_meme()
    if meme_url:
        logger.debug(f"Meme URL: {meme_url}")
        return {"meme_url": meme_url}
    else:
        logger.debug("Failed to fetch meme")
        return None


import os.path
import aiohttp
import aiofiles
from label_cog.src.view_utils import get_embed

import label_cog.src.global_vars as global_vars
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


def get_folder_size(folder):
    total_size = 0
    for dir_path, dir_names, file_names in os.walk(folder):
        for f in file_names:
            fp = os.path.join(dir_path, f)
            total_size += os.path.getsize(fp)
    return total_size


def folder_is_full(folder, size_gb):
    folder_size = get_folder_size(folder)
    if folder_size > size_gb * 1024 * 1024 * 1024: # Convert GB to bytes
        return True
    else:
        return False


def get_file_name_and_url(message):
    try:
        url = message.attachments[0].url
        name = message.attachments[0].filename
    except IndexError:
        return None, None
    else:
        return name, url


async def save_file_uploaded(message, folder, lang):
    logger.debug(f"Message: {message}")
    name, url = get_file_name_and_url(message)
    if name is None or url is None:
        await message.channel.send(embed=get_embed("no_file_attached", lang))
        return
    if not url.startswith("https://cdn.discordapp.com"):
        logger.error("Error: Invalid URL")
        await message.channel.send(embed=get_embed("error", lang))
        return
    async with aiohttp.ClientSession(headers={"Connection": "keep-alive"}) as session: # todo check if keep-alive is needed
        async with session.get(url) as r:
            if r.status != 200:
                logger.error(f"Error fetching file: {r.status}")
                await message.channel.send(embed=get_embed("error", lang))
                return
            # Read file directly into bytes
            file_bytes = await r.read()

            await message.channel.send(embed=get_embed("file_saved", lang))
            await message.channel.send(global_vars.channel_link.pop(message.author.id, "Error: You did not start creating a label before sending the file."))

            # Set the result to contain both the bytes and the filename
            future = global_vars.file_uploads_futures.pop(message.author.id)
            future.set_result(file_bytes)
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
    if folder_is_full(folder, 10):
        logger.error("Error: Drive is full")
        await message.channel.send(embed=get_embed("drive_full", lang))
        return
    if not url.startswith("https://cdn.discordapp.com"):
        logger.error("Error: Invalid URL")
        await message.channel.send(embed=get_embed("error", lang))
        return
    async with aiohttp.ClientSession(headers={"Connection": "keep-alive"}) as session: # todo check if keep-alive is needed
        async with session.get(url) as r:
            name = f"{message.author.id}_{name}"
            file_path = os.path.join(folder, name)
            try:
                async with aiofiles.open(file_path, 'wb') as out_file:
                    async for chunk in r.content.iter_chunked(8192):
                        await out_file.write(chunk)
                logger.info(f"Success: File saved as {name}")
                await message.channel.send(embed=get_embed("file_saved", lang))
                logger.debug(f"File uploads futures 3: {global_vars.file_uploads_futures}")
                await message.channel.send(global_vars.channel_link.pop(message.author.id, "Error: You did not start creating a label before sending the file."))
                #sets the result of the file future with the file path
                logger.debug(f"Message author ID: {message.author.id}")
                future = global_vars.file_uploads_futures.pop(message.author.id)
                future.set_result(file_path) # this sends the file path to the coroutine that is waiting for it.

                logger.debug(f"Jump URLs: {global_vars.channel_link}")
            except OSError as e:
                if e.errno == 28:  # Error number for "No space left on device"
                    logger.error("Error: Drive is full")
                    await message.channel.send(embed=get_embed("drive_full", lang))
                else:
                    logger.error(f"Error: {e}")
                    await message.channel.send(embed=get_embed("error", lang))
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise e
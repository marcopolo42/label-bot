import os.path
import aiohttp
from label_cog.src.discord_utils import get_embed


async def save_file_uploaded(message, folder, lang):
    print(f"Message: {message}")
    try:
        url = message.attachments[0].url
        name = message.attachments[0].filename
    except IndexError:
        print("Error: No attachments")
        await message.channel.send(embed=get_embed("no_attachments", lang))
    else:
        if url.startswith("https://cdn.discordapp.com"):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    name = f"{message.author.id}_{name}"
                    with open(os.path.join(folder, name), 'wb') as out_file:
                        while True:
                            chunk = await r.content.read(8192)
                            if not chunk:
                                break
                            out_file.write(chunk)
                    print('Image saved')
                    await message.channel.send(embed=get_embed("file_saved", lang))
                    await message.channel.send(name)
        else:
            print("Error: Invalid URL")

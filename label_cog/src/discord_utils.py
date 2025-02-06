import discord
import os

from label_cog.src.config import Config
from label_cog.src.db import get_user_language
from label_cog.src.utils import get_lang


def set_current_value_as_default(select, key):
    for i in select.options:
        if i.value == key:
            i.default = True
        else:
            i.default = False


def get_embed(key, lang, image=None):
    display_messages = Config().get("display_messages")
    if display_messages is None:
        raise ValueError("Display messages are missing from the config file")
    message = display_messages.get(key)
    if message is None:
        message = display_messages.get("default")
    embed = discord.Embed(
        title=get_lang(message.get("title"), lang),
        description=get_lang(message.get("description"), lang),
        color=message.get("color")
    )
    if image is not None:
        embed.set_image(url=f"attachment://{os.path.basename(image)}")
    return embed


async def modify_message(key, lang, image=None, original_message=None, interaction=None, view=None):
    if view is None:
        image = None
    embed = get_embed(key, lang, image)
    if interaction is not None:
        if interaction.response.is_done():
            if image is not None:
                print(f"embed modified with image. \"{embed.title}\"")
                await interaction.edit_original_response(embed=embed, file=discord.File(image), view=view)
            else:
                print(f"embed modified without image. title: \"{embed.title}\"")
                await interaction.edit_original_response(embed=embed, files=[], attachments=[], view=view)
        else:
            if image is not None:
                print(f"embed responded with image. text: \"{embed.title}\"")
                await interaction.response.edit_message(embed=embed, file=discord.File(image), view=view)
            else:
                print(f"embed responded without image. text: {embed.title}")
                await interaction.response.edit_message(embed=embed, files=[], attachments=[], view=view)
    if original_message is not None:
        if view is None:
            await original_message.edit(embed=embed, files=[], attachments=[])
        else:
            await original_message.edit(embed=embed, files=[], attachments=[], view=view)


async def update_displayed_status(key, lang, image=None, interaction=None, original_message=None, view=None):
    display_messages = Config().get("display_messages")
    if display_messages is None:
        raise ValueError("Display messages are missing from the config file")
    message = display_messages.get(key)
    if message is None:
        message = display_messages.get("default")
    await modify_message(
        key=key,
        lang=lang,
        image=image,
        original_message=original_message,
        interaction=interaction,
        view=view
    )
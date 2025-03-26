import discord
import os

from label_cog.src.config import Config
from label_cog.src.database import get_user_language
from label_cog.src.utils import get_lang
from label_cog.src.utils import get_local_directory
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.coins_render import render_coins_image
from label_cog.src.database import get_user_coins
from label_cog.src.utils import get_cache_directory
from label_cog.src.image_utils import pil_to_BytesIO
logger = setup_logger(__name__)



def set_current_value_as_default(select, key):
    for i in select.options:
        if i.value == key:
            i.default = True
        else:
            i.default = False


def get_display_message(key):
    display_messages = Config().get("display_messages")
    if display_messages is None:
        raise ValueError("Display messages are missing from the config file")
    message = display_messages.get(key)
    if message is None:
        logger.warning(f"Message with key {key} not found in display_messages")
        message = display_messages.get("default")
    return message


def get_embed(key, lang, image=None, thumbnail=None):
    message = get_display_message(key)
    embed = discord.Embed(
        title=get_lang(message.get("title"), lang),
        description=get_lang(message.get("description"), lang),
        color=message.get("color")
    )
    if thumbnail is not None:
        embed.set_thumbnail(url=f"attachment://{os.path.basename(thumbnail)}")
    if image is not None:
        embed.set_image(url=f"attachment://preview.png")
    return embed


# This function is as ugly as shit we both know it and will not talk about it, thanks.
async def modify_message(key, lang, image=None, thumbnail=None, original_message=None, interaction=None, view=None):
    if view is None:
        image = None
    embed = get_embed(key, lang, image, thumbnail)
    if interaction is not None:
        if interaction.response.is_done():
            if image is not None:
                image = pil_to_BytesIO(image)
                logger.debug(f"embed modified with image. \"{embed.title}\"")
                await interaction.edit_original_response(embed=embed, files=[discord.File(image, filename="preview.png"), discord.File(thumbnail)], view=view)
            else:
                logger.debug(f"embed modified without image. title: \"{embed.title}\"")
                await interaction.edit_original_response(embed=embed, files=[], attachments=[], view=view)
        else:
            if image is not None:
                image = pil_to_BytesIO(image)
                logger.debug(f"embed responded with image. text: \"{embed.title}\"")
                await interaction.response.edit_message(embed=embed, files=[discord.File(image, filename="preview.png"), discord.File(thumbnail)], view=view)
            else:
                logger.debug(f"embed responded without image. text: {embed.title}")
                await interaction.response.edit_message(embed=embed, files=[], attachments=[], view=view)
    if original_message is not None:
        if view is None:
            await original_message.edit(embed=embed, files=[], attachments=[])
        else:
            await original_message.edit(embed=embed, files=[], attachments=[], view=view)


async def update_displayed_status(key, lang, image=None, interaction=None, original_message=None, view=None):
    if image is None:
        thumbnail = None
    else:
        img_coin = render_coins_image(await get_user_coins(interaction.user))
        thumbnail = get_cache_directory("coin.png")
        img_coin.save(thumbnail)
    await modify_message(
        key=key,
        lang=lang,
        image=image,
        thumbnail=thumbnail,
        original_message=original_message,
        interaction=interaction,
        view=view
    )


async def display_and_stop(view, interaction, status):
    view.disable_all_items()
    await update_displayed_status(str(status), view.lang, interaction=interaction, view=view)
    view.stop()


def create_option(template, lang):
    return discord.SelectOption(
        label=get_lang(template.get("name"), lang),
        value=template.get("key"),
        description=get_lang(template.get("description"), lang),
        emoji=template.get("emoji")
    )


def get_templates_options(roles_names_lower, lang):
    templates = Config().get("templates")
    options = []
    for template in templates:
        allowed_roles = template.get("allowed_roles")
        for a_role in allowed_roles:
            if a_role.lower() in roles_names_lower:
                options.append(create_option(template, lang))
                break
    if len(options) == 0:
        options.append(discord.SelectOption(
            label="No templates available",
            value="no_templates",
            description="You don't have access to any templates",
        ))
    return options


def get_templates_values():
    templates = Config().get("templates")
    logger.debug(f"Templates: {templates}")
    values = []
    for template in templates:
        logger.debug(f"Template: {template}")
        values.append(template.get("key"))
    if len(values) == 0:
        values.append("no_templates_available")
    return values


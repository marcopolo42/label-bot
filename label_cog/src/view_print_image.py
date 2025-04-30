import discord

from label_cog.src.view_utils import set_current_value_as_default, update_displayed_status

from label_cog.src.template import Template, TemplateException

from label_cog.src.database import update_user_language, get_user_language, add_log

from label_cog.src.printer import ql_brother_print_usb

from label_cog.src.modals import CustomLabelModal

from label_cog.src.config import Config

from label_cog.src.utils import get_translation, get_lang

from label_cog.src.view_utils import get_embed, display_and_stop, get_templates_options

from label_cog.src.printer import print_label
from label_cog.src.label import Label
from label_cog.src.view_utils import get_select_count_options

import asyncio

import os

import label_cog.src.global_vars as global_vars
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)




class PrintImageView(discord.ui.View):
    def __init__(self, count_options, label, session, file):
        super().__init__(timeout=800)  # 13 minutes timeout
        self.author = session.author
        self.roles = session.roles
        self.lang = session.lang
        self.label = label
        self.file = file

        self.select_count = discord.ui.Select(
            row=2,
            placeholder=get_translation("select_count_placeholder", self.lang),
            custom_id="LabelCountSelect",
            options=count_options,
        )
        self.select_count.callback = self.select_count_callback

        self.print_button = discord.ui.Button(
            row=3,
            label=get_translation("print_button_label", self.lang),
            custom_id="PrintBtn",
            style=discord.ButtonStyle.green,
            emoji="🖨️",
        )
        self.print_button.callback = self.print_button_callback

        self.cancel_button = discord.ui.Button(
            row=3,
            label=get_translation("cancel_button_label", self.lang),
            style=discord.ButtonStyle.secondary,
            emoji="🚫",
        )
        self.cancel_button.callback = self.cancel_button_callback

        self.help_button = discord.ui.Button(
            row=3,
            label=get_translation("help_button_label", self.lang),
            style=discord.ButtonStyle.blurple,
            emoji="📖",
        )
        self.help_button.callback = self.help_button_callback

        #add items to the view
        self.add_item(self.select_count)
        self.add_item(self.print_button)
        self.add_item(self.cancel_button)
        self.add_item(self.help_button)

    #ideally this would be in the __init__ but we need to use async methods
    @classmethod
    async def create(cls, file, session):
        label = Label()
        # load the template information of type "custom_image"
        label.template.load("custom_image", session.author, session.lang)
        # add the image to the template available data
        label.template.data["img_bytes"] = await file.read()
        await label.make()
        options = await get_select_count_options(label.template, session.author)
        label.count = int(options[0].value)
        return cls(count_options=options, label=label, session=session, file=file)

    async def select_count_callback(self, interaction):
        self.label.count = int(self.select_count.values[0])
        set_current_value_as_default(self.select_count, self.select_count.values[0])
        await interaction.response.defer()

    async def print_button_callback(self, interaction):
        await update_displayed_status("printing", self.lang, interaction=interaction, view=self)
        status = await print_label(self.label, self.author)
        await display_and_stop(self, interaction, status)

    async def cancel_button_callback(self, interaction):
        await display_and_stop(self, interaction, "canceled")

    async def help_button_callback(self, interaction):
        await update_displayed_status("help", self.lang, interaction=interaction, view=self)

    async def on_timeout(self):
        logger.info("Timeout of ChooseLabelView")
        self.disable_all_items()
        await update_displayed_status("timeout", self.lang, original_message=self.parent, view=self)
        self.stop()

    async def update_select_count_options(self):
        self.select_count.options = await get_select_count_options(self.label.template, self.author)
        self.label.count = int(self.select_count.options[0].value)





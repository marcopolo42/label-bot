
import discord
from label_cog.src.config import Config
from label_cog.src.view_utils import update_displayed_status
from label_cog.src.db import update_user_language
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)

class ChangeLanguageView(discord.ui.View):
    def __init__(self, session):
        super().__init__(disable_on_timeout=True, timeout=300)  # 5 minutes timeout
        self.author = session.author
        self.lang = session.lang

        # get the language options from the configuration file
        languages = Config().get("languages")
        if languages is None:
            raise ValueError("Languages are missing from the config file")
        options = []
        for language in languages:
            options.append(discord.SelectOption(
                label=language.get("name"),
                value=language.get("key"),
                emoji=language.get("emoji")
            ))
            if language.get("key") == session.lang:
                options[-1].default = True
        self.language_select = discord.ui.Select(
            options=options
        )
        self.language_select.callback = self.language_select_callback
        self.add_item(self.language_select)

    #todo set the current discord language as default
    async def language_select_callback(self, interaction):
        value = self.language_select.values[0]
        await update_user_language(interaction.user, value)
        self.lang = value
        self.disable_all_items()
        await update_displayed_status("language_changed", self.lang, interaction=interaction, view=self)
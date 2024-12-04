import discord

from label_cog.src.discord_utils import set_current_value_as_default, change_displayed_status

from label_cog.src.template_class import Template

from label_cog.src.db_utils import update_user_language, get_user_language

from label_cog.src.modals import CustomLabelModal

from label_cog.src.config import Config

from label_cog.src.utils import get_translation, get_lang


class ChooseLabelView(discord.ui.View):
    def __init__(self, session, label):
        super().__init__(timeout=None)
        self.conn = session.conn
        self.author = session.author
        self.lang = session.lang
        self.label = label

        # Create the select and buttons
        self.select_type = discord.ui.Select(
            placeholder=get_translation("select_type_placeholder", self.lang),
            custom_id="LabelTypeSelect",
            options=self.get_select_type_options(self.author.roles),
        )
        self.select_type.callback = self.select_type_callback

        self.select_count = discord.ui.Select(
            placeholder=get_translation("select_count_placeholder", self.lang),
            custom_id="LabelCountSelect",
            options=[discord.SelectOption(label="0", value="0")],
            disabled=True,
        )
        self.select_count.callback = self.select_count_callback

        self.print_button = discord.ui.Button(
            label=get_translation("print_button_label", self.lang),
            custom_id="PrintBtn",
            style=discord.ButtonStyle.green,
            emoji="🖨️",
        )
        self.print_button.callback = self.print_button_callback

        self.cancel_button = discord.ui.Button(
            label=get_translation("cancel_button_label", self.lang),
            style=discord.ButtonStyle.secondary,
            emoji="🚫",
        )
        self.cancel_button.callback = self.cancel_button_callback

        self.help_button = discord.ui.Button(
            label=get_translation("help_button_label", self.lang),
            style=discord.ButtonStyle.blurple,
            emoji="📖",
        )
        self.help_button.callback = self.help_button_callback

        self.reload_button = discord.ui.Button(
            label="Reload",
            style=discord.ButtonStyle.secondary,
            emoji="🔄",
        )
        self.reload_button.callback = self.select_type_callback

        #add items to the view
        self.add_item(self.select_type)
        self.add_item(self.select_count)
        self.add_item(self.print_button)
        self.add_item(self.cancel_button)
        self.add_item(self.help_button)

    async def select_type_callback(self, interaction):
        self.label.reset()
        self.label.template = Template(self.select_type.values[0], self.lang)
        set_current_value_as_default(self.select_type, self.select_type.values[0])
        await self.get_custom_label_fields(interaction, self.label)
        self.update_reload_button(self.label.template)
        await self.update_select_count_options(interaction)
        await self.update_view(interaction)

    async def select_count_callback(self, interaction):
        self.label.count = int(self.select_count.values[0])
        set_current_value_as_default(self.select_count, self.select_count.values[0])
        await interaction.response.defer()

    async def print_button_callback(self, interaction):
        self.label.validated = True
        await self.close(interaction)

    async def cancel_button_callback(self, interaction):
        self.label.reset()
        await self.close(interaction)

    async def help_button_callback(self, interaction):
        await change_displayed_status("help", self.lang, interaction=interaction, view=self)

    async def on_timeout(self):
        self.label.clear()

    # Close the view and disable all items
    async def close(self, interaction=None):
        self.disable_all_items()
        if interaction is not None:
            if interaction.response.is_done():
                await interaction.edit_original_message(view=self)
            else:
                await interaction.response.edit_message(view=self)
        else:
            if not self._message or self._message.flags.ephemeral:
                message = self.parent
            else:
                message = self.message

            if message:
                m = await message.edit(view=self)
                if m:
                    self._message = m
        self.stop()

    def update_reload_button(self, template):
        if template.settings is None:
            value = None
        else:
            value = template.settings.get("reload_button")
        if value:
            if self.reload_button not in self.children:
                self.add_item(self.reload_button)
        else:
            self.remove_item(self.reload_button)


    async def get_custom_label_fields(self, interaction, label):
        if label.template.fields is None:
            return None
        modal = CustomLabelModal(label, self.lang)
        await interaction.response.send_modal(modal)
        # disable the print button and select count so the user can't click on if they decide to not fill the fields.
        self.print_button.disabled = True
        self.select_count.disabled = True
        # I wanted to change the status before the modal is sent, but it seems that I can't send the modal only as a direct response to the interaction.
        await change_displayed_status("waiting_fields", self.lang, interaction=interaction, view=self)
        await modal.wait()
        return None

    def is_bocal_role(self, user_roles):
        bocal_roles = [role.lower() for role in Config().get("bocal_roles")]
        return any(role in [role.name.lower() for role in user_roles] for role in bocal_roles)

    def get_select_type_options(self, user_roles):
        templates = Config().get("templates")
        roles = [role.name.lower() for role in user_roles]
        if self.is_bocal_role(user_roles):
            print("User has a bocal role")
            roles.append("bocal")
        options = []
        for template in templates:
            for a_role in template.get("allowed_roles"):
                if str(a_role).lower() in roles:
                    options.append(discord.SelectOption(
                        label=get_lang(template.get("name"), self.lang),
                        value=template.get("key"),
                        description=get_lang(template.get("description"), self.lang),
                        emoji=template.get("emoji")
                    ))
                    break
        return options

    async def update_select_count_options(self, interaction):
        available_prints = self.label.template.prints_available_today(self.author, self.conn)
        if available_prints == 0:
            self.select_count.options = [discord.SelectOption(label="0", value="0")]
        else:
            self.select_count.options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(1, available_prints + 1)]
        self.label.count = int(self.select_count.options[0].value)
        self.select_count.options[0].default = True

    def are_custom_fields_filled(self):
        if self.label.template is None or self.label.template.fields is None:
            return True
        for field in self.label.template.fields:
            if self.label.data.get(field.get("key")) is None:
                return False
        return True

    async def update_view(self, interaction):
        self.select_count.disabled = True
        self.print_button.disabled = True
        if self.label.count < 1:
            await change_displayed_status("daily_limit_reached", self.lang, interaction=interaction, view=self)
            return
        if not self.are_custom_fields_filled():
            await change_displayed_status("missing_fields", self.lang, interaction=interaction, view=self)
            return
        print("Creating the label embed ...")
        await change_displayed_status("creating", self.lang, interaction=interaction, view=self)
        print("label.make() ...")
        self.label.make()
        self.select_count.disabled = False
        self.print_button.disabled = False
        await change_displayed_status("preview", self.lang, image=self.label.preview, interaction=interaction, view=self)


class ChangeLanguageView(discord.ui.View):
    def __init__(self, session):
        super().__init__(disable_on_timeout=True, timeout=300)  # 5 minutes timeout
        self.conn = session.conn
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
            if language.get("key") == get_user_language(self.author, self.conn):
                options[-1].default = True
        self.language_select = discord.ui.Select(
            options=options
        )
        self.language_select.callback = self.language_select_callback
        self.add_item(self.language_select)

    #todo set the current language as default
    async def language_select_callback(self, interaction):
        value = self.language_select.values[0]
        update_user_language(interaction.user, value, self.conn)
        self.lang = value
        self.disable_all_items()
        await change_displayed_status("language_changed", self.lang, interaction=interaction, view=self)
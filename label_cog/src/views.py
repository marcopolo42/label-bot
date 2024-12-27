import discord

from label_cog.src.discord_utils import set_current_value_as_default, update_displayed_status

from label_cog.src.template_class import Template, TemplateException

from label_cog.src.db_utils import update_user_language, get_user_language, add_log

from label_cog.src.printer_utils import ql_brother_print_usb

from label_cog.src.modals import CustomLabelModal

from label_cog.src.config import Config

from label_cog.src.utils import get_translation, get_lang


class ChooseLabelView(discord.ui.View):
    def __init__(self, session, label):
        super().__init__(timeout=800)  # 13 minutes timeout
        self.conn = session.conn
        self.author = session.author
        self.roles = session.roles
        self.lang = session.lang
        self.label = label
        # we cannot display more than 25 options in a select, so we need to split the options in multiple pages
        self.options = self.load_templates_options()
        self.option_pages_count = self.count_of_option_pages()

        # Create the select and buttons
        self.select_type = discord.ui.Select(
            row=0,
            placeholder=get_translation("select_type_placeholder", self.lang),
            custom_id="LabelTypeSelect",
            options=self.get_options_page(0),
        )
        self.select_type.callback = self.select_type_callback

        self.previous_button = discord.ui.Button(
            row=1,
            label=None,
            style=discord.ButtonStyle.secondary,
            emoji="⬅️",
        )
        self.previous_button.callback = self.previous_button_callback

        self.next_button = discord.ui.Button(
            row=1,
            label=None,
            style=discord.ButtonStyle.secondary,
            emoji="➡️",
        )
        self.next_button.callback = self.next_button_callback

        self.select_count = discord.ui.Select(
            row=2,
            placeholder=get_translation("select_count_placeholder", self.lang),
            custom_id="LabelCountSelect",
            options=[discord.SelectOption(label="0", value="0")],
            disabled=True,
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

        self.reload_button = discord.ui.Button(
            row=3,
            label="Reload",
            style=discord.ButtonStyle.secondary,
            emoji="🔄",
        )
        self.reload_button.callback = self.select_type_callback

        #add items to the view
        self.add_item(self.select_type)
        if self.option_pages_count > 1:
            self.add_item(self.previous_button)
            self.add_item(self.next_button)
        self.add_item(self.select_count)
        self.add_item(self.print_button)
        self.add_item(self.cancel_button)
        self.add_item(self.help_button)

    async def select_type_callback(self, interaction):
        self.label.reset()
        try:
            self.label.template = Template(self.select_type.values[0], self.lang, self.author)
        except TemplateException as e:
            await self.display_and_stop(interaction, e)
        except Exception as e:
            raise e
        else:
            set_current_value_as_default(self.select_type, self.select_type.values[0])
            await self.ask_for_custom_label_fields(interaction, self.label)
            self.update_reload_button(self.label.template)
            await self.update_select_count_options(interaction)
            await self.update_view(interaction)

    async def previous_button_callback(self, interaction): # todo
        await interaction.response.defer()

    async def next_button_callback(self, interaction):
        await interaction.response.defer()

    async def select_count_callback(self, interaction):
        self.label.count = int(self.select_count.values[0])
        set_current_value_as_default(self.select_count, self.select_count.values[0])
        await interaction.response.defer()

    '''status = {
                'instructions_sent': True, # The instructions were sent to the printer.
                'outcome': 'unknown', # String description of the outcome of the sending operation like: 'unknown', 'sent', 'printed', 'error'
                'printer_state': None, # If the selected backend supports reading back the printer state, this key will contain it.
                'did_print': False, # If True, a print was produced. It defaults to False if the outcome is uncertain (due to a backend without read-back capability).
                'ready_for_next_job': False, # If True, the printer is ready to receive the next instructions. It defaults to False if the state is unknown.
            }
            '''
    async def print_button_callback(self, interaction):
        await update_displayed_status("printing", self.lang, interaction=interaction, view=self)
        label = self.label
        add_log(f"Label {label.template.key} {label.count} was printed", self.author, label, self.conn)
        print(f"You have chosen to print the label {label.template.key} {label.count} times.")

        try:
            status = ql_brother_print_usb(label.image, label.count)
        except Exception as e:
            print(f"\033[91mError while printing: {e}\033[0m")
            await self.display_and_stop(interaction, "error_print")
        else:
            outcome = status.get("outcome")
            if outcome == "error":
                await self.display_and_stop(interaction, "error_print")
                return
            elif outcome == "printed":
                await self.display_and_stop(interaction, "printed")
                return
            else:
                raise ValueError(f"Unexpected outcome: {outcome}")

    async def cancel_button_callback(self, interaction):
        self.label.clear_files()
        await self.display_and_stop(interaction, "canceled")

    async def help_button_callback(self, interaction):
        await update_displayed_status("help", self.lang, interaction=interaction, view=self)

    async def on_timeout(self):
        print("Timeout")
        self.label.clear_files()
        self.disable_all_items()
        await update_displayed_status("timeout", self.lang, original_message=self.parent, view=self)
        self.stop()



    async def display_and_stop(self, interaction, status):
        self.disable_all_items()
        await update_displayed_status(str(status), self.lang, interaction=interaction, view=self)
        self.stop()

    def update_reload_button(self, template):
        if template.settings is None:
            value = None
        else:
            value = template.settings.get("reload_button")
        if value is not None:
            if self.reload_button not in self.children:
                self.add_item(self.reload_button)
        else:
            self.remove_item(self.reload_button)


    async def ask_for_custom_label_fields(self, interaction, label):
        if label.template.fields is None:
            return None
        modal = CustomLabelModal(label, self.lang)
        await interaction.response.send_modal(modal)
        # disable the print button and select count so the user can't click on if they decide to not fill the fields.
        self.print_button.disabled = True
        self.select_count.disabled = True
        # I wanted to change the status before the modal is sent, but it seems that I can't send the modal only as a direct response to the interaction.
        await update_displayed_status("waiting_fields", self.lang, interaction=interaction, view=self)
        await modal.wait()
        return None

    def create_option(self, template):
        return discord.SelectOption(
            label=get_lang(template.get("name"), self.lang),
            value=template.get("key"),
            description=get_lang(template.get("description"), self.lang),
            emoji=template.get("emoji")
        )

    def load_templates_options(self):
        templates = Config().get("templates")
        options = []
        for template in templates:
            allowed_roles = template.get("allowed_roles")
            print(f"allowed_roles: {allowed_roles}")
            for a_role in allowed_roles:
                if a_role.lower() in self.roles.names_lower:
                    print(f"option added: {template.get('key')}")
                    options.append(self.create_option(template))
                    break
        if len(options) == 0:
            options.append(discord.SelectOption(
                label="No templates available",
                value="no_templates",
                description="You don't have access to any templates",
            ))
        return options

    def count_of_option_pages(self):
        return len(self.options) // 25

    def get_options_page(self, page):
        return self.options[25 * page: 25 * (page + 1)]

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
            await update_displayed_status("daily_limit_reached", self.lang, interaction=interaction, view=self)
            return
        if not self.are_custom_fields_filled():
            await update_displayed_status("missing_fields", self.lang, interaction=interaction, view=self)
            return
        print("Creating the label embed ...")
        await update_displayed_status("creating", self.lang, interaction=interaction, view=self)
        print("label.make() ...")
        self.label.make()
        self.select_count.disabled = False
        self.print_button.disabled = False
        await update_displayed_status("preview", self.lang, image=self.label.preview, interaction=interaction, view=self)


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

    #todo set the current discord language as default
    async def language_select_callback(self, interaction):
        value = self.language_select.values[0]
        update_user_language(interaction.user, value, self.conn)
        self.lang = value
        self.disable_all_items()
        await update_displayed_status("language_changed", self.lang, interaction=interaction, view=self)

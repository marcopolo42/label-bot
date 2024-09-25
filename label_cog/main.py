from cProfile import label

import discord
import yaml
from PIL import Image, ImageOps
from brother_ql.output_helpers import textual_description_discovered_devices
from discord.ext import commands
from datetime import datetime, timedelta
import sqlite3
import os
import dotenv
import fitz

from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster
from blabel import LabelWriter

# Load environment variables and configure PIL
dotenv.load_dotenv()
Image.MAX_IMAGE_PIXELS = 8294400  # Increase pixel limit for PIL (4K)


#Utility functions
def get_time(days_to_add=0):
    if days_to_add is None:
        days_to_add = 0
    time = datetime.now() + timedelta(days=days_to_add)
    return time.strftime("%d.%m.%Y %Hh")


def get_discord_url(id):
    if id is None:
        return None
    # return "https://profile.intra.42.fr/users/" + id
    return "https://discordapp.com/users/" + str(id)


#Image related functions
def convert_to_grayscale(image_path):
    image = Image.open(image_path)
    grayscale_image = ImageOps.grayscale(image)
    grayscale_image.save(image_path)


def pdf_to_image(pdf):
    doc = fitz.open(pdf)  # we are using pymupdf because it is easier to install than pdf2image(poppler)
    page = doc.load_page(0)
    # get the pixmap of the page at 600 dpi
    pix = page.get_pixmap(alpha=False, dpi=600)  # todo does 600 instead of 300 work better ?
    image_path = f"label_cog/images/{os.path.splitext(os.path.basename(pdf))[0]}.png"
    pix.save(image_path)
    doc.close()
    return image_path


def add_log(log, author, label, conn):
    cursor = conn.cursor()
    if label.template is None:
        cursor.execute("INSERT INTO logs (log, user_id, user_display_name, user_avatar) VALUES (?, ?, ?, ?)",
                       (log, author.id, author.display_name, author.avatar.url))
    else:
        cursor.execute(
            "INSERT INTO logs (log, user_id, user_display_name, user_avatar, template_key, label_count) VALUES (?, ?, ?, ?, ?, ?)",
            (log, author.id, author.display_name, author.avatar.url, label.template.key, label.count))
    conn.commit()


# count the number of label prints today using the user id and the label.count
def prints_count_today(author, template_key, conn):
    cursor = conn.cursor()
    # select the sum of label_count from logs where the user_id is the same as the author's id and the creation date is in the last 24 hours and the label_type is the same as the label_type
    cursor.execute(
        "SELECT SUM(label_count) FROM logs WHERE user_id = ? AND creation_date > datetime('now', '-1 day') AND template_key = ?", (author.id, template_key))
    count = cursor.fetchone()
    if count is None:
        return 0
    if count[0] is None:
        return 0
    return count[0]


def prints_available_today(author, template, conn):
    limit = template.get_daily_limit(author.roles)
    available = limit - prints_count_today(author, template.key, conn)
    if available < 0:
        return 0
    return available


def create_tables():
    conn = sqlite3.connect('label_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs
                      (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log TEXT,
                        user_id INTEGER, 
                        user_display_name TEXT,
                        user_avatar TEXT,
                        template_key TEXT, 
                        label_count INTEGER, 
                        creation_date TEXT DEFAULT CURRENT_TIMESTAMP
                      )''')
    # for future language and TIG feature support
    # cursor.execute('''CREATE TABLE IF NOT EXISTS users
    #                     (
    #                         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                         user_id INTEGER,
    #                         user_display_name TEXT,
    #                         user_avatar TEXT,
    #                         user_url TEXT,
    #                         creation_date TEXT DEFAULT CURRENT_TIMESTAMP
    #
    #                     )''')
    conn.commit()
    conn.close()


def display_logs(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs")
    rows = cursor.fetchall()
    logs = ""
    for row in rows:
        print(row)
        logs += row.__str__() + "\n"
    return logs


#Configuration file functions
def load_config():
    config_file = f"label_cog/config.yaml"
    config = yaml.safe_load(open(config_file))
    if config is None:
        raise ValueError("Configuration file is empty or invalid")
    return config


def ql_brother_print_usb(image, count=1):
    if image is None:
        return
    im = Image.open(image)
    #print images size
    print(im.size) #todo remove debug
    backend = 'pyusb'  # 'pyusb', 'linux_kernel', 'network'
    model = 'QL-710W'
    printer = 'usb://0x04f9:0x20c0/000D9Z773204'  # Get these values from the Windows usb driver filter.  Linux/Raspberry Pi uses '/dev/usb/lp0'. Macos use 'lsusb' from homebrew.
    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True #todo remove for production
    instructions = convert(

        qlr=qlr,
        images=[im],  # Takes a list of file names or PIL objects.
        label='62',
        rotate=('0' if im.size[0] > im.size[1] else '90'),  # 'Auto', '0', '90', '270'
        threshold=70.0,  # Black and white threshold in percent.
        dither=False,
        compress=False,
        red=False,  # Only True if using Red/Black 62 mm label tape.
        dpi_600=False,
        hq=True,  # False for low quality.
        cut=True

    )
    send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True)


class Template:
    def __init__(self, type):
        raw = self.load_template(type)
        self.key = raw.get("key")
        self.name = raw.get("name")
        self.description = raw.get("description")
        self.emoji = raw.get("emoji")
        
        self.settings = raw.get("settings")

        self.allowed_roles = raw.get("allowed_roles")

        self.daily_role_limits = raw.get("daily_role_limits")

        self.fields = raw.get("fields")

    def load_template(self, type):
        config = load_config()
        templates = config.get("templates")
        template = None
        for t in templates:
            if t["key"] == type:
                template = t
                break
        if template is None:
            raise ValueError(f"Template {type} not found in config file")
        return template

    def get_daily_limit(self, user_roles):
        if self.daily_role_limits is None:
            return 25
        limit = 0
        u_roles = [role.name.lower() for role in user_roles]
        a_roles = [role.lower() for role in self.allowed_roles]
        for role in u_roles:
            if role in a_roles:
                tmp = self.daily_role_limits.get(role)
                if tmp is None:
                    tmp = 25
                if limit < tmp:
                    limit = tmp
        return limit

    def display(self): #debug function
        print(f"Key: {self.key}")
        print(f"Name: {self.name}")
        print(f"Description: {self.description}")
        print(f"Emoji: {self.emoji}")
        print(f"Settings: {self.settings}")
        print(f"Allowed roles: {self.allowed_roles}")
        print(f"Daily role limits: {self.daily_role_limits}")
        print(f"Fields: {self.fields}")


class Label:
    def __init__(self, author):
        self.template = None
        self.count = 1
        self.validated = None
        # default information that is always available. More info can be added based on the template config
        self.data = dict(
            user_name=author.display_name,
            user_picture=author.avatar,
            user_url=get_discord_url(str(author.id)),
            creation_date=get_time()
        )
        #return files
        self.pdf = None
        self.image = None

    def make(self):
        # removes previous files
        if self.pdf is not None:
            os.remove(self.pdf)
        if self.image is not None:
            os.remove(self.image)
        if self.template is None:
            return
        if self.count < 1:
            return

        # the folder name of the template should be the same as the value
        directory = f"{os.getcwd()}/label_cog/templates/{self.template.key}"
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Template folder for {self.template.key} is missing")
        label_writer = LabelWriter(item_template_path=f"{directory}/template.html",
                                   default_stylesheets=(f"{directory}/style.css",)) # todo check if this works for images

        # Set the settings from the template to the data available for the label creation
        if self.template.settings:
            for key, value in self.template.settings.items():
                self.data.update({key: value})

        # Makes multiple copies of the label #todo will be removed in the future because we will print the images not the pdfs
        records = []
        for i in range(self.count):
            records.append(self.data)

        # Writes the labels to a PDF file with a unique file name using the author's ID and the current timestamp
        self.pdf = f"{os.getcwd()}/label_cog/pdfs/{self.data.get("user_name")}_{datetime.now().strftime('%d-%m-%Y-%Hh%Mm%Ss')}.pdfs"
        label_writer.write_labels(records, target=self.pdf)
        self.image = pdf_to_image(self.pdf)
        convert_to_grayscale(self.image)


    def clear(self):
        if self.pdf is not None and os.path.exists(self.pdf):
            os.remove(self.pdf)
            self.pdf = None
        if self.pdf is not None and os.path.exists(self.image):
            os.remove(self.image)
            self.image = None
        self.template = None
        self.count = 0
        self.validated = False


# Modal to ask for additional data using a modal form
async def ask_for_additional_data(interaction, label, view):
    if label.template.fields is None:
        return

    class MyModal(discord.ui.Modal):
        def __init__(self, label):
            super().__init__(title="What would you like on your label ?", timeout=300) #5 minutes timeout
            self.label = label
            fields = label.template.fields
            if len(fields) > 5:
                raise ValueError("Too many extra fields, the modal can only handle 5 fields")
            for f in fields:
                if f.get("max_length") > 20:
                    style = discord.InputTextStyle.long
                else:
                    style = discord.InputTextStyle.short
                # check if the field has already been filled before and add the old value back
                previous_value = label.data.get(f.get("key"))
                if previous_value is not None:
                    self.add_item(discord.ui.InputText(label=f.get("name"), max_length=f.get("max_length"), placeholder=f.get("placeholder"), style=style, value=previous_value))
                else:
                    self.add_item(discord.ui.InputText(label=f.get("name"), max_length=f.get("max_length"), placeholder=f.get("placeholder"), style=style))

        async def callback(self, interaction: discord.Interaction):
            for idx, item in enumerate(self.label.template.fields):
                self.label.data.update({item["key"]: self.children[idx].value})
            embed = discord.Embed(title="Creating the label !", description="please wait ...", color=0x53B7BA)
            await interaction.response.edit_message(embed=embed, files=[], view=view)

    modal = MyModal(label)
    if interaction.response.is_done():
        await interaction.followup.send_modal(modal)
    else:
        await interaction.response.send_modal(modal)
    await modal.wait()
    return None


async def update_preview(interaction, label, view):
    if label.count < 1:
        return
    # if the response is not done, we defer it, because the image may take some time to be generated.
    if not interaction.response.is_done():
        embed = discord.Embed(title="Creating the label !", description="please wait ...", color=0x53B7BA)
        # remove the discord file from the previous message
        await interaction.response.edit_message(embed=embed, files=[], view=view)
    label.make()
    if label.image is None:
        embed = discord.Embed(title="The label could not be generated", description="An error occurred while generating the label", color=0xff0000)
        await interaction.edit_original_response(embed=embed, view=view)
        return
    #debug
    #for key, value in label.data.items():
    #   embed.add_field(name=key, value=value)
    file = None
    if label.image is not None:
        file = discord.File(label.image)
    if file is None:
        embed = discord.Embed(title="The label could not be displayed", description="An error occurred while generating the label", color=0xff0000)
        await interaction.edit_original_response(embed=embed, view=view)
    else:
        embed = discord.Embed(title="Preview of your label", description="This is how your label will look like.", color=0x53B7BA)
        embed.set_image(url=f"attachment://{os.path.basename(label.image)}")
        #check embed image
        print(embed.image)
        await interaction.edit_original_response(embed=embed, file=file, view=view)


def get_select_type_options(user_roles):
    config = load_config()
    templates = config.get("templates")
    u_roles = [role.name.lower() for role in user_roles]
    options = []
    for template in templates:
        for a_role in template.get("allowed_roles"):
            if str(a_role).lower() in u_roles:
                options.append(discord.SelectOption(
                    label=template["name"],
                    value=template["key"],
                    description=template["description"],
                    emoji=template["emoji"]
                ))
                break
    return options



class ChooseLabelView(discord.ui.View):
    def __init__(self, ctx, label, conn):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.ctx = ctx
        self.label = label
        self.conn = conn

        # Create the select menu for label types dynamically using `ctx.author.roles`
        self.select_type = discord.ui.Select(
            placeholder="Choose your label...",
            custom_id="LabelTypeSelect",
            options=get_select_type_options(self.ctx.author.roles),
        )
        self.select_type.callback = self.select_type_callback

        # Create the select menu for label count (quantity)
        self.select_count = discord.ui.Select(
            placeholder="Choose how many...",
            custom_id="LabelCountSelect",
            options=[discord.SelectOption(label="1", value="1")],
            disabled=True,
        )
        self.select_count.callback = self.select_count_callback

        self.validation_button = discord.ui.Button(
            label="Print",
            custom_id="PrintBtn",
            style=discord.ButtonStyle.green,
            emoji="🖨️",
        )
        self.validation_button.callback = self.validation_button_callback

        self.cancel_button = discord.ui.Button(
            label="Stop",
            style=discord.ButtonStyle.secondary,
            emoji="🚫",
        )
        self.cancel_button.callback = self.cancel_button_callback

        self.help_button = discord.ui.Button(
            label="Help",
            style=discord.ButtonStyle.blurple,
            emoji="📖",
        )
        self.help_button.callback = self.help_button_callback

        #add items to the view
        self.add_item(self.select_type)
        self.add_item(self.select_count)
        self.add_item(self.validation_button)
        self.add_item(self.cancel_button)
        self.add_item(self.help_button)

    # Callback for label type selection
    async def select_type_callback(self, interaction):
        self.label.template = Template(self.select_type.values[0])
        # to prevent the view from resetting the choice when reloading
        for i in self.select_type.options:
            if i.value == self.label.template.key:
                i.default = True
            else:
                i.default = False

        await self.update_select_count_options(interaction)
        await ask_for_additional_data(interaction, self.label, self)
        await update_preview(interaction, self.label, self)

    # Callback for label count selection
    async def select_count_callback(self, interaction):
        self.label.count = int(self.select_count.values[0])
        # to prevent the view from resetting the choice when reloading
        for i in self.select_count.options:
            if i.value == str(self.label.count):
                i.default = True
            else:
                i.default = False
        await interaction.response.defer()

    # Button for validation/print
    async def validation_button_callback(self, interaction):
        self.label.validated = True
        await self.close(interaction)

    # Button to cancel the operation
    async def cancel_button_callback(self, interaction):
        self.label.clear()
        await self.close(interaction)

    # Button to show help
    async def help_button_callback(self, interaction):
        embed = discord.Embed(title="Help", description="This is a help message", color=0x5A64EA)
        await interaction.response.edit_message(embed=embed, files=[])

    # Handle timeout
    async def on_timeout(self):
        self.label.clear()
        await self.close()

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

    async def update_select_count_options(self, interaction):
        available_prints = prints_available_today(self.ctx.author, self.label.template, self.conn)
        if available_prints == 0:
            embed = create_embed("Daily limit reached", f"You have reached the daily limit of {self.label.template.name} labels", 0xff0000, None)
            self.select_count.options = [discord.SelectOption(label="0", value="0")]
            self.select_count.disabled = True
            self.validation_button.disabled = True
            await interaction.response.edit_message(embed=embed, view=self, files=[])
        else:
            self.select_count.options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(1, available_prints + 1)]
            self.select_count.disabled = False
            self.validation_button.disabled = False

        self.label.count = int(self.select_count.options[0].value)
        self.select_count.options[0].default = True


def cog_intial_setup():
    current_dir = os.path.join(os.getcwd(), "label_cog")

    os.makedirs(os.path.join(current_dir, "pdfs"), exist_ok=True)
    os.makedirs(os.path.join(current_dir, "images"), exist_ok=True)

    templates_dir = os.path.abspath("templates")

    print(f"Current working directory: {current_dir}")
    print(f"Templates directory: {templates_dir}")

    if not os.path.exists(os.path.join(current_dir, "templates")):
        raise FileNotFoundError("Templates folder 'templates' is missing")
    if not os.listdir(os.path.join(current_dir, "templates")):
        raise FileNotFoundError("Templates folder 'templates' is empty")
    if not os.path.exists(os.path.join(current_dir, "config.yaml")):
        raise FileNotFoundError("Config file 'config.yaml' is missing")
    if os.path.exists(os.path.join(current_dir, "label_db.sqlite")):
        os.remove(os.path.join(current_dir, "label_db.sqlite")) # todo dev only
    if not os.path.exists(os.path.join(current_dir, "label_db.sqlite")):
        create_tables()



def create_embed(title, description, color, image):
    embed = discord.Embed(title=title, description=description, color=color)
    if image is not None:
        embed.set_image(url=f"attachment://{os.path.basename(image)}")
    return embed



class LabelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cog_intial_setup()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} is ready and online!")

    @discord.slash_command(name="label", description="Print a label")
    async def slash_label(self, ctx):
        conn = sqlite3.connect('label_db.sqlite')

        label = Label(ctx.author)
        view = ChooseLabelView(ctx, label, conn)
        og_message = await ctx.respond(view=view, ephemeral=True)
        await view.wait()
        if label.validated is None:
            embed = create_embed("Operation timed out", "You have taken too long to respond", 0xff0000, label.image)
            await og_message.edit(embed=embed)
            add_log("Operation timed out", ctx.author, label, conn)
            print("interaction timed out...")
        elif label.validated is False:
            embed = create_embed("Operation was canceled", "You have chosen to cancel the operation", 0xff0000, label.image)
            await og_message.edit(embed=embed)
            add_log("Operation was canceled", ctx.author, label, conn)
            print("The operation was canceled...")
        elif label.validated is True:
            embed = create_embed("Waiting for the printer", "The label is being printed", 0xFFFF00, label.image)
            await og_message.edit(embed=embed)
            add_log(f"Label {label.template.key} {label.count} was printed", ctx.author, label, conn)
            ql_brother_print_usb(label.image, label.count)
            print(f"You have chosen to print the label {label.template.key} {label.count} times and validated: {label.validated}")
        display_logs(conn)

    @discord.slash_command(name="logs", description="Display logs")
    async def slash_logs(self, ctx):
        conn = sqlite3.connect('label_db.sqlite')
        print("Displaying logs...")
        logs = display_logs(conn)
        conn.close()
        if logs:
            await ctx.respond(logs)
        else:
            await ctx.respond("No logs found")


def setup(bot):
    bot.add_cog(LabelCog(bot))


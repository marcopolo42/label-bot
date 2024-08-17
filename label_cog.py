import discord
import json
import yaml
import brother_ql

from PIL import Image
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster


from discord.ui import Button, Select, View
from blabel import LabelWriter
from blabel import label_tools
from discord.ext import commands

from datetime import datetime, timedelta

# Importing Image and ImageOps module from PIL package
from PIL import Image, ImageOps

import dotenv
import os
dotenv.load_dotenv()

import pdf2image as p2i


#Utility functions
def get_time(days_to_add=0):
    if days_to_add is None:
        days_to_add = 0
    fmt = "%d.%m.%Y %Hh"
    time = datetime.now() + timedelta(days=days_to_add)
    time = time.strftime(fmt)
    return time


def get_discord_url(id):
    if id is None:
        return ""
    # return "https://profile.intra.42.fr/users/" + id
    return "https://discordapp.com/users/" + str(id)


def get_config():
    config_file = os.getenv("CONFIG_FILE")
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file {config_file} is missing")
    config = yaml.safe_load(open(config_file))
    if config is None:
        raise ValueError("config file is empty or invalid")
    return config


def get_template_info(type, key):
    if type is None:
        raise ValueError("Type is missing")
    if key is None:
        raise ValueError("Key is missing")
    config = get_config()
    templates = config.get("templates")
    if templates is None:
        raise ValueError("Templates are missing in the config file")
    template = None
    for t in templates:
        if t["value"] == type:
            template = t
            break
    if template is None:
        raise ValueError(f"Template {type} not found in config file")
    if key not in template:
        return None
    return template[key]


#parse config.yaml to get the options for the select based on the user's role
def get_role_options(author):
    config = get_config()

    templates = config.get("templates")
    a_roles = [role.name.lower() for role in author.roles]
    print("Author roles before:", a_roles) #todo remove this when done testing
    a_roles.remove("@everyone")
    print("Author roles after:", a_roles)

    options = []
    for template in templates:
        for t_role in template["roles"]:
            print("role t:", t_role.lower())
            if t_role.lower() in a_roles:
                print("common Role found:", t_role)
                print("template:", template)
                options.append(discord.SelectOption(label=template["label"], value=template["value"], description=template["description"], emoji=template["emoji"]))
                break
    if len(options) == 0:
        raise ValueError("No valid roles found for the user")
    return options


def ft_print(image):
    im = Image.open(image)
    im = im.resize((991, 306))
    #print image size
    print(im.size)

    backend = 'pyusb'  # 'pyusb', 'linux_kernal', 'network'
    model = 'QL-600'  # your printer model.
    printer = 'usb://0x04f9:0x20c0'  # Get these values from the Windows usb driver filter.  Linux/Raspberry Pi uses '/dev/usb/lp0'. Macos use 'lsusb' from homebrew.
    if printer is None:
        raise ValueError("Printer ID is missing")
    qlr = BrotherQLRaster(model)
    qlr.exception_on_warning = True

    instructions = convert(

        qlr=qlr,
        images=[im],  # Takes a list of file names or PIL objects.
        label='29x90',
        rotate='90',  # 'Auto', '0', '90', '270'
        threshold=70.0,  # Black and white threshold in percent.
        dither=False,
        compress=False,
        red=False,  # Only True if using Red/Black 62 mm label tape.
        dpi_600=False,
        hq=True,  # False for low quality.
        cut=True

    )

    send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True)


class Label:
    def __init__(self, author):
        self.type = None #todo make default value if user presses without choosing a type it prints "student_food"
        self.count = 1
        self.validated = None
        # default information that is always available. More info can be added based on the template config
        self.info = dict(
            user_name=author.display_name,
            user_picture=author.avatar,
            user_url=get_discord_url(str(author.id)),
            creation_date=get_time()
        )
        # text fields that will be used to ask the user for information using a modal form
        self.fields = None
        #return files
        self.pdf = None
        self.preview = None

    def make(self):
        if self.pdf is not None:
            os.remove(self.pdf)
        if self.preview is not None:
            os.remove(self.preview)

        directory = f"{os.getcwd()}/templates/{self.type}"
        # the folder name of the template should be the same as the type
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Template folder for {self.type} is missing")
        label_writer = LabelWriter(item_template_path=f"{directory}/template.html",
                                   default_stylesheets=(f"templates/{self.type}/style.css",))

        # Set information that don't need user input but are based on the config file
        self.info["expiration_date"] = get_time(get_template_info(self.type, "expiration"))

        # Makes multiple copies of the label
        records = []
        for i in range(self.count):
            records.append(self.info)

        # Writes the labels to a PDF file with a unique file name using the author's ID and the current timestamp
        self.pdf = f"pdf/{self.info.get("user_name")}_{datetime.now().strftime('%d-%m-%Y-%Hh%Mm%Ss')}.pdf"
        label_writer.write_labels(records, target=self.pdf)

        # Convert the PDF to an image
        preview_images = p2i.convert_from_path(self.pdf)
        first_page_image = preview_images[0]
        preview_image_path = os.path.join("preview/", os.path.basename(self.pdf).replace(".pdf", ".png"))
        first_page_image.save(preview_image_path, "PNG")

        # applying grayscale method
        im1 = Image.open(preview_image_path)
        im2 = ImageOps.grayscale(im1)
        im2.save(preview_image_path)

        self.preview = preview_image_path
        return self.preview

    def print(self):
        ft_print(self.preview)

    def update_type(self, type):
        self.type = type
        self.fields = get_template_info(self.type, "fields")


async def update_preview(interaction, label, view):
    embed = discord.Embed(title="Preview of your label", description="This is how your label will look like.", color=0x00ff00)

    for key, value in label.info.items():
        embed.add_field(name=key, value=value)

    label.make()
    file = None
    if label.preview is not None:
        embed.set_image(url=f"attachment://{os.path.basename(label.preview)}")
        file = discord.File(label.preview)
    if interaction.response.is_done():
        await interaction.edit_original_response(embed=embed, view=view, file=file)
    else:
        await interaction.response.edit_message(embed=embed, view=view, file=file)


# Modal to ask for additional data using a modal form
async def ask_for_additional_data(interaction, label, view):
    if label.fields is None:
        return None

    class MyModal(discord.ui.Modal):
        def __init__(self, label):
            super().__init__(title="What would you like on your label ?", timeout=60.0)
            self.label = label
            print(f"Fields: {label.fields}")
            if len(label.fields) > 5:
                raise ValueError("Too many extra fields, the modal can only handle 5 fields")
            for f in label.fields:
                print(f"Adding MFjeiofesif {f}")
                print(f"Adding field {f.get("label")} with max length {f.get("max_length")}")
                if f.get("max_length") > 20:
                    style = discord.InputTextStyle.long
                else:
                    style = discord.InputTextStyle.short
                self.add_item(discord.ui.InputText(label=f.get("label"), max_length=f.get("max_length"), placeholder=f.get("placeholder"), style=style))

        async def callback(self, interaction: discord.Interaction):
            for idx, item in enumerate(self.label.fields): #todo may not work
                self.label.info.update({item["name"]: self.children[idx].value})
            await update_preview(interaction, self.label, view)

    modal = MyModal(label)
    await interaction.response.send_modal(modal)
    await modal.wait()
    return None


async def choose_label(ctx):
    label = Label(ctx.author)

    class ChooseLabelView(discord.ui.View):
        def __init__(self):
            super().__init__(disable_on_timeout=True) # todo check if timeout disable is needed

        @discord.ui.select(placeholder="Choose your label...", custom_id="LabelTypeSelect", options=get_role_options(ctx.author))
        async def label_type_select(self, select, interaction):
            label.update_type(select.values[0])
            # Set the default value to the selected label so that the view doesn't reset the choice
            for i in select.options:
                if i.value == label.type:
                    i.default = True
                else:
                    i.default = False
            self.children[1].options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 3)]
            await ask_for_additional_data(interaction, label, self)
            await update_preview(interaction, label, view)

        @discord.ui.select(placeholder="Choose the number of labels...", custom_id="LabelCountSelect", options=[
            discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 11)])
        async def label_count_select(self, select, interaction):
            label.count = int(select.values[0])
            await interaction.response.defer()

        @discord.ui.button(label="Print", custom_id="PrintBtn", style=discord.ButtonStyle.green, emoji="🖨️")
        async def validation_button(self, button, interaction):
            label.validated = True
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            self.stop()

        @discord.ui.button(label="Stop", style=discord.ButtonStyle.secondary, emoji="🚫") #🚫⛔
        async def cancel_button(self, button, interaction):
            label.validated = False
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
            self.stop()

        @discord.ui.button(label="Help", style=discord.ButtonStyle.blurple, emoji="📖")
        async def help_button(self, button, interaction):
            await interaction.response.send_message("This is a help message", ephemeral=True)

        async def on_timeout(self):
            label.validated = None


    view = ChooseLabelView()
    await ctx.respond(view=view, ephemeral=True)
    await view.wait()
    if label.validated is None:
        print("interaction timed out...")
    elif label.validated is False:
        print("The operation was canceled...")
    elif label.validated is True:
        print(f"You have chosen to print the label {label.type} {label.count} times and validated: {label.validated}")
    return label


def print_pdf(pdf):
    print("Printing PDF")
    #todo print the pdf
    pass


class LabelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} is ready and online!")

    @discord.slash_command(name="label", description="Print a label")
    async def slash_label(self, ctx):
        label = await choose_label(ctx)
        if label.validated is True:
            preview = label.make()
        label.print()



def setup(bot):
    bot.add_cog(LabelCog(bot))


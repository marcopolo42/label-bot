import discord
from discord.ext import commands
import sqlite3
import os
import dotenv

from label_cog.src.db_utils import create_tables, add_log, get_logs, get_user_language

from label_cog.src.discord_utils import change_displayed_status, get_embed

from label_cog.src.label_class import Label

from label_cog.src.views import ChangeLanguageView, ChooseLabelView

from label_cog.src.config import Config

dotenv.load_dotenv()


def cog_setup():
    current_dir = os.path.join(os.getcwd(), "label_cog")
    os.makedirs(os.path.join(current_dir, "pdfs"), exist_ok=True)
    os.makedirs(os.path.join(current_dir, "images"), exist_ok=True)
    if not os.path.exists(os.path.join(current_dir, "templates")):
        raise FileNotFoundError("Templates folder 'templates' is missing")
    if not os.listdir(os.path.join(current_dir, "templates")):
        raise FileNotFoundError("Templates folder 'templates' is empty")
    if not os.path.exists(os.path.join(current_dir, "config.yaml")):
        raise FileNotFoundError("Config file 'config.yaml' is missing")
    if os.path.exists(os.path.join(current_dir, "database.sqlite")):
        os.remove(os.path.join(current_dir, "database.sqlite")) # todo dev only
    if not os.path.exists(os.path.join(current_dir, "database.sqlite")):
        create_tables()


class Session:
    def __init__(self, author):
        self.conn = sqlite3.connect('label_cog/database.sqlite')
        self.author = author
        self.lang = get_user_language(author, self.conn)


class LabelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cog_setup()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} is ready and online!")

    @discord.slash_command(name="label", description="Print a label")
    async def slash_label(self, ctx):
        #update the config in case it has changed
        Config().update_from_file()

        session = Session(ctx.author)
        label = Label(ctx.author)
        view = ChooseLabelView(session, label)
        message = await ctx.respond(embed=get_embed("help", session.lang), view=view, ephemeral=True, timeout=60)
        await view.wait()

        if label.validated is None:
            await change_displayed_status("timeout", session.lang, original_message=message)
            print("interaction timed out...")

        elif label.validated is False:
            await change_displayed_status("canceled", session.lang, original_message=message)
            print("The operation was canceled...")

        elif label.validated is True:
            await change_displayed_status("printing", session.lang, original_message=message)
            add_log(f"Label {label.template.key} {label.count} was printed", ctx.author, label, session.conn)
            #ql_brother_print_usb(label.image, label.count)
            print(f"You have chosen to print the label {label.template.key} {label.count} times and validated: {label.validated}")
        get_logs(session.conn)

    @discord.slash_command(name="change_language", description="Change the language used for the label bot")
    async def slash_change_language(self, ctx):
        session = Session(ctx.author)
        await ctx.respond(view=ChangeLanguageView(session), ephemeral=True)

    @discord.slash_command(name="logs", description="Display logs")
    async def slash_logs(self, ctx):
        conn = sqlite3.connect('label_cog/database.sqlite')
        print("Displaying logs...")
        logs = get_logs(conn)
        conn.close()
        if logs:
            await ctx.respond(logs)
        else:
            await ctx.respond("No logs found")


def setup(bot):
    bot.add_cog(LabelCog(bot))


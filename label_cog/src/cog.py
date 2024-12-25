import discord
from discord.ext import commands
import sqlite3
import os
import dotenv

from label_cog.src.db_utils import create_tables, add_log, get_logs, get_user_language

from label_cog.src.discord_utils import update_displayed_status, get_embed

from label_cog.src.label_class import Label

from label_cog.src.views import ChangeLanguageView, ChooseLabelView

from label_cog.src.config import Config

from label_cog.src.printer_utils import ql_brother_print_usb

from label_cog.src.cleanup_thread import start_cleanup

dotenv.load_dotenv()


def cog_setup():
    current_dir = os.path.join(os.getcwd(), "label_cog")
    os.makedirs(os.path.join(current_dir, "cache"), exist_ok=True)
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
    # start the cleanup thread that will delete old files every 24 hours
    start_cleanup(
        [os.path.join(current_dir, "cache")],
        1,
        24)


class Session:
    def __init__(self, author):
        self.conn = sqlite3.connect('label_cog/database.sqlite')
        self.author = author
        self.roles = Roles(author.roles)
        self.lang = get_user_language(author, self.conn)


class Roles:
    def __init__(self, author_roles):
        self.names = [role.name for role in author_roles]
        self.names_lower = [role_name.lower() for role_name in self.names]


async def choose_and_print_label(ctx):
    session = Session(ctx.author)
    label = Label()
    view = ChooseLabelView(session, label)
    message = await ctx.respond(embed=get_embed("help", session.lang), view=view, ephemeral=True)
    await view.wait()


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
        await choose_and_print_label(ctx)


    @discord.slash_command(name="admin_test_as_role",description="enable you to test the bot as a specific role",)
    async def slash_admin_test_as_role(self, ctx, role: discord.Role):
        #check if the user has the bocal role
        if ("bocal" not in [role.name.lower() for role in ctx.author.roles]
                and ctx.author.id != 508712588381782046     # marco #todo get from config
                and ctx.author.id != 378496894441095168):   # jerome
            await ctx.respond("You need to be from the bocal to use this command", ephemeral=True)
            return
        #ctx.author.roles = [role]
        roles = Roles(ctx.author.roles)

        await choose_and_print_label(ctx)

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


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
        6)


class Session:
    def __init__(self, author):
        self.conn = sqlite3.connect('label_cog/database.sqlite')
        self.author = author
        self.roles = Roles(author.roles)
        self.lang = get_user_language(author, self.conn)


class Roles:
    def __init__(self, author_roles):
        self.names_lower = [role.name.lower() for role in author_roles]
        self.add_bocal_if_needed()

    def is_bocal_role(self, user_roles):
        bocal_roles = [role.lower() for role in Config().get("bocal_roles")]
        return any(role in user_roles for role in bocal_roles)

    def add_bocal_if_needed(self):
        if self.is_bocal_role(self.names_lower):
            print("User has a bocal role")
            self.names_lower.append(Config().get("bocal_role_name").lower())

    def set_as_only_role(self, role):
        self.names_lower = [role.lower()]


def is_admin(ctx):
    if Config().get("bocal_role_name") in [role.name.lower() for role in ctx.author.roles]:
        return True
    unlimited_users = Config().get("unlimited_users")
    if unlimited_users is not None:
        print(f"unlimited_users: {unlimited_users}")
        for user in unlimited_users:
            print(f"user: {user}")
            if user.get("id") == ctx.author.id:
                return True
    return False


async def choose_and_print_label(ctx, session):
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
        session = Session(ctx.author)
        await choose_and_print_label(ctx, session)

    @discord.slash_command(name="admin_test_role", description="enable you to test the bot as a specific role",)
    async def slash_admin_test_role(self, ctx, role: discord.Role):
        Config().update_from_file()
        if is_admin(ctx):
            session = Session(ctx.author)
            session.roles.set_as_only_role(role.name)
            await choose_and_print_label(ctx, session)
        else:
            await ctx.respond("You need to be from the bocal to use this command", ephemeral=True)

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


import discord
from discord.ext import commands
import sqlite3
import aiosqlite
import os
import dotenv
import subprocess

from label_cog.src.db import add_log, get_logs, get_user_language
from label_cog.src.db import Database, create_tables

from label_cog.src.discord_utils import update_displayed_status, get_embed

from label_cog.src.label_class import Label

from label_cog.src.views import ChangeLanguageView, ChooseLabelView

from label_cog.src.config import Config

from label_cog.src.printer_utils import ql_brother_print_usb

from label_cog.src.cleanup_thread import start_cleanup

from label_cog.src.save_user_upload import save_file_uploaded
from label_cog.src.utils import get_cache_directory, get_local_directory

import socket

import label_cog.src.global_vars as global_vars


dotenv.load_dotenv()



def cog_setup():
    # create the cache folders if they don't exist
    if os.getenv('ENV') == 'prod':
        os.makedirs(os.path.join("/dev/shm", 'label_cog', 'cache'), exist_ok=True)
        print("Created cache folder in /dev/shm")
    os.makedirs(os.path.join(os.getcwd(), 'label_cog', 'cache'), exist_ok=True)
    if not os.path.exists(get_local_directory("templates")):
        raise FileNotFoundError("Templates folder 'templates' is missing")
    if not os.listdir(get_local_directory("templates")):
        raise FileNotFoundError("Templates folder 'templates' is empty")
    if not os.path.exists(get_local_directory("config.yaml")):
        raise FileNotFoundError("Config file 'config.yaml' is missing")
    if os.path.exists(get_local_directory("database.sqlite")):
        os.remove(get_local_directory("database.sqlite")) # todo dev only
    # start the cleanup thread that will delete old files every 24 hours
    start_cleanup(
        [get_cache_directory(), os.path.join(os.getcwd(), 'label_cog', 'cache')], #todo clean later
        15,
        1)


class Session:
    def __init__(self, author, lang):
        self.author = author
        self.roles = Roles(author.roles)
        self.lang = lang


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
    interaction = await ctx.respond(embed=get_embed("help", session.lang), view=view, ephemeral=True)
    print(f"interaction contents: {interaction}")
    print(f"interaction contents: {interaction.message}")
    global_vars.channel_link.update({ctx.author.id: interaction.channel.mention})
    await view.wait()


def get_current_ip():
    # Step 1: Get the local hostname.
    local_hostname = socket.gethostname()
    # Step 2: Get a list of IP addresses associated with the hostname.
    ip_addresses = socket.gethostbyname_ex(local_hostname)[2]
    # Step 3: Filter out loopback addresses (IPs starting with "127.").
    filtered_ips = [ip for ip in ip_addresses if not ip.startswith("127.")]
    # Step 4: Extract the first IP address (if available) from the filtered list.
    first_ip = filtered_ips[:1]
    # Step 5: Print the obtained IP address to the console.
    return first_ip


class LabelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cog_setup()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} is ready and online and the current IP is {get_current_ip()}")
        await Database().initialize("label_cog/database.sqlite")
        await create_tables()

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"before session")
        #session = Session(message.author) #todo fix enable to work while /label is used
        print(f"after session")
        if message.author == self.bot.user: # prevent the bot from responding to itself
            return
        print(f"before save_file_uploaded")
        await save_file_uploaded(message, "label_cog/cache", "en")

    @discord.slash_command(name="label", description="Print a label")
    async def label(self, ctx):
        #check if the user is in server
        if ctx.guild is None:
            await ctx.respond("This command can only be used in the 42 server.", ephemeral=True)
            return
        #update the config in case it has changed
        Config().update_from_file()
        session = Session(ctx.author, await get_user_language(ctx.author))
        await choose_and_print_label(ctx, session)

    @discord.slash_command(name="change_language", description="Change the language used for the label bot")
    async def change_language(self, ctx):
        if ctx.guild is None:
            await ctx.respond("This command can only be used in a server", ephemeral=True)
            return
        session = Session(ctx.author, await get_user_language(ctx.author))
        await ctx.respond(view=ChangeLanguageView(session), ephemeral=True)

    #ADMIN COMMANDS
    admin = discord.SlashCommandGroup("admin", "admin only commands")

    @admin.command(name="test_role", description="enable you to test the bot as a specific role", )
    async def test_role(self, ctx, role: discord.Role):
        Config().update_from_file()
        if is_admin(ctx):
            session = Session(ctx.author, await get_user_language(ctx.author))
            session.roles.set_as_only_role(role.name)
            await choose_and_print_label(ctx, session)
        else:
            await ctx.respond("You need to be from the bocal to use this command", ephemeral=True)

    @admin.command(name="logs", description="Display logs")
    async def logs(self, ctx):
        conn = sqlite3.connect('label_cog/database.sqlite')
        print("Displaying logs...")
        logs = get_logs(conn)
        conn.close()
        if logs:
            await ctx.respond(logs)
        else:
            await ctx.respond("No logs found")

    def launch_script(self, script):
        script_path = get_local_directory("scripts", script)
        process = subprocess.Popen(['sudo', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        output = stdout.decode() + stderr.decode()
        return output

    async def run_admin_script(self, ctx, script):
        if os.getenv("ENV") == "dev":
            await ctx.respond("This command is disabled in dev mode", ephemeral=True)
            return
        if not is_admin(ctx):
            await ctx.respond("You need to be from the bocal to use this command", ephemeral=True)
            return
        script_name = script.split(".")[0]
        await ctx.respond(f"Running the {script} script...")
        try:
            output = self.launch_script(script)
            await ctx.followup.send(f"{script_name} script ran successfully. Output:\n{output}")
        except Exception as e:
            await ctx.followup.send(f"Failed to run {script} script: {e}")

    @admin.command(name="update", description="Update the bot")
    async def update(self, ctx):
        await self.run_admin_script(ctx, "update.sh")

    @admin.command(name="start", description="Start the bot")
    async def start(self, ctx):
        await self.run_admin_script(ctx, "start.sh")

    @admin.command(name="stall", description="Disable the bot for 30 minutes")
    async def stall(self, ctx):
        await self.run_admin_script(ctx, "stall.sh")

    @admin.command(name="stop", description="Stop the bot")
    async def stop(self, ctx):
        await self.run_admin_script(ctx, "stop.sh")


def setup(bot):
    bot.add_cog(LabelCog(bot))


def close(self): # may not work
    Database().close()
    print("Database closed for the cog")

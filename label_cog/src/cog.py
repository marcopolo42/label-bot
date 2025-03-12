import discord
from discord.ext import commands
import sqlite3
import aiosqlite
import os
import dotenv
import subprocess

from label_cog.src.database import add_log, get_logs, get_user_language
from label_cog.src.database import Database, create_tables

from label_cog.src.view_utils import update_displayed_status, get_embed

from label_cog.src.label import Label

from label_cog.src.view_choose_label import ChooseLabelView

from label_cog.src.view_change_language import ChangeLanguageView

from label_cog.src.config import Config

from label_cog.src.printer import ql_brother_print_usb

from label_cog.src.cleanup_thread import start_cleanup

from label_cog.src.user_upload import save_file_uploaded
from label_cog.src.utils import get_cache_directory, get_local_directory

import socket

import label_cog.src.global_vars as global_vars

from label_cog.src.utils import get_current_ip

from label_cog.src.admin import is_admin, run_admin_script

from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)

import time

from label_cog.src.session import Session


def cog_setup():
    # create the cache folders if they don't exist
    if os.getenv('ENV') == 'prod':
        os.makedirs(os.path.join("/dev/shm", 'label_cog', 'cache'), exist_ok=True)
        print("Created cache folder in /dev/shm")
        logger.info("Created cache folder in /dev/shm")
    os.makedirs(os.path.join(os.getcwd(), 'label_cog', 'cache'), exist_ok=True)
    if not os.path.exists(get_local_directory("templates")):
        raise FileNotFoundError("Templates folder 'templates' is missing")
    if not os.listdir(get_local_directory("templates")):
        raise FileNotFoundError("Templates folder 'templates' is empty")
    if not os.path.exists(get_local_directory("config")):
        raise FileNotFoundError("Config folder 'config' is missing")
    if os.path.exists(get_local_directory("database.sqlite")):
        os.remove(get_local_directory("database.sqlite")) # todo dev only
    # start the cleanup thread that will delete old files every 24 hours
    start_cleanup(
        [get_cache_directory(), os.path.join(os.getcwd(), 'label_cog', 'cache')], #todo clean later
        15,
        1)
    Config().load_config_files()




async def choose_and_print_label(ctx, session):
    label = Label()
    view = ChooseLabelView(session, label)
    await ctx.respond(embed=get_embed("help", session.lang), view=view, ephemeral=True)
    await view.wait()


class LabelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        cog_setup()

    async def cog_before_invoke(self, ctx):
        logger.debug("cog_before_invoke: database initialization")
        await Database().initialize("label_cog/database.sqlite")
        await create_tables()

    async def cog_after_invoke(self, ctx):
        await Database().close()
        logger.debug("cog_after_invoke: database closed successfully")

    def cog_unload(self):
        logger.debug("Unloading LabelCog...")

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{self.bot.user} is ready and online and the current IP is {get_current_ip()}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: # prevent the bot from responding to itself
            return
        logger.debug(f"before save_file_uploaded")
        await save_file_uploaded(message, "label_cog/cache", "en")

    @discord.slash_command(name="label", description="Print a label")
    async def label(self, ctx):
        #check if the user is in server
        if ctx.guild is None:
            await ctx.respond("This command can only be used in the 42 server.", ephemeral=True)
            return
        #update the config in case it has changed
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
        if is_admin(ctx):
            session = Session(ctx.author, await get_user_language(ctx.author))
            session.roles.set_as_only_role(role.name)
            await choose_and_print_label(ctx, session)
        else:
            await ctx.respond("You need to be from the bocal to use this command", ephemeral=True)

    @admin.command(name="logs", description="Display logs")
    async def logs(self, ctx):
        conn = sqlite3.connect('label_cog/database.sqlite')
        logger.debug("Displaying logs...")
        logs = get_logs()
        conn.close()
        if logs:
            await ctx.respond(logs)
        else:
            await ctx.respond("No logs found")

    @admin.command(name="update", description="Update the bot")
    async def update(self, ctx):
        await run_admin_script(ctx, "update.sh")

    @admin.command(name="start", description="Start the bot")
    async def start(self, ctx):
        await run_admin_script(ctx, "start.sh")

    @admin.command(name="stall", description="Disable the bot for 30 minutes")
    async def stall(self, ctx):
        await run_admin_script(ctx, "stall.sh")

    @admin.command(name="stop", description="Stop the bot")
    async def stop(self, ctx):
        await run_admin_script(ctx, "stop.sh")


def setup(bot):
    bot.add_cog(LabelCog(bot))


def teardown(bot):
    logger.debug("teardown of LabelCog")


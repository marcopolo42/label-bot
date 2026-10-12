"""Bot construction, extension loading, and command-line startup."""
import os
from pathlib import Path

import dotenv
from discord.ext import commands

EXTENSIONS = ("labelbot.cogs.labels",)


class LabelBot(commands.Bot):
    async def close(self):
        cog = self.get_cog("LabelCog")
        if cog is not None:
            await cog.database_ready
        from labelbot.database import Database
        await Database().close()
        for extension in EXTENSIONS:
            if extension in self.extensions:
                self.unload_extension(extension)
        await super().close()


def create_bot():
    bot = LabelBot()
    for extension in EXTENSIONS:
        bot.load_extension(extension)
    return bot


def main():
    dotenv.load_dotenv(Path.cwd() / ".env")
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Set DISCORD_TOKEN in the environment or .env")
    create_bot().run(token)

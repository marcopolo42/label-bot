import discord
from discord.ext import commands
import dotenv
import os
from aiohttp.client_exceptions import ClientConnectorError

dotenv.load_dotenv()


class Bot(commands.Bot):
    async def close(self):
        print('Gracefully shutting down the bot...')
        bot.unload_extension("label_cog.src.cog")
        await super().close()  # don't forget this!


bot = Bot()
bot.load_extension("label_cog.src.cog")


def main():
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except ClientConnectorError:
        print("\033[91mNo internet connection.\033[0m")  # the weird syntax is for making the text red
    except Exception as e:
        raise e


if __name__ == "__main__":
    main()





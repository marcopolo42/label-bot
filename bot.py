import discord
from discord.ext import commands
import dotenv
import os
from aiohttp.client_exceptions import ClientConnectorError

dotenv.load_dotenv()

# Define the bot
bot = discord.Bot()

# Add the cog to the bot
bot.load_extension("label_cog.src.cog")

# Run the bot and catch error when no internet connection
try:
    bot.run(os.getenv('DISCORD_TOKEN'))
except ClientConnectorError:
    print("\033[91mNo internet connection.\033[0m") #the weird syntax is for making the text red
except Exception as e:
    print("\033[91mNo internet connection.\033[0m")



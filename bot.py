import discord
from discord.ext import commands
import dotenv
import os

dotenv.load_dotenv()

# Define the bot
bot = discord.Bot()

# Add the cog to the bot
bot.load_extension("label_cog.main")

# Run the bot with the token
bot.run(os.getenv('DISCORD_TOKEN'))

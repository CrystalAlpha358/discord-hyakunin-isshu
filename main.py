import discord
from discord.commands import Option
from os import getenv
import sys

GUILD_ID = int(getenv('DISCORD_GUILD_ID'))
BOT_TOKEN = getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.none()
intents.guilds = True
intents.reactions = True
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print('Started')

@bot.slash_command(guild_ids=[GUILD_ID])
async def hello(ctx):
    await ctx.respond('Hello!')

bot.run(BOT_TOKEN)

import discord
from discord.commands import Option
import json
from random import randint
import os
import sys

# Constants
JSON = './hyakunin-isshu.json'
GUILD_ID = [ int(os.getenv('DISCORD_GUILD_ID')) ] if True else None
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MSG = {
    'cmds': {
        'testmode':  'プリントに表記されている50首のみ対象にします',
        'ephemeral': '他人から見えないエフェメラルレスポンスで返信します'
    }
}

# Definition
def err(string: str, code: int) -> None:
    print(f'Error: {string}', file=sys.stderr)
    if code > 0:
        sys.exit(code)

def makeEmbed(index: int, dataAll: dict) -> discord.Embed:
    data = dataAll[index]
    author = data['author']
    firstKana = f"__{data['begin']}__{data['first']['kana'].lstrip(data['begin'])}"

    embed = discord.Embed(
        title=f"{data['first']['origin']}\n{data['second']['origin']}"
    )
    embed.set_author(name=f"No. {index + 1}")
    embed.add_field(
        name='かな',
        value=f"__{data['begin']}__{data['first']['kana'].lstrip(data['begin'])}\n" +
              f"{data['second']['kana']}",
        inline=False
    )
    embed.add_field(name='歌意', value=data['mean'], inline=False)
    embed.add_field(name='作者', value=f"{author['origin']} ({author['kana']})", inline=False)

    if data['test']:
        embed.set_footer(text='プリントに表記されています')

    return embed

def getTestsNo(lis: list) -> list:
    ret = []
    for idx, item in enumerate(lis):
        if item['test']:
            ret.append(idx)
    return ret

def findDictFromList(lis: list, key: str, value) -> (int, dict):
    for idx, item in enumerate(lis):
        if (type(item) is dict) and (key in item) and (item[key] == value):
            return idx, item
    return None

# Pycord
intents = discord.Intents.none()
intents.guilds = True
#intents.reactions = True
bot = discord.Bot(intents=intents)

# Load JSON
try:
    with open(JSON, 'r') as f:
        JOBJECT = json.load(f)
except Exception as e:
    err(f"Loading the JSON file {JSON}:\n{e}", 1)

DATA = JOBJECT['data']
testmodeNo = getTestsNo(DATA)

# Ready
@bot.event
async def on_ready():
    print('Started')

# Slash commands
@bot.slash_command(guild_ids=GUILD_ID, name='random')
async def isshu_random(
    ctx,
    testmode:  Option(bool, MSG['cmds']['testmode'],  required=False, default=True),
    ephemeral: Option(bool, MSG['cmds']['ephemeral'], required=False, default=True)
):
    no = testmodeNo[randint(0, len(testmodeNo) - 1)] if testmode else randint(0, 99)
    await ctx.respond(embed=makeEmbed(no, DATA), ephemeral=ephemeral)

# Connect
bot.run(BOT_TOKEN)

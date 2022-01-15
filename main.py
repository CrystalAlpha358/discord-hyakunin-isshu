from random import randint
import json
import os
import re
import sys

import discord
from discord.commands import Option
from discord.ext import pages as Pages

# Constants
JSON = './hyakunin-isshu.json'
GUILD_ID = [ int(os.getenv('DISCORD_GUILD_ID')) ] if True else None
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
OPT = {
    'testmode':  Option(
        bool,
        'プリントに表記されている50首のみ対象にします(既定値: True)',
        required=False, default=True
    ),
    'ephemeral': Option(
        bool,
        '他人から見えないエフェメラルレスポンスで返信します(既定値: True)',
        required=False, default=True
    )
}
PAGE_SIZE = 10

# Definition
def err(string: str, code: int) -> None:
    print(f'Error: {string}', file=sys.stderr)
    if code > 0:
        sys.exit(code)

def expandDictInList(lis: list, base: list) -> dict:
    ret = {}
    for key in base:
        ret[key] = [dic.get(key) for dic in lis]
    return ret

def getDataByNo(index: int, data: dict) -> dict:
    ret = {}

    for key in ['first', 'second', 'author']:
        if not key in ret:
            ret[key] = {}
        for itemkey in ['origin', 'kana']:
            ret[key][itemkey] = data[key][itemkey][index]

    for key in ['begin', 'mean', 'test']:
        ret[key] = data[key][index]

    return ret

def makeEmbed(index: int, data: list) -> discord.Embed:
    dt = getDataByNo(index, data)
    au = dt['author']

    embed = discord.Embed(
        title=f"{dt['first']['origin']}\n{dt['second']['origin']}"
    )
    embed.set_author(name=f"No. {index + 1}")
    embed.add_field(
        name='かな',
        value=f"__{dt['begin']}__{dt['first']['kana'].lstrip(dt['begin'])}\n" +
              f"{dt['second']['kana']}",
        inline=False
    )
    embed.add_field(name='歌意', value=dt['mean'], inline=False)
    embed.add_field(name='作者', value=f"{au['origin']} ({au['kana']})", inline=False)

    if dt['test']:
        embed.set_footer(text='プリントに表記されています')

    return embed

async def sendError(ctx, msg: str) -> None:
    await ctx.respond(f':no_entry_sign: {msg}', ephemeral=True)

# Start
print("Discord Hyakunin Isshu bot\nMade by CrystalAlpha358")

# Pycord
intents = discord.Intents.none()
intents.guilds = True
bot = discord.Bot(intents=intents)

# Load JSON
print('Loading JSON file...')
try:
    with open(JSON, 'r') as f:
        #JOBJECT = json.load(f)
        DATA = expandDictInList(json.load(f)['data'], [
            'first', 'second', 'begin', 'mean', 'author', 'test'
        ])
        for key in ['first', 'second', 'author']:
            DATA[key] = expandDictInList(DATA[key], ['origin', 'kana'])
except Exception as e:
    err(f"Loading the JSON file {JSON}:\n{e}", 1)

# Ready
@bot.event
async def on_ready():
    print('Ready')

# Slash commands
@bot.slash_command(guild_ids=GUILD_ID, name='random')
async def isshu_random(
    ctx,
    testmode:  OPT['testmode' ],
    ephemeral: OPT['ephemeral']
):
    """ランダムに一句を選び詳細を表示します"""
    no = DATA['test'][randint(0, len(DATA['test']) - 1)] if testmode else randint(0, 99)
    await ctx.respond(embed=makeEmbed(no, DATA), ephemeral=ephemeral)

@bot.slash_command(guild_ids=GUILD_ID, name='get')
async def isshu_getByNo(
    ctx,
    number:    Option(int,  '歌番号を指定します(1~100)'),
    ephemeral: OPT['ephemeral']
):
    """歌番号から句を取得し詳細を表示します"""
    if number < 1 or number > 100:
        await sendError(ctx, '指定された値は範囲外です')
    else:
        await ctx.respond(embed=makeEmbed(number - 1, DATA), ephemeral=ephemeral)

@bot.slash_command(guild_ids=GUILD_ID, name='search')
async def isshu_search(
    ctx,
    regex:     Option(str, '検索文字列を指定します。句は歴史的仮名遣いです。正規表現が使えます'),
    target:    Option(
        str, '検索対象を指定します(既定値: phrase)',
        required=False, default='phrase', choices=[
            'phrase', 'first_phrase', 'second_phrase',
            'phrase/kana', 'first_phrase/kana', 'second_phrase/kana',
            'mean',
            'author', 'author/kana'
        ]
    ),
    testmode:  OPT['testmode' ],
    ephemeral: OPT['ephemeral']
):
    """文字列から句を検索します"""
    data = []
    kana = 'kana' if target.endswith('/kana') else 'origin'

    if target == 'mean':
        data = DATA['mean']
    elif target.startswith('author'):
        data = DATA['author'][kana]
    elif (pos := target.find('phrase')) >= 0:
        if pos == 0 or target.startswith('first_'):
            data  = DATA['first'][kana]
        if pos == 0 or target.startswith('second_'):
            data += DATA['second'][kana]
    else:
        await sendError(ctx, '指定された対象は存在しません')
        return
    data = [s.replace(' ', '') for s in data]

    await ctx.defer(ephemeral=ephemeral)
    try:
        regex = re.compile(regex)
    except re.error as e:
        msg = '**正規表現エンジンがエラーを報告しました。文法が誤っていないか確認してください**\n'
        if not e.pos is None:
            start = e.pos - 9 if len(e.pattern) >= 10 else 0
            msg += f'位置 {e.pos}: ``' + \
                   ('...' if start else '') + \
                   e.pattern[start:e.pos + 1].replace('``', r'\`\`') + \
                   '`` *←[問題箇所]*\n'
        msg += f'メッセージ:\n```\n{e.msg}\n```'
        await sendError(ctx, msg)
        return

    result = sorted(list(set([
        idx - (100 if idx >= 100 else 0)
        for idx, val in enumerate(data)
        if regex.search(val)
    ])))
    if testmode and len(result):
        result = [idx for idx in result if DATA['test'][idx]]
    result_len = len(result)

    if not result_len:
        await ctx.respond(
            ':mag_right: 条件に一致する項目は見つかりませんでした',
            ephemeral=ephemeral
        )
        return

    pages = []
    for start in range(0, len(result), PAGE_SIZE):
        embed = discord.Embed(title=f':mag: 検索結果: {result_len}件')
        for idx in result[start:start + PAGE_SIZE]:
            embed.add_field(
                name=(DATA['first']['origin'][idx] + DATA['second']['origin'][idx]).replace(' ', ''),
                value=f"No. {idx + 1}・{DATA['author']['origin'][idx]}",
                inline=False
            )
        pages.append(embed)

    await Pages.Paginator(pages=pages).respond(ctx.interaction, ephemeral=ephemeral)

# Connect
print('Connecting...')
bot.run(BOT_TOKEN)

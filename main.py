from random import randint, sample as rndsample
import asyncio
import json
import os
import re
import sys

import discord
from discord.commands import Option
from discord.ext import pages as Pages

# Constants
JSON = './hyakunin-isshu.json'
GUILD_ID = [int(os.getenv('DISCORD_GUILD_ID'))] if True else None
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
OPT = {
    'testmode': Option(
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
MAX_TIMEOUT = 600


# Definition
def err(string: str, code: int) -> None:
    print(f'Error: {string}', file=sys.stderr)
    if code > 0:
        sys.exit(code)


def expand_dict_in_list(lis: list, base: list) -> dict:
    ret = {}
    for key in base:
        ret[key] = [dic.get(key) for dic in lis]
    return ret


def get_data_by_no(index: int, data: dict) -> dict:
    ret = {}

    for key in ['first', 'second', 'author']:
        if key not in ret:
            ret[key] = {}
        for itemkey in ['origin', 'kana']:
            ret[key][itemkey] = data[key][itemkey][index]

    for key in ['begin', 'mean', 'test']:
        ret[key] = data[key][index]

    return ret


def make_embed(index: int, data: list) -> discord.Embed:
    dt = get_data_by_no(index, data)
    au = dt['author']

    embed = discord.Embed(title=f"{dt['first']['origin']}\n{dt['second']['origin']}")
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


async def send_error(ctx, msg: str) -> None:
    await ctx.respond(f':no_entry_sign: {msg}', ephemeral=True)


# Class
class DropdownView(discord.ui.View):
    def __init__(self, item, timeout):
        super().__init__(timeout=timeout)
        self.add_item(item)


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
        DATA = expand_dict_in_list(json.load(f)['data'], [
            'first', 'second', 'begin', 'mean', 'author', 'test'
        ])
        for key in ['first', 'second', 'author']:
            DATA[key] = expand_dict_in_list(DATA[key], ['origin', 'kana'])
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
    testmode: OPT['testmode'],
    ephemeral: OPT['ephemeral']
):
    """ランダムに一句を選び詳細を表示します"""
    no = DATA['test'][randint(0, len(DATA['test']) - 1)] if testmode else randint(0, 99)
    await ctx.respond(embed=make_embed(no, DATA), ephemeral=ephemeral)


@bot.slash_command(guild_ids=GUILD_ID, name='get')
async def isshu_getByNo(
    ctx,
    number: Option(int,  '歌番号を指定します(1~100)', min_value=1, max_value=100),
    ephemeral: OPT['ephemeral']
):
    """歌番号から句を取得し詳細を表示します"""
    if number < 1 or number > 100:
        await send_error(ctx, '指定された値は範囲外です')
    else:
        await ctx.respond(embed=make_embed(number - 1, DATA), ephemeral=ephemeral)


@bot.slash_command(guild_ids=GUILD_ID, name='search')
async def isshu_search(
    ctx,
    regex: Option(str, '検索文字列を指定します。句は歴史的仮名遣いです。正規表現が使えます'),
    target: Option(
        str, '検索対象を指定します(既定値: phrase)',
        required=False, default='phrase', choices=[
            'phrase', 'first_phrase', 'second_phrase',
            'phrase/kana', 'first_phrase/kana', 'second_phrase/kana',
            'mean',
            'author', 'author/kana'
        ]
    ),
    testmode: OPT['testmode'],
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
            data = DATA['first'][kana]
        if pos == 0 or target.startswith('second_'):
            data += DATA['second'][kana]
    else:
        await send_error(ctx, '指定された対象は存在しません')
        return
    data = [s.replace(' ', '') for s in data]

    await ctx.defer(ephemeral=ephemeral)
    try:
        regex = re.compile(regex)
    except re.error as e:
        msg = '**正規表現エンジンがエラーを報告しました。文法が誤っていないか確認してください**\n'
        if e.pos is not None:
            start = e.pos - 9 if len(e.pattern) >= 10 else 0
            msg += (f'位置 {e.pos}: ``'
                    + ('...' if start else '')
                    + e.pattern[start:e.pos + 1].replace('``', r'\`\`')
                    + '`` *←[問題箇所]*\n')
        msg += f'メッセージ:\n```\n{e.msg}\n```'
        await send_error(ctx, msg)
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
        for idx in result[start: start + PAGE_SIZE]:
            embed.add_field(
                # noqa
                name=(DATA['first']['origin'][idx] + DATA['second']['origin'][idx])
                     .replace(' ', ''),
                value=f"No. {idx + 1}・{DATA['author']['origin'][idx]}",
                inline=False
            )
        pages.append(embed)

    await Pages.Paginator(pages=pages).respond(ctx.interaction, ephemeral=ephemeral)


@bot.slash_command(guild_ids=GUILD_ID, name='question')
async def isshu_question(
    ctx,
    choices_cnt: Option(
        int, '選択肢の数を指定します(2~10, 既定値: 4)',
        required=False, min_value=2, max_value=10, default=4
    ),
    swapmode: Option(
        bool, '下の句から上の句を選ぶモードにします(既定値: False)',
        required=False, default=False
    ),
    timeout: Option(
        int, f'メニューが期限切れになるまでの秒数を指定します(10~{MAX_TIMEOUT}, 既定値: 最大値)',
        required=False, min_value=10, max_value=MAX_TIMEOUT, default=MAX_TIMEOUT
    ),
    testmode: OPT['testmode'],
    ephemeral: OPT['ephemeral']
):
    """ランダムに問題を生成します"""
    baselist = [i for i, v in enumerate(DATA['test']) if v] if testmode else range(100)
    choices = rndsample(baselist, choices_cnt)
    correct = randint(0, choices_cnt - 1)
    sent_msg = None
    task = None

    async def send_answer(method, msg: str):
        return await method(
            content=msg,
            embed=make_embed(choices[correct], DATA),
            ephemeral=True
        )

    async def send_disabled_dropdown(msg: str):
        try:
            return await sent_msg.edit_original_message(view=DropdownView(discord.ui.Select(
                placeholder=msg,
                disabled=True,
                options=[discord.SelectOption(label='dummy', value='dummy')]
            ), timeout))
        except (discord.HTTPException, discord.Forbidden):
            return None

    async def timed_out(method):
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            return
        await send_answer(method, ':x: 時間切れです...')
        await send_disabled_dropdown('[期限切れです]')

    class Question(discord.ui.Select):
        def __init__(self):
            super().__init__(placeholder='句を選択...', min_values=1, max_values=1)

            i = 1
            for idx in choices:
                self.add_option(
                    # noqa
                    label=f"{i}._{DATA['first' if swapmode else 'second']['origin'][idx]}"
                          .replace(' ', '').replace('_', ' '),
                    value=str(i - 1)
                )
                i += 1

        async def callback(self, interaction: discord.Interaction):
            no = int(self.values[0])

            await send_answer(interaction.response.send_message,
                              ':o: 正解！' if no == correct else ':x: 不正解...')

            task.cancel()
            await send_disabled_dropdown(
                f"{DATA['first' if swapmode else 'second']['origin'][choices[no]]}"
                .replace(' ', '')
            )

    sent_msg = await ctx.respond(
        content=f":question: この{'下' if swapmode else '上'}の句に対応する"
                + f"__**{'上' if swapmode else '下'}の句**__を選択してください",
        embed=discord.Embed(
            # noqa
            title=f"{DATA['second' if swapmode else 'first']['origin'][choices[correct]]}"
                  .replace(' ', ''),
            description=f'※メニューは約{timeout}秒間有効です'
        ),
        view=DropdownView(Question(), timeout),
        ephemeral=ephemeral
    )

    task = asyncio.create_task(timed_out(ctx.respond))

# Connect
print('Connecting...')
bot.run(BOT_TOKEN)

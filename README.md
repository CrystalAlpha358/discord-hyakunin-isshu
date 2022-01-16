discord-hyakunin-isshu
===

Discordで百人一首の勉強ができる... かも？

## Description
テストの為に急遽作ることになったDiscord用百人一首Botです。  
開発期間3日、実時間だと18〜20時間くらい？  
とにかく急いで作った(+そんなにPythonを触ったことがない)ので雑です。

...まあ間に合わなかったんですけど。

## Requirements
- Python 3.8 以上 (3.8.10 でテスト済み)
- [Pycord](https://github.com/Pycord-Development/pycord) の開発版 (スラッシュコマンドに対応していること)

## How to use
こんなもの一体誰が使うのかわかりませんが一応書いておきます。

1. 環境変数 `DISCORD_BOT_TOKEN` にBotのトークンをセット
1. 環境変数 `DISCORD_GUILD_ID` にDiscordサーバーのIDをセット  
   グローバルコマンドとして登録させたい場合は `main.py` の13行目の `True` を `False` にすれば多分動く(未検証)
1. `main.py` を実行 (具体的なコマンドは環境依存なので割愛)  
   `hyakunin-isshu.json` が同じディレクトリに無いと起動できないので注意
1. 煮るなり焼くなりお好きにどうぞ

## Commands
- `/get <number> [ephemeral]`
  - 歌番号 `number` に対応する句の詳細を表示します。
- `/random [testmode] [ephemeral]`
  - 句の中からランダムに一つ句を選び、その詳細を表示します。  
- `/search <regex> [target] [testmode] [ephemeral]`
  - `regex` に指定した正規表現にマッチする句を検索し、ヒットした一覧を表示します。  
    `target` には検索する対象を指定することができます。[ここ](#Supplement-検索対象について)を参照してください。
    省略時は `phrase` です。  
    句は歴史的仮名遣いであることに注意してください。  
- `/question [choices_cnt=2-10] [swapmode=True|False] [timeout=10-600] [testmode] [ephemeral]`
  - 問題を生成します。  
    デフォルトでは上の句から下の句を選ぶモードですが、`swapmode` を `True` にすると下の句から上の句を選ぶモードになります。  
    `choices_cnt` は選択肢の数を `2` 〜 `10` 個の間で指定できます。省略時は `4` です。  
    `timeout` は選択メニューが期限切れになるまでの秒数を `10` 〜 `600` 秒(10分)の間で指定します。省略時は `600` です。  

### Common options
- `... [testmode=True|False]`
  - `True` の場合、プリントに表記された50首のみが対象になります。  
    省略時は `True` です。
- `... [ephemeral=True|False]`
  - `True` の場合、他人に見えないようにエフェメラルレスポンスで返答します。  
    `False` の場合は通常のメッセージと同じように他人から閲覧することができます。  
    省略時は `True` です。

#### Supplement: 検索対象について
| target               | 説明             |
|:---------------------|:-----------------|
| `phrase`             | 句全体           |
| `first_phrase`       | 上の句           |
| `second_phrase`      | 下の句           |
| `phrase/kana`        | 句全体、ひらがな |
| `first_phrase/kana`  | 上の句、ひらがな |
| `second_phrase/kana` | 下の句、ひらがな |
| `mean`               | 歌意             |
| `author`             | 作者             |
| `author/kana`        | 作者、ひらがな   |

## TODO
- [x] 簡単な問題生成 (上の句から下の句をn択で選べみたいな)

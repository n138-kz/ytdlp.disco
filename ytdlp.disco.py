import json
import os
import sys
import math
import discord
from discord.ext import commands, tasks
import datetime
import time
import yt_dlp

def load_config():
    config = None
    with open('.secret/config.json') as f:
        config = json.load(f)
    return config
config = load_config()

def now(splitchar_date='-',splitchar_time=':'):
    now = datetime.datetime.now()
    return now.strftime(f'%Y{splitchar_date}%m{splitchar_date}%d %H{splitchar_time}%M{splitchar_time}%S')

# App version
SELF_CONTEXT = {
    'version': '1',
}

# Discord APIトークン
DISCORD_API_TOKEN = config['external']['discord']['bot_token']

# Wakeup 接頭辞
PREPAND_LINKS = []
PREPAND_LINKS.extend(config['internal']['prepand_links'])

def ytdlp_progress_hook(d):
    if d['status'] == 'downloading':
        # ダウンロード中の処理
        print(f"進捗: {d['_percent_str']}")
    elif d['status'] == 'finished':
        # ダウンロード完了時の処理
        print("ダウンロード完了")

def ytdlp_metadata(meta):
    return {
        'upload_date': meta['upload_date'],
        'uploader': meta['uploader'],
        'views': meta['view_count'],
        'likes': meta['like_count'],
        'id': meta['id'],
        'format': meta['format'],
        'duration': meta['duration'],
        'title': meta['title'],
        'description': meta['description'],
    }

# yt-dlp オプション
YDL_OPTS = config['internal']['ydl_options']
YDL_OPTS = {**YDL_OPTS, **{'progress_hooks': [ytdlp_progress_hook]}}

intents=discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_message(message):
    try:
        # 送信者がbotである場合は弾く
        if message.author.bot:
            return
        
        # テキストチャンネルのみ処理
        if message.channel.type != discord.ChannelType.text:
            return
        
        for prepand_link in PREPAND_LINKS:
            if message.content.startswith(prepand_link):
                print('[{0}] [{1}] {2}: {3}'.format(
                    now(), 'DEBUG'.ljust(8, ' '),
                    'on.message',
                    message.content,
                ))

                with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                    meta = ydl.extract_info(
                        message.content,
                        download=False
                    )
                    ydl.download([message.content])

                file='result.json'
                with open(file, mode='w',encoding='UTF-8') as f:
                    json.dump(meta,f,indent=4,ensure_ascii=False)

                text = '[{0}] {1}\n{2}\n'.format(
                    meta['id'],
                    meta['title'],
                    meta['uploader'],
                )

                embed = discord.Embed(
                    title=client.user.name.capitalize(),
                    description=text,
                    color=0x00ff00,
                    url='https://github.com/n138-kz/ytdlp.disco',
                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                )
                embed.set_thumbnail(url=client.user.avatar.url)
                response = await message.reply(embed=embed,files=[discord.File(file)])
                print(response)
    except:
        sys.exit()

@tree.command(name="ping",description="Botのレイテンシを測定します。")
async def ping(interaction: discord.Interaction):
    # Ping値を秒単位で取得
    raw_ping = client.latency

    # ミリ秒に変換して丸める
    ping = round(raw_ping * 1000)

    # 送信する
    await interaction.response.send_message(f"Pong!\nBotのPing値は{ping}msです。",ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

@tree.command(name="version",description="Botのバージョンを表示します。")
async def version(interaction: discord.Interaction):
    text = ''
    text += 'python\n```\n'+sys.version+'```\n'
    text += 'discord.py\n```\n'+discord.__version__+' ('+str(discord.version_info)+')'+'```\n'
    text += client.user.name+'\n```\n'+SELF_CONTEXT['version']+'```\n'

    # 送信する
    await interaction.response.send_message(GLOBAL_TEXT['err'][LOCALE]['incomplete_command'],ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

@client.event
async def on_ready():
    print('[{0}] [{1}] {2}: {3}'.format(
        now(), 'DEBUG'.ljust(8, ' '),
        'discord.bot.url',
        config['external']['discord']['scope']['bot_invite_url'],
    ))

    print('[{0}] [{1}] {2}: {3}'.format(
        now(), 'DEBUG'.ljust(8, ' '),
        'config', '--BEGIN',
    ))
    for prepand_link in PREPAND_LINKS:
        print('[{0}] [{1}] {2}: {3}'.format(
            now(), 'DEBUG'.ljust(8, ' '),
            'config.internal.prepand_links',
            prepand_link,
        ))
    print('[{0}] [{1}] {2}: {3}'.format(
        now(), 'DEBUG'.ljust(8, ' '),
        'config', '--END',
    ))

    # スラッシュコマンドを同期
    await tree.sync()
    print('[{0}] [{1}] {2}: {3}'.format(
        now(), 'DEBUG'.ljust(8, ' '),
        'discord.bot.sync.tree',
        'Done',
    ))

    # アクティビティステータスを設定
    # https://qiita.com/ryo_001339/items/d20777035c0f67911454
    await client.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name='/help'))

    print('[{0}] [{1}] {2}: {3}'.format(
        now(), 'DEBUG'.ljust(8, ' '),
        'discord.bot.name',
        ''+client.user.name,
    ))

# botを起動
def main():
    client.run(DISCORD_API_TOKEN)

if __name__ == '__main__':
    main()

import os
import sqlite3

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# データベース
# =========================

def init_database():
    conn = sqlite3.connect("niku_bot.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS enabled_channels (
            guild_id INTEGER NOT NULL,
            channel_id INTEGER PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()


def load_enabled_channels():
    conn = sqlite3.connect("niku_bot.db")

    rows = conn.execute(
        "SELECT guild_id, channel_id FROM enabled_channels"
    ).fetchall()

    conn.close()

    return {
        (row[0], row[1])
        for row in rows
    }


def enable_channel(guild_id, channel_id):
    conn = sqlite3.connect("niku_bot.db")

    conn.execute(
        """
        INSERT OR IGNORE INTO enabled_channels
        (guild_id, channel_id)
        VALUES (?, ?)
        """,
        (guild_id, channel_id)
    )

    conn.commit()
    conn.close()


def disable_channel(channel_id):
    conn = sqlite3.connect("niku_bot.db")

    conn.execute(
        "DELETE FROM enabled_channels WHERE channel_id = ?",
        (channel_id,)
    )

    conn.commit()
    conn.close()


# 起動時にデータベースを準備
init_database()

# データベースからONになっているチャンネルを読み込む
enabled_channels = load_enabled_channels()


# =========================
# Bot
# =========================

@bot.event
async def on_ready():
    print(f"{bot.user} でログインしました")


@bot.command()
@commands.has_permissions(administrator=True)
async def niku(ctx, mode=None):

    guild_id = ctx.guild.id
    channel_id = ctx.channel.id
    channel_key = (guild_id, channel_id)

    if mode == "off":
        disable_channel(channel_id)
        enabled_channels.discard(channel_key)

        await ctx.send("このチャンネルでの反応をOFFにしました。")

    elif mode == "status":
        if channel_key in enabled_channels:
            await ctx.send("現在、このチャンネルはONです。")
        else:
            await ctx.send("現在、このチャンネルはOFFです。")

    else:
        enable_channel(guild_id, channel_id)
        enabled_channels.add(channel_key)

        await ctx.send("このチャンネルでの反応をONにしました。")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.guild is None:
        await bot.process_commands(message)
        return

    # ONになっているチャンネルだけ反応
    channel_key = (message.guild.id, message.channel.id)

    if channel_key in enabled_channels:
        if "にく" in message.content:
            await message.channel.send("nice お肉‼")

    # !niku などのコマンドを処理
    await bot.process_commands(message)


bot.run(token)
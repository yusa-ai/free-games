import os
import sqlite3
from datetime import datetime

import discord
import requests
from discord.ext import tasks

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

DB_FILE = "games.db"
DB_SCRIPT_FILE = "script.sql"

CHEAPSHARK_API_DEAL_ENDPOINT = "https://www.cheapshark.com/api/1.0/deals"
CHEAPSHARK_API_STORE_ENDPOINT = "https://www.cheapshark.com/api/1.0/stores"
CHEAPSHARK_DEAL_URL = "https://www.cheapshark.com/redirect?dealID="


bot = discord.Bot()

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

with open(DB_SCRIPT_FILE) as file:
    script = file.read()

cursor.executescript(script)

conn.commit()


def get_current_date_time():
    return "[" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "]"


def get_free_games() -> dict:
    cursor.execute("SELECT id FROM stores")
    store_tuples = cursor.fetchall()

    store_ids = ",".join(tpl[0] for tpl in store_tuples)

    response = requests.get(url=CHEAPSHARK_API_DEAL_ENDPOINT, params={
        "upperPrice": 0,
        "storeID": store_ids
    })
    return response.json()


def get_url(deal_id: str) -> str:
    return f"{CHEAPSHARK_DEAL_URL}{deal_id}"


def get_store_name(store_id: str) -> str:
    cursor.execute("SELECT name FROM stores WHERE id = ?", (store_id,))
    store_name = cursor.fetchone()[0]

    return store_name


def get_embed(game):
    embed = discord.Embed(
        title=game["title"],
        url=f"https://www.cheapshark.com/redirect?dealID={game['dealID']}",
        description=f"Free for a limited time on {get_store_name(game['storeID'])}!", color=0xc15c5c
    )
    embed.set_thumbnail(url=game["thumb"])
    return embed


@tasks.loop(minutes=15)
async def broadcast_free_games(debug=False):
    cursor.execute("SELECT id FROM channels")
    channel_ids = [ch[0] for ch in cursor.fetchall()]

    free_games = get_free_games()

    # Remove expired deals from history
    remove_expired_deals(free_games)

    for channel_id in channel_ids:
        cursor.execute("SELECT id FROM deals WHERE channel_id = ?", (channel_id,))
        previous_deal_ids = [deal[0] for deal in cursor.fetchall()]

        for game in free_games:
            deal_id = game["dealID"]

            if deal_id not in previous_deal_ids or debug is True:
                embed = get_embed(game)
                await bot.get_channel(channel_id).send(embed=embed)

                if debug is False:
                    cursor.execute("INSERT INTO deals VALUES (?, ?)", (deal_id, channel_id))
                    conn.commit()

    print(f"{get_current_date_time()} Sent free games to subscribed channels")


async def send_free_games(ctx, debug=False):
    free_games = get_free_games()

    cursor.execute("SELECT id FROM deals WHERE channel_id = ?", (ctx.channel_id,))
    previous_deal_ids = [deal[0] for deal in cursor.fetchall()]

    embeds = []

    for game in free_games:
        deal_id = game["dealID"]

        if deal_id not in previous_deal_ids or debug is True:
            embeds.append(get_embed(game))

            if debug is False:
                cursor.execute("INSERT INTO deals VALUES (?, ?)", (deal_id, ctx.channel_id))
                conn.commit()

    if embeds:
        await ctx.respond(embeds=embeds)
    else:
        await ctx.respond("No new free game available!")


def remove_expired_deals(free_games):
    cursor.execute("SELECT DISTINCT id FROM deals")
    history_deal_ids = [deal[0] for deal in cursor.fetchall()]

    free_game_ids = [game["dealID"] for game in free_games]

    for deal_id in history_deal_ids:
        if deal_id not in free_game_ids:
            cursor.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
    conn.commit()


@bot.event
async def on_ready():
    print(f"{get_current_date_time()} Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for free games"))
    broadcast_free_games.start()


@bot.slash_command(description="Fetch free game deals")
async def free(ctx):
    await send_free_games(ctx)


@bot.slash_command(description="Subscribe the bot to the current channel to get free game deals")
async def subscribe(ctx):
    try:
        cursor.execute("INSERT INTO channels VALUES (?)", (ctx.channel_id,))
        conn.commit()
        await ctx.respond("✅ This channel is now subscribed to receive free game deals.")
    except sqlite3.IntegrityError:
        await ctx.respond("❌ This channel is already subscribed to receive free game deals.")


@bot.slash_command(description="Unsubscribe the current channel from receiving free game deals")
async def unsubscribe(ctx):
    cursor.execute("DELETE FROM deals WHERE channel_id = ?", (ctx.channel_id,))
    cursor.execute("DELETE FROM channels WHERE id = ?", (ctx.channel_id,))
    conn.commit()
    await ctx.respond("✅ This channel is now unsubscribed from receiving free game deals.")


bot.run(DISCORD_BOT_TOKEN)

from datetime import datetime

import discord
import requests

import database

CHEAPSHARK_API_DEAL_ENDPOINT = "https://www.cheapshark.com/api/1.0/deals"
CHEAPSHARK_API_STORE_ENDPOINT = "https://www.cheapshark.com/api/1.0/stores"
CHEAPSHARK_DEAL_URL = "https://www.cheapshark.com/redirect?dealID="


def get_current_date_time():
    return "[" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "]"


def get_free_games() -> dict:
    database.cursor.execute("SELECT id FROM stores")
    store_tuples = database.cursor.fetchall()

    store_ids = ",".join(tpl[0] for tpl in store_tuples)

    response = requests.get(url=CHEAPSHARK_API_DEAL_ENDPOINT, params={
        "upperPrice": 0,
        "storeID": store_ids
    })
    return response.json()


def get_store_name(store_id: str) -> str:
    database.cursor.execute("SELECT name FROM stores WHERE id = ?", (store_id,))
    store_name = database.cursor.fetchone()[0]

    return store_name


def get_embed(game):
    embed = discord.Embed(
        title=game["title"],
        url=f"{CHEAPSHARK_DEAL_URL}{game['dealID']}",
        description=f"Free for a limited time on {get_store_name(game['storeID'])}!", color=0xc15c5c
    )
    embed.set_thumbnail(url=game["thumb"])
    return embed


async def send_free_games(ctx, debug=False):
    free_games = get_free_games()

    database.cursor.execute("SELECT id FROM deals WHERE channel_id = ?", (ctx.channel_id,))
    previous_deal_ids = [deal[0] for deal in database.cursor.fetchall()]

    embeds = []

    for game in free_games:
        deal_id = game["dealID"]

        if deal_id not in previous_deal_ids or debug is True:
            embeds.append(get_embed(game))

            if debug is False:
                database.cursor.execute("INSERT INTO deals VALUES (?, ?)", (deal_id, ctx.channel_id))
                database.connection.commit()

    if embeds:
        await ctx.respond(embeds=embeds)
    else:
        await ctx.respond("No new free game available!")

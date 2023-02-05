from datetime import datetime

import discord
import requests

import database

CHEAPSHARK_API_DEAL_ENDPOINT = "https://www.cheapshark.com/api/1.0/deals"
CHEAPSHARK_API_STORE_ENDPOINT = "https://www.cheapshark.com/api/1.0/stores"
CHEAPSHARK_DEAL_URL = "https://www.cheapshark.com/redirect?dealID="

METACRITIC_URL = "https://www.metacritic.com"


def get_current_date_time() -> str:
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


def get_deal_url(game: dict) -> str:
    return f"{CHEAPSHARK_DEAL_URL}{game['dealID']}"


def get_store_name(store_id: str) -> str:
    database.cursor.execute("SELECT name FROM stores WHERE id = ?", (store_id,))
    store_name = database.cursor.fetchone()[0]

    return store_name


def get_embed(game: dict) -> discord.Embed:
    embed = discord.Embed(
        title=game["title"],
        url=get_deal_url(game),
        description=f"Free for a limited time on {get_store_name(game['storeID'])}!",
        color=0xc15c5c
    )

    embed.add_field(name="Sale price", value=f"${game['salePrice']}", inline=True)
    embed.add_field(name="Normal price", value=f"${game['normalPrice']}", inline=True)

    embed.add_field(name="\u200b", value="\u200b")

    embed.add_field(name="Metacritic score", value=game["metacriticScore"], inline=True)
    embed.add_field(name="Metacritic URL", value=f"[Metacritic]({METACRITIC_URL}{game['metacriticLink']})",
                    inline=True)

    embed.set_image(url=game["thumb"])

    return embed


def get_stores() -> list:
    database.cursor.execute("SELECT * FROM stores ORDER BY name")
    stores = database.cursor.fetchall()
    return stores


def get_selected_store_ids(channel_id: int) -> list:
    database.cursor.execute("SELECT store_id FROM channel_stores WHERE channel_id = ?", (channel_id,))
    selected_store_ids = database.cursor.fetchall()
    selected_store_ids = [tpl[0] for tpl in selected_store_ids]
    return selected_store_ids

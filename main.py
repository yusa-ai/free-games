import os
import sqlite3

import discord
from discord.ext import commands
from discord.ext import tasks

import database
import functions
from select_stores import SelectStores

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

bot = discord.Bot()


@tasks.loop(minutes=15)
async def broadcast_free_games(debug=False):
    database.cursor.execute("SELECT id FROM channels")
    channel_ids = [ch[0] for ch in database.cursor.fetchall()]

    free_games = functions.get_free_games()

    # Remove expired deals from history
    functions.remove_expired_deals(free_games)

    for channel_id in channel_ids:
        database.cursor.execute("SELECT id FROM deals WHERE channel_id = ?", (channel_id,))
        previous_deal_ids = [deal[0] for deal in database.cursor.fetchall()]

        for game in free_games:
            deal_id = game["dealID"]

            if deal_id not in previous_deal_ids or debug is True:
                embed = functions.get_embed(game)
                await bot.get_channel(channel_id).send(embed=embed)

                if debug is False:
                    database.cursor.execute("INSERT INTO deals VALUES (?, ?)", (deal_id, channel_id))
                    database.connection.commit()

    print(f"{functions.get_current_date_time()} Sent free games to subscribed channels")


@bot.event
async def on_ready():
    print(f"{functions.get_current_date_time()} Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for free games"))
    broadcast_free_games.start()


@bot.slash_command(description="Query free game deals manually")
@commands.cooldown(1, 900, commands.BucketType.guild)
async def free(ctx):
    await functions.send_free_games(ctx)


@bot.slash_command(description="Subscribe the bot to the current channel to get free game deals")
async def subscribe(ctx):
    try:
        database.cursor.execute("INSERT INTO channels VALUES (?)", (ctx.channel_id,))
        database.connection.commit()
        await ctx.respond("✅ This channel is now subscribed to receive free games.")
    except sqlite3.IntegrityError:
        await ctx.respond("✅ This channel is already subscribed to receive free games.")


@bot.slash_command(description="Unsubscribe the current channel from receiving free games")
async def unsubscribe(ctx):
    database.cursor.execute("DELETE FROM deals WHERE channel_id = ?", (ctx.channel_id,))
    database.cursor.execute("DELETE FROM channels WHERE id = ?", (ctx.channel_id,))
    database.connection.commit()
    await ctx.respond("✅ This channel is now unsubscribed from receiving free games.")


@bot.slash_command(description="Choose which stores to get free games from", guild_ids=[1067218515343450264])
async def stores(ctx):
    view = discord.ui.View(SelectStores(ctx))
    await ctx.respond("Select which stores to look for free games from", view=view)


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"❌ This command is currently on cooldown. Please try again in {round(error.retry_after)}s.")


bot.run(DISCORD_BOT_TOKEN)

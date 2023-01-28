import os

from discord.ext import commands
from discord.ext import tasks

from functions import *

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

bot = discord.Bot()


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


@bot.event
async def on_ready():
    print(f"{get_current_date_time()} Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for free games"))
    broadcast_free_games.start()


@bot.slash_command(description="Query free game deals manually")
@commands.cooldown(1, 900, commands.BucketType.guild)
async def free(ctx):
    await send_free_games(ctx)


@bot.slash_command(description="Subscribe the bot to the current channel to get free game deals")
async def subscribe(ctx):
    try:
        cursor.execute("INSERT INTO channels VALUES (?)", (ctx.channel_id,))
        conn.commit()
        await ctx.respond("✅ This channel is now subscribed to receive free game deals.")
    except sqlite3.IntegrityError:
        await ctx.respond("✅ This channel is already subscribed to receive free game deals.")


@bot.slash_command(description="Unsubscribe the current channel from receiving free game deals")
async def unsubscribe(ctx):
    cursor.execute("DELETE FROM deals WHERE channel_id = ?", (ctx.channel_id,))
    cursor.execute("DELETE FROM channels WHERE id = ?", (ctx.channel_id,))
    conn.commit()
    await ctx.respond("✅ This channel is now unsubscribed from receiving free game deals.")


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"❌ This command is currently on cooldown. Please try again in {round(error.retry_after)}s.")


bot.run(DISCORD_BOT_TOKEN)

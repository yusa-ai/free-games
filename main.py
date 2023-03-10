import os
import sqlite3

import discord
from discord.ext import commands
from discord.ext import tasks

import database
import functions
from components import SelectStores, DealButton, SelectRole

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(intents=intents)

WAIT_INTERVAL_HOURS = 12


@tasks.loop(hours=WAIT_INTERVAL_HOURS)
async def main_loop() -> None:
    free_games = functions.get_free_games()

    await broadcast_free_games(free_games)
    await remove_expired_deals(free_games)


async def broadcast_free_games(free_games, debug=False) -> None:
    database.cursor.execute("SELECT id FROM channels")
    channel_ids = [ch[0] for ch in database.cursor.fetchall()]

    for channel_id in channel_ids:
        # Get stores that the channel listens to
        database.cursor.execute("SELECT store_id FROM channel_stores WHERE channel_id = ?", (channel_id,))
        selected_store_ids = database.cursor.fetchall()
        selected_store_ids = [tpl[0] for tpl in selected_store_ids]

        # Get previous deals
        database.cursor.execute("SELECT id FROM deals WHERE channel_id = ?", (channel_id,))
        previous_deal_ids = [deal[0] for deal in database.cursor.fetchall()]

        for game in free_games:
            if game["storeID"] not in selected_store_ids:
                continue

            deal_id = game["dealID"]

            # Check if deal was not already sent
            if deal_id not in previous_deal_ids or debug is True:
                database.cursor.execute("SELECT role_id FROM channels WHERE id = ?", (channel_id,))
                role_id = database.cursor.fetchone()[0]

                content = f"<@&{role_id}>" if role_id else None
                embed = functions.get_embed(game)
                view = discord.ui.View(DealButton(game))

                await bot.get_channel(channel_id).send(content=content, embed=embed, view=view)

                if debug is False:
                    database.cursor.execute("INSERT INTO deals VALUES (?, ?)", (deal_id, channel_id))
                    database.connection.commit()

    print(f"{functions.get_current_date_time()} Sent free games to subscribed channels")


async def remove_expired_deals(free_games) -> None:
    database.cursor.execute("SELECT DISTINCT id FROM deals")
    history_deal_ids = [deal[0] for deal in database.cursor.fetchall()]

    free_game_ids = [game["dealID"] for game in free_games]

    for deal_id in history_deal_ids:
        if deal_id not in free_game_ids:
            database.cursor.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
    database.connection.commit()


@commands.has_permissions(administrator=True)
@bot.slash_command(description="Register the current channel to get free game deals")
async def register(ctx: discord.ApplicationContext) -> None:
    try:
        database.cursor.execute("INSERT INTO channels (id, guild_id) VALUES (?, ?)", (ctx.channel_id, ctx.guild_id))

        # Add default stores to channel
        default_stores = functions.get_stores()
        for store in default_stores:
            database.cursor.execute("INSERT INTO channel_stores VALUES (?, ?)", (ctx.channel_id, store[0]))
        database.connection.commit()

        await ctx.respond("??? This channel is now subscribed to receive free games.")

    except sqlite3.IntegrityError:
        await ctx.respond("??? This channel is already subscribed to receive free games.")


@commands.has_permissions(administrator=True)
@bot.slash_command(description="Unregister the current channel from receiving free games")
async def unregister(ctx: discord.ApplicationContext) -> None:
    database.cursor.execute("DELETE FROM deals WHERE channel_id = ?", (ctx.channel_id,))
    database.cursor.execute("DELETE FROM channels WHERE id = ?", (ctx.channel_id,))
    database.cursor.execute("DELETE FROM channel_stores WHERE channel_id = ?", (ctx.channel_id,))
    database.connection.commit()

    await ctx.respond("??? This channel is now unsubscribed from receiving free games.")


@commands.has_permissions(administrator=True)
@bot.slash_command(description="Select which stores to get free games from")
async def stores(ctx: discord.ApplicationContext) -> None:
    view = discord.ui.View(SelectStores(ctx))
    await ctx.respond("Select which stores to get free games from", view=view, ephemeral=True)


@commands.has_permissions(administrator=True)
@bot.slash_command(description="Select which role to ping when there is a free game to claim")
async def role(ctx: discord.ApplicationContext) -> None:
    view = discord.ui.View(SelectRole(ctx))
    await ctx.respond("Select which role to mention when there is a free game to claim", view=view, ephemeral=True)


@commands.has_permissions(administrator=True)
@bot.slash_command(description="Change the bot's nickname in this server")
async def nickname(ctx: discord.ApplicationContext, nick: str) -> None:
    await ctx.me.edit(nick=nick)
    await ctx.respond("Server nickname changed.", ephemeral=True)


@commands.has_permissions(administrator=True)
@bot.slash_command(description="Send a message that can grant users the mentioned role for game deals")
async def role_assign(ctx: discord.ApplicationContext) -> None:
    message: discord.Message = await ctx.send("React ??? to this message to get mentioned when game deals are available!")
    await message.add_reaction("???")
    await ctx.respond("Reaction message sent.", ephemeral=True)

    # Add message ID to database
    database.cursor.execute("UPDATE channels SET role_message_id = ? WHERE id = ?",
                            (message.id, ctx.channel_id))
    database.connection.commit()


@bot.event
async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent) -> None:
    if reaction.user_id == bot.user.id:
        return

    database.cursor.execute("SELECT role_id, role_message_id FROM channels WHERE id = ?", (reaction.channel_id,))
    role_id, role_message_id = database.cursor.fetchone()

    if reaction.message_id == role_message_id:
        guild_role = bot.get_guild(reaction.guild_id).get_role(role_id)
        await reaction.member.add_roles(guild_role)


@bot.event
async def on_raw_reaction_remove(reaction: discord.RawReactionActionEvent) -> None:
    database.cursor.execute("SELECT role_id, role_message_id FROM channels WHERE id = ?", (reaction.channel_id,))
    role_id, role_message_id = database.cursor.fetchone()

    if reaction.message_id == role_message_id:
        guild = bot.get_guild(reaction.guild_id)
        member = guild.get_member(reaction.user_id)
        guild_role = guild.get_role(role_id)

        await member.remove_roles(guild_role)


@bot.event
async def on_ready() -> None:
    print(f"{functions.get_current_date_time()} Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for free games"))
    main_loop.start()


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException) -> None:
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"??? This command is currently on cooldown. Please try again in {round(error.retry_after)}s.",
                          ephemeral=True)


bot.run(DISCORD_BOT_TOKEN)

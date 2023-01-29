import discord

import database
import functions


class SelectStores(discord.ui.Select):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx

        # Get stores from DB
        stores = functions.get_stores()

        # Get selected stores from DB
        selected_store_ids = functions.get_selected_store_ids(ctx.channel_id)

        options = [
            discord.SelectOption(
                value=store[0],
                label=store[1],
                default=store[0] in selected_store_ids
            ) for store in stores
        ]

        super().__init__(
            placeholder="Select stores",
            options=options,
            min_values=1,
            max_values=len(options)
        )

    async def callback(self, interaction: discord.InteractionResponse):
        database.cursor.execute("DELETE FROM channel_stores WHERE channel_id = ?", (self.ctx.channel_id,))
        for value in self.values:
            database.cursor.execute("INSERT INTO channel_stores VALUES (?, ?)", (self.ctx.channel_id, value))
        database.connection.commit()

        await interaction.response.send_message("Your changes have been saved.")


class DealButton(discord.ui.Button):
    def __init__(self, game):
        super().__init__(
            label="Get the game!",
            style=discord.ButtonStyle.link,
            url=functions.get_deal_url(game)
        )


class SelectRole(discord.ui.Select):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx
        self.roles = ctx.guild.roles

        self.roles = [role for role in self.roles if role.name != "@everyone"]

        options = [
            discord.SelectOption(
                value=str(role.id),
                label=role.name,
            ) for role in self.roles
        ]

        super().__init__(
            placeholder="Select role",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.InteractionResponse):
        database.cursor.execute("UPDATE channels SET role_id = ? WHERE id = ?", (self.values[0], self.ctx.channel_id))
        database.connection.commit()

        await interaction.response.send_message("Your changes have been saved.", ephemeral=True)

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
                label=store[1],
                value=store[0],
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

        await interaction.response.send_message("Your changes have been saved.", ephemeral=True)


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
        options = [discord.SelectOption(label="None (don't ping any role)", value="none")]
        for role in self.roles:
            options.append(
                discord.SelectOption(
                    label=role.name,
                    value=str(role.id)
                )
            )

        super().__init__(
            placeholder="Select role",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.InteractionResponse):
        role_id = self.values[0] if self.values[0] != "none" else None

        # Insert row if it doesn't exist (register the channel)
        database.cursor.execute("INSERT OR IGNORE INTO channels (id, guild_id, role_id) VALUES (?, ?, ?)",
                                (self.ctx.channel_id, self.ctx.guild_id, role_id))

        database.cursor.execute("UPDATE channels SET role_id = ? WHERE id = ?", (role_id, self.ctx.channel_id))
        database.connection.commit()

        if role_id:
            await interaction.response.send_message(f"{self.ctx.bot.user.name} will now mention your selected role "
                                                    f"when sending free games.",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(f"{self.ctx.bot.user.name} will not ping anyone when sending "
                                                    f"free games.", ephemeral=True)

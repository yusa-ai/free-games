import discord

import database


class SelectStores(discord.ui.Select):
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx

        # Get stores from DB
        database.cursor.execute("SELECT * FROM stores ORDER BY name")
        stores = database.cursor.fetchall()

        # Get selected stores from DB
        database.cursor.execute("SELECT store_id FROM channel_stores WHERE channel_id = ?", (ctx.channel_id,))
        selected_store_ids = database.cursor.fetchall()
        selected_store_ids = [tpl[0] for tpl in selected_store_ids]

        options = [
            discord.SelectOption(
                value=store[0],
                label=store[1],
                default=store[0] in selected_store_ids
            ) for store in stores
        ]

        super().__init__(
            placeholder="Stores",
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

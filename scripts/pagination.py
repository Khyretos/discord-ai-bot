# Source - https://stackoverflow.com/a
# Posted by Hazzu, modified by community. See post 'Timeline' for change history
# Retrieved 2026-01-23, License - CC BY-SA 4.0

from typing import Callable, Optional

import discord


class Pagination(discord.ui.View):
    def __init__(
        self,
        interaction: discord.Interaction,
        get_page: Callable,
        generate_chat_response: Callable,
    ):
        self.interaction = interaction
        self.get_page = get_page
        self.generate_chat_response = generate_chat_response
        self.total_pages: Optional[int] = None
        self.index = 1
        super().__init__(timeout=100)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680,
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navegate(
        self,
    ):
        emb, self.total_pages = await self.get_page(self.index)

        self.update_buttons()
        await self.interaction.followup.send(embed=emb, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        if self.total_pages == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True
            self.children[2].disabled = True
        elif self.index > self.total_pages // 2:
            self.children[2].emoji = "⏮️"
        else:
            self.children[2].emoji = "⏭️"
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == self.total_pages

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def end(self, interaction: discord.Interaction, button: discord.Button):
        if self.index <= self.total_pages // 2:
            self.index = self.total_pages
        else:
            self.index = 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="↩️", style=discord.ButtonStyle.blurple)
    async def retry(self, interaction: discord.Interaction, button: discord.Button):
        embeds = interaction.message.embeds
        for embed in embeds:
            for field in embed.fields:
                if field.name == "Question":
                    print(field.value)
                    await self.generate_chat_response(interaction, field.value)

        # await self.edit_page(interaction)

    async def on_timeout(self):
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(total_results: int, results_per_page: int) -> int:
        return ((total_results - 1) // results_per_page) + 1

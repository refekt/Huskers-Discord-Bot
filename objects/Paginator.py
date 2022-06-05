import discord
from typing import List
from collections import deque


class EmbedPaginatorView(discord.ui.View):
    def __init__(self, embeds: List[discord.Embed], timeout: int = None):
        self._embeds = embeds
        self._queue = deque(embeds)  # collections.deque
        self._initial = embeds[0]
        self._len = len(embeds)

        super().__init__(timeout=timeout)

    @discord.ui.button(emoji="\N{LEFTWARDS BLACK ARROW}")
    async def previous_embed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self._queue.rotate(1)
        embed = self._queue[0]
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(emoji="\N{BLACK RIGHTWARDS ARROW}")
    async def next_embed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self._queue.rotate(-1)
        embed = self._queue[0]
        await interaction.response.edit_message(embed=embed)

    @property
    def initial(self) -> discord.Embed:
        return self._initial

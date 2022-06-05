from collections import deque
from typing import List

import discord


class EmbedPaginatorView(discord.ui.View):
    def __init__(self, embeds: List[discord.Embed], timeout: int = None) -> None:
        self._embeds = embeds
        self._queue = deque(embeds)  # collections.deque
        self._initial = embeds[0]
        self._len = len(embeds)
        self._current_index = 0

        super().__init__(timeout=timeout)

    def update_current_page(self):
        self._current_index = self._queue.index(self._queue[0])

        for button in self.children:
            if button.custom_id == "ud_current_page":
                button.label = f"Page {self._current_index}/{self._len}"
                break

    @discord.ui.button(emoji="\N{LEFTWARDS BLACK ARROW}", custom_id="ud_left")
    async def previous_embed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self._queue.rotate(1)
        embed = self._queue[0]
        self.update_current_page()
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(
        label="Page #/#",
        custom_id="ud_current_page",
        disabled=True,
        style=discord.ButtonStyle.grey,
    )
    async def current_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.update_current_page()

    @discord.ui.button(emoji="\N{BLACK RIGHTWARDS ARROW}", custom_id="ud_right")
    async def next_embed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self._queue.rotate(-1)
        embed = self._queue[0]
        self.update_current_page()
        await interaction.response.edit_message(embed=embed)

    @property
    def initial(self) -> discord.Embed:
        return self._initial

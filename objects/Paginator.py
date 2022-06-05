import logging
from collections import deque
from typing import List

import discord

logger = logging.getLogger(__name__)


class EmbedPaginatorView(discord.ui.View):
    def __init__(
        self,
        embeds: List[discord.Embed],
        response: discord.InteractionMessage,
        timeout: int = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self._embeds: List[discord.Embed] = embeds
        self._queue = deque(embeds)  # collections.deque
        self._initial: discord.Embed = embeds[0]
        self._len: int = len(embeds)
        self.current_index: int = 1
        self.response: discord.InteractionMessage = response

        try:
            self.add_item(
                discord.ui.Button(
                    label=f"Page {self.current_index}/{self._len}",
                    custom_id="ud_current_page",
                    disabled=True,
                    style=discord.ButtonStyle.grey,
                )
            )
        except (TypeError, ValueError) as e:
            logger.exception(f"Error creating ud_current_page button: {e}")

    async def update_current_page(self):
        logger.info(f"Current index is: {self.current_index}")

        for button in self.children:
            if button.custom_id == "ud_current_page":
                button.label = f"Page {self.current_index}/{self._len}"
                break
        await self.response.edit(view=self)

    @discord.ui.button(emoji="\N{LEFTWARDS BLACK ARROW}", custom_id="ud_left")
    async def previous_embed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        logger.info("Going to previous embed")
        self._queue.rotate(1)
        if self.current_index == 1:
            self.current_index = len(self._queue)
        else:
            self.current_index -= 1
        await self.update_current_page()

        embed = self._queue[0]
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(emoji="\N{BLACK RIGHTWARDS ARROW}", custom_id="ud_right")
    async def next_embed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        logger.info("Going to next embed")
        self._queue.rotate(-1)
        if self.current_index == len(self._queue):
            self.current_index = 1
        else:
            self.current_index += 1
        await self.update_current_page()

        embed = self._queue[0]
        await interaction.response.edit_message(embed=embed)

    @property
    def initial(self) -> discord.Embed:
        return self._initial

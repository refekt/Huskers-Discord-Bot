import logging
from collections import deque
from typing import List

import discord

from helpers.constants import GLOBAL_TIMEOUT
from objects.Logger import discordLogger, is_debugging

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

__all__: list[str] = ["EmbedPaginatorView"]


class EmbedPaginatorView(discord.ui.View):
    __slots__ = [
        "_embeds",
        "_initial",
        "_len",
        "_queue",
        "children",
        "current_index",
        "id",
        "response",
        "timeout",
    ]

    def __init__(
        self,
        embeds: List[discord.Embed],
        original_message: discord.InteractionMessage,
        timeout: int = GLOBAL_TIMEOUT,
    ) -> None:
        """

        :param embeds:
        :param original_message:
        :param timeout:
        """
        super().__init__(timeout=timeout)
        self._embeds: List[discord.Embed] = embeds
        self._queue = deque(embeds)  # collections.deque
        self._initial: discord.Embed = embeds[0]
        self._len: int = len(embeds)
        self.current_index: int = 1
        self.response: discord.InteractionMessage = original_message
        self.timeout: int = timeout

        try:  # TODO Make this show up in the middle.
            self.add_item(
                discord.ui.Button(
                    label=f"Page {self.current_index}/{self._len}",
                    custom_id="ud_current_page",
                    disabled=True,
                    style=discord.ButtonStyle.grey,
                )
            )
        except (TypeError, ValueError) as e:
            logger.exception(
                f"Error creating ud_current_page button: {e}", exc_info=True
            )
        self.children: discord.Button | discord.ui.Item = self._children

    async def update_current_page(self) -> None:
        logger.debug(f"Current index is: {self.current_index}")

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

        embed: discord.Embed = self._queue[0]
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(emoji="\N{BLACK RIGHTWARDS ARROW}", custom_id="ud_right")
    async def next_embed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        logger.debug("Going to next embed")
        self._queue.rotate(-1)
        if self.current_index == len(self._queue):
            self.current_index = 1
        else:
            self.current_index += 1
        await self.update_current_page()

        embed: discord.Embed = self._queue[0]
        await interaction.response.edit_message(embed=embed)

    @property
    def initial(self) -> discord.Embed:
        return self._initial


logger.info(f"{str(__name__).title()} module loaded!")

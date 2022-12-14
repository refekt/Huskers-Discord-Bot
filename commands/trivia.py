import logging

import discord
from discord import app_commands
from discord.app_commands import Group
from discord.ext import commands

from helpers.constants import GUILD_PROD
from objects.Logger import discordLogger, is_debugging
from objects.Trivia import (
    TriviaBot,
    TriviaCategories,
    TriviaDifficulty,
    TriviaQuestionType,
)

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

__all__ = []


class TriviaCommands(commands.Cog, name="Trivia Commands"):
    bet_trivia: Group = app_commands.Group(
        name="trivia", description="Trivia commands", guild_ids=[GUILD_PROD]
    )

    @bet_trivia.command(name="start", description="Start a trivia game!")
    @app_commands.describe(
        category="The category for the trivia game",
        difficulty="Difficulty of the trivia game",
        question_type="Multiple choice or True/False questions",
        question_amount="Number of questions to ask",
    )
    async def trivia_start(
            self,
            interaction: discord.Interaction,
            category: TriviaCategories,
            difficulty: TriviaDifficulty,
            question_type: TriviaQuestionType,
            question_amount: int = 3 if is_debugging() else 10,
    ):
        trivia_bot: TriviaBot = TriviaBot(
            game_master=interaction.user,
            channel=interaction.channel,
            category=category,
            difficulty=difficulty,
            question_type=question_type,
            question_amount=question_amount,
        )

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Game started! You can dismiss this message.")

        await trivia_bot.start_game()

    async def trivia_leaderboard(self, interaction: discord.Interaction) -> None:
        pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TriviaCommands(bot), guilds=[discord.Object(id=GUILD_PROD)])


logger.info(f"{str(__name__).title()} module loaded!")

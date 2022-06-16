# https://gist.github.com/AbstractUmbra/a9c188797ae194e592efe05fa129c57f
# https://discordpy.readthedocs.io/en/latest/interactions/api.html#discord.Interaction

import discord
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD
from objects.Logger import discordLogger

logger = discordLogger(__name__)


class MyCog(commands.Cog):
    # for simplicity, these commands are all global. You can add `guild=` or `guilds=` to `Bot.add_cog` in `setup` to add them to a guild.
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required in this context.

    group_example = app_commands.Group(name="example-command", description="TBD")

    @group_example.command(name="sub-command")
    async def sub_command(self, interaction: discord.Interaction) -> None:
        """/example-command sub-command"""
        ...

    @app_commands.command(name="command-1", description="Descript #1")
    @app_commands.describe(
        example="Description for example variable"
    )  # Typos here will cause the cog not to load
    @app_commands.guilds(GUILD_PROD)
    @app_commands.default_permissions(
        administrator=True
    )  # https://discordpy.readthedocs.io/en/latest/api.html#discord.Permissions
    async def my_command(self, interaction: discord.Interaction, example: str) -> None:
        """/command-1"""
        await interaction.response.send_message("Hello from command 1!", ephemeral=True)

    @app_commands.command(name="command-2")
    @app_commands.guilds(discord.Object(id=...), ...)
    async def my_private_command(self, interaction: discord.Interaction) -> None:
        """/command-2"""
        await interaction.response.send_message(
            "Hello from private command!", ephemeral=True
        )

    @app_commands.command(name="sub-1")
    async def my_sub_command_1(self, interaction: discord.Interaction) -> None:
        """/parent sub-1"""
        await interaction.response.defer(
            ephemeral=True
        )  # Send a private/hidden thinking message

        # Do some work...

        await interaction.followup.send(
            "Hello from sub command 1",
        )

    @app_commands.command(name="sub-2")
    async def my_sub_command_2(self, interaction: discord.Interaction) -> None:
        """/parent sub-2"""
        await interaction.response.send_message(
            "Hello from sub command 2", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyCog(bot), guilds=[discord.Object(id=GUILD_PROD)])

# https://gist.github.com/AbstractUmbra/a9c188797ae194e592efe05fa129c57f

import discord
from discord import app_commands
from discord.ext import commands


class MyCog(commands.Cog):
    # for simplicity, these commands are all global. You can add `guild=` or `guilds=` to `Bot.add_cog` in `setup` to add them to a guild.
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required in this context.

    @app_commands.command(name="command-1")
    async def my_command(self, interaction: discord.Interaction) -> None:
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
        await interaction.response.send_message(
            "Hello from sub command 1", ephemeral=True
        )

    @app_commands.command(name="sub-2")
    async def my_sub_command_2(self, interaction: discord.Interaction) -> None:
        """/parent sub-2"""
        await interaction.response.send_message(
            "Hello from sub command 2", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyCog(bot))
    # or if you want guild/guilds only...
    # await bot.add_cog(MyCog(bot), guilds=[discord.Object(id=...)])

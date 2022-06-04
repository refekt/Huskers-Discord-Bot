# TODO
# * Eightball
# * Markov
# * Police
# * Possumdroppings
# * Survey
# * Urbandictionary
# * Vote
# * Weather
# TODO


import random

import discord.ext.commands
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD
from helpers.embed import buildEmbed


class TextCog(commands.Cog, name="Text Commands"):
    @app_commands.command(
        name="eightball", description="Ask the Magic 8-Ball a question"
    )
    @app_commands.guilds(GUILD_PROD)
    async def eightball(self, interaction: discord.Interaction, question: str):
        responses = [
            "As I see it, yes.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Coach V's cigar would like this!",
            "Concentrate and ask again.",
            "Definitely yes!",
            "Don’t count on it...",
            "Frosty!",
            "Fuck Iowa!",
            "It is certain.",
            "It is decidedly so.",
            "Most likely...",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good and reply hazy",
            "Scott Frost approves!",
            "These are the affirmative answers.",
            "Try again...",
            "Without a doubt.",
            "Yes – definitely!",
            "You may rely on it.",
        ]

        reply = random.choice(responses)
        embed = buildEmbed(
            title="Eight Ball Response",
            description="These are all 100% accurate. No exceptions! Unless an answer says anyone other than Nebraska is good.",
            fields=[
                dict(name="Question Asked", value=question.capitalize(), inline=False),
                dict(name="Response", value=reply, inline=False),
            ],
        )
        await interaction.response.send_message(embed=embed)

    @commands.command()
    async def markov(self, interaction: discord.Interaction):
        ...

    @commands.command()
    async def police(self, interaction: discord.Interaction):
        ...

    @commands.command()
    async def possum(self, interaction: discord.Interaction):
        ...

    @commands.command()
    async def survey(self, interaction: discord.Interaction):
        ...

    @commands.command()
    async def urbandictionary(self, interaction: discord.Interaction):
        ...

    @commands.command()
    async def weather(self, interaction: discord.Interaction):
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TextCog(bot), guilds=[discord.Object(id=GUILD_PROD)])

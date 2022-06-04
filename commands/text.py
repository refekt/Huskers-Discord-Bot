import logging
import random
import re

import discord.ext.commands
import markovify
from discord import app_commands, Forbidden, HTTPException
from discord.ext import commands

from helpers.constants import GUILD_PROD, CHAN_BANNED
from helpers.embed import buildEmbed

logger = logging.getLogger(__name__)


class TextCog(commands.Cog, name="Text Commands"):
    @app_commands.command(
        name="eightball", description="Ask the Magic 8-Ball a question"
    )
    @app_commands.describe(question="The question you want to ask the Magic 8-Ball")
    @app_commands.guilds(GUILD_PROD)
    async def eightball(self, interaction: discord.Interaction, question: str) -> None:
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

    @app_commands.command(
        name="markov",
        description="Generate an AI-created message from the server's messages!",
    )
    @app_commands.describe(
        source_channel="A Discord text channel you want to use as a source",
        source_member="A Discord server member you want to use as a source",
    )
    @app_commands.guilds(GUILD_PROD)
    async def markov(
        self,
        interaction: discord.Interaction,
        source_channel: discord.TextChannel = None,
        source_member: discord.Member = None,
    ) -> None:
        await interaction.response.defer()

        channel_history_limit: int = 1000
        combined_sources: list = []
        message_history: list = []
        source_conent: str = ""

        if source_channel is not None:
            combined_sources.append(source_channel)

        if source_member is not None:
            combined_sources.append(source_member)

        def check_message(message: discord.Message) -> str:
            if (
                message.channel.id in CHAN_BANNED
                or message.author.bot
                or message.content is ""
            ):
                return ""

            return f"\n{message.content.capitalize()}"

        def cleanup_source_conent(check_source_conent: str) -> str:
            output = check_source_conent

            regex_discord_http = [
                r"(<@\d{18}>|<@!\d{18}>|<:\w{1,}:\d{18}>|<#\d{18}>)",  # All Discord mentions
                r"((Http|Https|http|ftp|https)://|)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",  # All URLs
            ]

            for regex in regex_discord_http:
                output = re.sub(regex, "", output, flags=re.IGNORECASE)

            regex_new_lines = r"(\r\n|\r|\n){1,}"  # All line breaks
            output = re.sub(regex_new_lines, "", output, flags=re.IGNORECASE)

            regex_multiple_whitespace = r"\s{2,}"
            output = re.sub(regex_multiple_whitespace, "", output, flags=re.IGNORECASE)

            return output

        if not combined_sources:  # Nothing was provided
            try:
                message_history = [
                    message
                    async for message in interaction.channel.history(
                        limit=channel_history_limit
                    )
                ]
            except (Forbidden, HTTPException) as e:
                logger.exception(f"Unable to collect message history!\n{e}")

            for message in message_history:
                source_conent += check_message(message)
        else:
            for source in combined_sources:
                if type(source) == discord.Member:
                    message_member_history = [
                        message
                        async for message in interaction.channel.history(
                            limit=channel_history_limit
                        )
                    ]
                    for message in message_member_history:
                        if message.author == source:
                            source_conent += check_message(message)
                elif type(source) == discord.TextChannel:
                    ...
                else:
                    logger.exception("Unexpected source type!")
                    continue

        if not source_conent == "":
            source_conent = cleanup_source_conent(source_conent)
        else:
            logger.exception(
                f"There was not enough information available to make a Markov chain.",
            )

        markvov_response = markovify.NewlineText(source_conent, well_formed=True)
        markov_output = markvov_response.make_sentence(
            max_overlap_ratio=0.9, max_overlap_total=27, min_words=7, tries=100
        )

        if markov_output is None:
            logger.exception("Markovify failed to create an output!")
        else:
            await interaction.response.send_message(source_conent)

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

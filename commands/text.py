import json
import random
import re
from datetime import timedelta, datetime
from typing import List, Optional, Union

import discord.ext.commands
import markovify
import requests
from bs4 import BeautifulSoup
from discord import app_commands, Forbidden, HTTPException
from discord.ext import commands

from helpers.constants import (
    CHAN_BANNED,
    CHAN_POSSUMS,
    DT_OPENWEATHER_UTC,
    GLOBAL_TIMEOUT,
    GUILD_PROD,
    HEADERS,
    TZ,
    US_STATES,
    WEATHER_API_KEY,
)
from helpers.embed import buildEmbed
from objects.Exceptions import CommandException, WeatherException, TextException
from objects.Logger import discordLogger
from objects.Paginator import EmbedPaginatorView
from objects.Survey import Survey
from objects.Weather import WeatherResponse, WeatherHour

logger = discordLogger(__name__)


class TextCog(commands.Cog, name="Text Commands"):
    @app_commands.command(
        name="eightball", description="Ask the Magic 8-Ball a question"
    )
    @app_commands.describe(question="The question you want to ask the Magic 8-Ball")
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
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
                dict(
                    name="Question Asked",
                    value=question.capitalize(),
                ),
                dict(
                    name="Response",
                    value=reply,
                ),
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
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def markov(
        self,
        interaction: discord.Interaction,
        source_channel: discord.TextChannel = None,
        source_member: discord.Member = None,
    ) -> None:
        logger.info("Attempting to create a markov chain")

        await interaction.response.defer(thinking=True)

        channel_history_limit: int = 1000
        combined_sources: list = []
        message_history: list = []
        source_content: str = ""
        message_channel_history: list[Optional[discord.Message]] = [None]
        message_member_history: list[Optional[discord.Message]] = [None]

        if source_channel is not None:
            if source_channel.id in CHAN_BANNED:
                raise TextException(
                    f"You cannot use this command with {source_channel.mention}!"
                )
            logger.info("Adding channel to sources")
            combined_sources.append(source_channel)

        if source_member is not None:
            logger.info("Adding member to sources")
            combined_sources.append(source_member)

        def check_message(message: discord.Message) -> str:
            if (
                message.channel.id in CHAN_BANNED
                or message.author.bot
                or message.content == ""
            ):
                return ""

            return f"\n{message.content.capitalize()}"

        def cleanup_source_content(check_source_content: str) -> str:
            logger.info("Cleaning source content")
            output = check_source_content

            regex_discord_http = [
                r"(<@\d{18}>|<@!\d{18}>|<:\w{1,}:\d{18}>|<#\d{18}>)",  # All Discord mentions
                r"((Http|Https|http|ftp|https)://|)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",  # All URLs
            ]

            for regex in regex_discord_http:
                output = re.sub(regex, "", output, flags=re.IGNORECASE)

            regex_new_lines = r"(\r\n|\r|\n){1,}"  # All line breaks
            output = re.sub(regex_new_lines, "\n", output, flags=re.IGNORECASE)

            regex_multiple_whitespace = r"\s{2,}"
            output = re.sub(regex_multiple_whitespace, "", output, flags=re.IGNORECASE)

            logger.info("Source content cleaned")
            return output

        if not combined_sources:  # Nothing was provided
            logger.info("No sources provided")
            try:
                message_history = [
                    message
                    async for message in interaction.channel.history(
                        limit=channel_history_limit
                    )
                ]
            except (Forbidden, HTTPException) as e:
                raise TextException(f"Unable to collect message history!\n{e}")

            for message in message_history:
                source_content += check_message(message)
            logger.info("Compiled message content from current channel")
        else:
            logger.info("A source was provided")
            for source in combined_sources:
                if type(source) == discord.Member:
                    logger.info("Discord member source provided")
                    message_member_history = [
                        message
                        async for message in interaction.channel.history(
                            limit=channel_history_limit
                        )
                    ]
                    for message in message_member_history:
                        if message.author == source:
                            source_content += check_message(message)
                    logger.info("Discord member source compiled")
                elif type(source) == discord.TextChannel:
                    logger.info("Discord text channel source provided")
                    message_channel_history = [
                        message
                        async for message in source.history(limit=channel_history_limit)
                    ]
                    for message in message_channel_history:
                        source_content += check_message(message)
                    logger.info("Discord text channel source compiled")
                else:
                    logger.error("Unexpected source type!", exc_info=True)
                    continue

        if not source_content == "":
            source_content = cleanup_source_content(source_content)
        else:
            raise TextException(
                f"There was not enough information available in {[source.mention for source in combined_sources]} to make a Markov chain."
            )

        logger.info("Cleaning up variables")
        del (
            message_channel_history,
            message_history,
            message_member_history,
        )

        logger.info("Creating a markov chain")
        markov_response = markovify.NewlineText(source_content, well_formed=True)
        logger.info("Creating a markov original_message")
        markov_output = markov_response.make_sentence(
            max_overlap_ratio=0.9, max_overlap_total=27, min_words=7, tries=100
        )

        if not combined_sources:
            source_name: Union[discord.Member, discord.Text] = (
                interaction.channel.name.replace("-", " ").title().replace(" ", "-")
            )
        else:
            source_name = (
                source_member.name.replace("-", " ").title().replace(" ", "-")
                if source_member
                else source_channel.name.replace("-", " ").title().replace(" ", "-")
            )

        if markov_output is None:
            raise TextException(
                "Markovify failed to create an output! Mor than likely, there is not enough source material available to create a markov chain."
            )
        else:
            embed = buildEmbed(
                title="",
                author=f"{interaction.user.display_name} ({interaction.user.name}#{interaction.user.discriminator})",
                icon_url=interaction.user.avatar.url,
                footer=f"Markov chain crated by Bot Frost",
                fields=[
                    dict(
                        name=f"{source_name} said...",
                        value=markov_output,
                    )
                ],
            )

            if interaction.response.is_done():
                await interaction.edit_original_message(embed=embed)
            else:
                await interaction.channel.send(embed=embed)
            logger.info("Markov out sent")

    @app_commands.command(
        name="police",
        description="Arrest a server member!",
    )
    @app_commands.describe(
        arrestee="A Discord member you want to arrest",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def police(
        self, interaction: discord.Interaction, arrestee: discord.Member
    ) -> None:
        embed = buildEmbed(
            title="Wee woo, wee woo!",
            fields=[
                dict(
                    name="Halt!",
                    value=f"**"
                    f"🚨 NANI 🚨\n"
                    f"..🚨 THE 🚨\n"
                    f"...🚨 FUCK 🚨\n"
                    f"....🚨 DID 🚨\n"
                    f".....🚨 YOU 🚨\n"
                    f"....🚨 JUST 🚨\n"
                    f"...🚨 SAY 🚨\n"
                    f"..🚨 {arrestee.mention} 🚨\n"
                    f"🚨🚨🚨🚨🚨🚨🚨🚨\n"
                    f"\n"
                    f"👮‍📢 Information ℹ provided in the VIP 👑 Room 🏆 is intended for Husker247 🌽🎈 members only ‼🔫. Please do not copy ✏ and paste 🖨 or summarize this content elsewhere‼ Please try to keep all replies in this thread 🧵 for Husker247 members only! 🚫 ⛔ 👎 "
                    f"🙅‍♀️Thanks for your cooperation. 😍🤩😘"
                    f"**",
                )
            ],
        )
        await interaction.response.send_message(content=arrestee.mention, embed=embed)

    @app_commands.command(
        name="possum",
        description="The message you want to pass along for the possum",
    )
    @app_commands.describe(
        message="Share possum droppings for to the server",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def possum(self, interaction: discord.Interaction, message: str) -> None:
        # assert interaction.channel.id == CHAN_POSSUMS, CommandException(
        #     "You can only use this in the possum droppings channel!"
        # )
        assert message, CommandException("You cannot have an empty message!")

        await interaction.response.defer(ephemeral=True)

        embed = buildEmbed(
            title="Possum Droppings",
            thumbnail="https://cdn.discordapp.com/attachments/593984711706279937/875162041818693632/unknown.jpeg",
            footer="Created by a sneaky possum",
            fields=[
                dict(
                    name="Dropping",
                    value=message,
                )
            ],
        )
        chan = await interaction.client.fetch_channel(CHAN_POSSUMS)
        await chan.send(embed=embed)

    @app_commands.command(
        name="urban-dictionary",
        description="Look up a word on Urban Dictionary",
    )
    @app_commands.describe(
        word="The word to look up",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def urban_dictionary(
        self, interaction: discord.Interaction, word: str
    ) -> None:
        await interaction.response.defer()

        class UrbanDictDefinition:
            def __init__(self, lookup_word, meaning, example, contributor) -> None:
                self.lookup_word = lookup_word
                self.meaning = meaning
                self.example = example
                self.contributor = contributor

        r = requests.get(f"https://www.urbandictionary.com/define.php?term={word}")
        soup = BeautifulSoup(r.content, features="html.parser")

        try:
            definitions = soup.find_all(
                name="div", attrs={"class": re.compile("definition.*")}
            )
        except AttributeError:
            raise TextException(f"Unable to find [{word}] in the Urban Dictionary.")

        assert definitions, CommandException(
            f"Unable to find [{word}] in the Urban Dictionary."
        )

        del r, soup

        results = []
        for definition in definitions:
            results.append(
                UrbanDictDefinition(
                    lookup_word=definition.contents[0].contents[0].text,
                    meaning=definition.contents[0].contents[1].text,
                    example=definition.contents[0].contents[2].text,
                    contributor=definition.contents[0].contents[3].text,
                )
            )

        pages = []
        for index, result in enumerate(results):
            pages.append(
                buildEmbed(
                    title=f"Searched for: {result.lookup_word}",
                    description=f"Definition #{index + 1} from Urban Dictionary",
                    fields=[
                        dict(
                            name="Meaning",
                            value=result.meaning,
                        ),
                        dict(
                            name="Example",
                            value=result.example,
                        ),
                        dict(
                            name="Contributor",
                            value=result.contributor,
                        ),
                    ],
                )
            )

        view = EmbedPaginatorView(
            embeds=pages, original_message=await interaction.original_message()
        )
        await interaction.edit_original_message(embed=view.initial, view=view)

    @app_commands.command(
        name="survey",
        description="Create a survey for the server",
    )
    @app_commands.describe(
        question="The question you want to ask",
        options="A maximum of three space deliminated set of options; e.g., 'one two three'",
        timeout="Number of seconds to run the survey.",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def survey(
        self,
        interaction: discord.Interaction,
        question: str,
        options: str,
        timeout: int = GLOBAL_TIMEOUT,
    ) -> None:
        survey = Survey(
            client=interaction.client,
            interaction=interaction,
            question=question,
            options=options,
            timeout=timeout,
        )
        await survey.send()

    @app_commands.command(
        name="weather",
        description="Show the weather for a given location",
    )
    @app_commands.describe(
        city="The name of the city you are searching",
        state="The name of the states the city is in",
        country="The two digit abbreviation of the country the state is in",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def weather(
        self,
        interaction: discord.Interaction,
        city: str,
        state: str,
        country: str = "US",
    ) -> None:
        await interaction.response.defer()

        try:
            formatted_state = next(
                (
                    search_state
                    for search_state in US_STATES
                    if (
                        search_state["State"].lower() == state.lower()
                        or search_state["Abbrev"][:-1].lower() == state.lower()
                        or search_state["Code"].lower() == state.lower()
                    )
                ),
                None,
            )
        except StopIteration:
            raise WeatherException("Unable to find state. Please try again!")

        def shift_utc_tz(dt, shift: int) -> datetime:
            return dt + timedelta(seconds=shift)

        weather_url = f"https://api.openweathermap.org/data/2.5/weather?appid={WEATHER_API_KEY}&units=imperial&lang=en&q={city},{formatted_state['Code']},{country}"
        response = requests.get(weather_url, headers=HEADERS)
        j = json.loads(response.content)

        weather = WeatherResponse(j)
        if weather.cod == "404":
            raise WeatherException(
                f"Unable to find {city.title()}, {state}. Try again!"
            )

        temp_str = (
            f"Temperature: {weather.main.temp}℉\n"
            f"Feels Like: {weather.main.feels_like}℉\n"
            f"Humidity: {weather.main.humidity}%\n"
            f"Max: {weather.main.temp_max}℉\n"
            f"Min: {weather.main.temp_min}℉"
        )

        if len(weather.wind) == 2:
            wind_str = (
                f"Speed: {weather.wind.speed} MPH\n" f"Direction: {weather.wind.deg} °"
            )
        elif len(weather.wind) == 3:
            wind_str = (
                f"Speed: {weather.wind.speed} MPH\n"
                f"Gusts: {weather.wind.gust} MPH\n"
                f"Direction: {weather.wind.deg} °"
            )
        else:
            wind_str = f"Speed: {weather.wind.speed} MPH"

        hourly_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={weather.coord.lat}&lon={weather.coord.lon}&appid={WEATHER_API_KEY}&units=imperial"
        response = requests.get(hourly_url, headers=HEADERS)
        j = json.loads(response.content)
        hours: List[WeatherHour] = []
        for index, item in enumerate(j["hourly"]):
            hours.append(WeatherHour(item))
            if index == 3:
                break

        hour_temp_str = ""
        hour_wind_str = ""
        for index, hour in enumerate(hours):
            if index < len(hours) - 1:
                hour_temp_str += f"{hour.temp}℉ » "
                hour_wind_str += f"{hour.wind_speed} MPH » "
            else:
                hour_temp_str += f"{hour.temp}℉"
                hour_wind_str += f"{hour.wind_speed} MPH"

        sunrise = shift_utc_tz(weather.sys.sunrise, weather.timezone)
        sunset = shift_utc_tz(weather.sys.sunset, weather.timezone)

        sun_str = (
            f"Sunrise: {sunrise.astimezone(tz=TZ).strftime(DT_OPENWEATHER_UTC)}\n"
            f"Sunset: {sunset.astimezone(tz=TZ).strftime(DT_OPENWEATHER_UTC)}"
        )

        embed = buildEmbed(
            title=f"Weather conditions for {city.title()}, {state.upper()}",
            description=f"It is currently {weather.weather[0].main} with {weather.weather[0].description}. {city.title()}, {state} is located at {weather.coord.lat}, {weather.coord.lon}.",
            fields=[
                dict(
                    name="Temperature",
                    value=temp_str,
                ),
                dict(
                    name="Clouds",
                    value=f"Coverage: {weather.clouds.all}%",
                ),
                dict(
                    name="Wind",
                    value=wind_str,
                ),
                dict(
                    name="Temp Next 4 Hours",
                    value=hour_temp_str,
                ),
                dict(
                    name="Wind Next 4 Hours",
                    value=hour_wind_str,
                ),
                dict(
                    name="Sun",
                    value=sun_str,
                ),
            ],
            thumbnail=f"https://openweathermap.org/img/wn/{weather.weather[0].icon}@4x.png",
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="hype-me",
        description="Get hype from Husk",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def hypeme(self, interaction: discord.Interaction) -> None:
        class Scroll:
            def __init__(self, message: str) -> None:
                self.header: str = "  _______________________\n=(__    ___      __     _)=\n  |                     |\n"
                self.message_layer: str = "  |                     |\n"
                self.signature: str = "\n  |   ~*~ Husk          |\n"
                self.footer: str = "  |                     |\n  |__    ___   __    ___|\n=(_______________________)=\n"
                self.max_line_len: int = 19
                self.message: str = message

            def compile(self) -> str:
                new_line: str = "\n"
                lines = [
                    f"  | {str(self.message[i: i + self.max_line_len]).ljust(self.max_line_len, ' ')} |"
                    for i in range(0, len(self.message), self.max_line_len)
                ]

                return f"{self.header}{new_line.join([line for line in lines])}{self.signature}{self.footer}"

        logger.info("Creating a Husk markov chain")
        await interaction.response.defer()

        with open("resources/husk_messages.txt", encoding="UTF-8") as f:
            source_data = f.read()

        text_model = markovify.NewlineText(source_data)

        output = (
            str(text_model.make_short_sentence(min_chars=20, max_chars=50))
            .lower()
            .capitalize()
        )

        processed_output = Scroll(output).compile()

        if not output == "None":
            await interaction.followup.send(f"```\n{processed_output}```")
            logger.info("Husk markov chain created!")
        else:
            await interaction.followup.send(
                "Unable to make a Husk Chain!", ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TextCog(bot), guilds=[discord.Object(id=GUILD_PROD)])

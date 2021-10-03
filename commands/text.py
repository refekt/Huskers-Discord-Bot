import json
import random
import re
from datetime import timedelta
from urllib import parse

import discord
import markovify
import requests
from bs4 import BeautifulSoup
from dinteractions_Paginator import Paginator
from discord.ext import commands
from discord_slash import ComponentContext, cog_ext
from discord_slash.context import SlashContext
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_actionrow, create_button
from discord_surveys.survey import Survey

from objects.Weather import WeatherHour, WeatherResponse
from utilities.constants import (
    CHAN_BANNED,
    CHAN_POSSUMS,
    CommandError,
    DT_OPENWEATHER_UTC,
    HEADERS,
    TZ,
    US_STATES,
    UserError,
    WEATHER_API_KEY,
    guild_id_list,
    set_component_key,
)
from utilities.embed import build_embed

buttons_ud = [
    create_button(
        style=ButtonStyle.gray, label="Previous", custom_id="ud_previous", disabled=True
    ),
    create_button(style=ButtonStyle.gray, label="Next", custom_id="ud_next"),
]


def ud_embed(embed_word, embed_meaning, embed_example, embed_contributor):
    return build_embed(
        title="Urban Dictionary Result",
        inline=False,
        footer=embed_contributor,
        fields=[
            [embed_word, embed_meaning],
            ["Example", embed_example],
            [
                "Link",
                f"https://www.urbandictionary.com/define.php?term={parse.quote(string=embed_word)}",
            ],
        ],
    )


def check_channel_or_message(
    check_member: discord.Member, check_message: discord.Message = None
):
    if check_message.content == "":
        return ""

    if check_message.channel.id in CHAN_BANNED:
        return ""

    if check_member.bot:
        return ""

    return "\n" + str(check_message.content.capitalize())


def cleanup_source_data(source_data: str):
    regex_strings = [
        r"(<@\d{18}>|<@!\d{18}>|<:\w{1,}:\d{18}>|<#\d{18}>)",  # All Discord mentions
        r"((Http|Https|http|ftp|https)://|)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",  # All URLs
    ]

    new_source_data = source_data

    for regex in regex_strings:
        new_source_data = re.sub(regex, "", new_source_data, flags=re.IGNORECASE)

    regex_new_line = r"(\r\n|\r|\n){1,}"  # All new lines
    new_source_data = re.sub(regex_new_line, "\n", new_source_data, flags=re.IGNORECASE)

    regex_front_new_line = r"^\n"
    new_source_data = re.sub(
        regex_front_new_line, "", new_source_data, flags=re.IGNORECASE
    )

    regex_multiple_whitespace = r"\s{2,}"
    new_source_data = re.sub(
        regex_multiple_whitespace, " ", new_source_data, flags=re.IGNORECASE
    )

    return new_source_data


# noinspection PyUnresolvedReferences
class TextCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class Definition:
        def __init__(self, lookup_word, meaning, example, contributor):
            self.lookup_word = lookup_word
            self.meaning = meaning
            self.example = example
            self.contributor = contributor

    @cog_ext.cog_slash(
        name="urbandictionary",
        description="Look up a word on Urban Dictionary",
        guild_ids=guild_id_list(),
    )
    async def _urbandictionary(self, ctx: SlashContext, *, word: str):
        r = requests.get(f"http://www.urbandictionary.com/define.php?term={word}")
        soup = BeautifulSoup(r.content, features="html.parser")

        try:
            definitions = soup.find_all(name="div", attrs={"class": "def-panel"})
        except AttributeError:
            raise UserError(f"Unable to find [{word}] in the Urban Dictionary.")

        del r, soup

        if len(definitions) == 0:
            raise UserError(f"Unable to find [{word}] in the Urban Dictionary.")

        try:
            del definitions[1]  # Word of the day
        except IndexError:
            pass

        results = []
        for definition in definitions:
            results.append(
                self.Definition(
                    lookup_word=definition.contents[1].contents[0].text,
                    meaning=definition.contents[2].text,
                    example=definition.contents[3].text,
                    contributor=definition.contents[4].text,
                )
            )

        pages = []
        for index, result in enumerate(results):
            pages.append(
                build_embed(
                    title=f"Searched for: {result.lookup_word}",
                    description=f"Definition #{index + 1} from Urban Dictionary",
                    fields=[
                        ["Meaning", result.meaning],
                        ["Example", result.example],
                        ["Contributor", result.contributor],
                    ],
                )
            )

        await Paginator(
            bot=ctx.bot,
            ctx=ctx,
            pages=pages,
            useIndexButton=True,
            useSelect=False,
            firstStyle=ButtonStyle.gray,
            nextStyle=ButtonStyle.gray,
            prevStyle=ButtonStyle.gray,
            lastStyle=ButtonStyle.gray,
            indexStyle=ButtonStyle.gray,
        ).run()

    @cog_ext.cog_slash(
        name="vote",
        description="Ask the community for their opinion in votes",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="query",
                description="What to vote on",
                option_type=3,
                required=True,
            ),
            create_option(
                name="option_a",
                description="Option A to vote on",
                option_type=3,
                required=False,
            ),
            create_option(
                name="option_b",
                description="Option b to vote on",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def _vote(
        self,
        ctx: SlashContext,
        query: str,
        option_a: str = "UP VOTE",
        option_b: str = "DOWN VOTE",
    ):
        if (option_a is not None and option_b is None) or (
            option_b is not None and option_a is None
        ):
            raise UserError("You must provide both options!")

        option_a = str(option_a).upper()
        option_b = str(option_b).upper()

        but_a = ButtonStyle.green
        but_b = ButtonStyle.red

        key = set_component_key()
        buttons_voting = []

        query = query.capitalize()
        if not query.endswith("?"):
            query += "?"

        if option_a != "UP VOTE" and option_b != "DOWN VOTE":  # Non-standard vote
            but_a = but_b = ButtonStyle.gray

        buttons_voting.append(
            create_button(custom_id=f"{key}_a", label=option_a, style=but_a)
        )
        buttons_voting.append(
            create_button(custom_id=f"{key}_b", label=option_b, style=but_b)
        )

        embed = build_embed(
            title=f"Q: {query}",
            inline=False,
            fields=[
                [buttons_voting[-2]["label"], "0"],
                [buttons_voting[-1]["label"], "0"],
                ["Voters", "_"],
            ],
            footer=key,
        )

        await ctx.send(
            content="", embed=embed, components=[create_actionrow(*buttons_voting)]
        )

    @cog_ext.cog_slash(
        name="markov",
        description="Attempts to create a meaningful sentence from old messages",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="channel",
                description="Discord text channel",
                option_type=7,
                required=False,
            ),
            create_option(
                name="member",
                description="Discord member",
                option_type=6,
                required=False,
            ),
        ],
    )
    async def _markov(self, ctx: SlashContext, channel=None, member=None):
        await ctx.defer()

        sources = []
        if channel is not None:
            sources.append(channel)

        if member is not None:
            sources.append(member)

        source_data = ""

        CHAN_HIST_LIMIT = 1000

        if not sources:  # Uses current channel for source data
            compiled_message_history = await ctx.channel.history(
                limit=CHAN_HIST_LIMIT
            ).flatten()  # potential discord vs discord_slash issue
            for message in compiled_message_history:
                source_data += check_channel_or_message(ctx.author, message)
        else:
            for source in sources:
                if (
                    type(source) == discord.Member
                ):  # Use current channel and source Discord Member
                    compiled_message_history = await ctx.channel.history(
                        limit=CHAN_HIST_LIMIT
                    ).flatten()
                    for message in compiled_message_history:
                        if message.author == source:
                            source_data += check_channel_or_message(
                                message.author, message
                            )
                elif type(source) == discord.TextChannel:
                    compiled_message_history = await source.history(
                        limit=CHAN_HIST_LIMIT
                    ).flatten()
                    for message in compiled_message_history:
                        source_data += check_channel_or_message(message.author, message)

        if not source_data == "":
            source_data = cleanup_source_data(source_data)
        else:
            await ctx.send(
                f"There was not enough information available to make a Markov chain."
            )

        chain = markovify.NewlineText(source_data, well_formed=True)
        markov_output = chain.make_sentence(
            max_overlap_ratio=0.9, max_overlap_total=27, min_words=7, tries=100
        )

        if markov_output is None:
            await ctx.send(f"Creating a Markov chain failed.")
        else:
            punctuation = ("!", ".", "?", "...")
            markov_output += random.choice(punctuation)
            await ctx.send(markov_output)

    @cog_ext.cog_slash(
        name="possumdroppings",
        description="Only the most secret and trustworthy drops",
        guild_ids=guild_id_list(),
    )
    async def _possumdroppings(self, ctx: SlashContext, message: str):
        await ctx.defer()

        if not ctx.channel_id == CHAN_POSSUMS:
            raise UserError(
                f"You can only use this command in [{ctx.guild.get_channel(CHAN_POSSUMS).mention}]"
            )

        await ctx.send("Thinking...", delete_after=0)

        embed = build_embed(
            title="Possum Droppings",
            inline=False,
            thumbnail="https://cdn.discordapp.com/attachments/593984711706279937/875162041818693632/unknown.jpeg",
            footer="Created by a possum",
            fields=[["Droppings", message]],
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="eightball",
        description="Ask the magic 8-ball a question",
        guild_ids=guild_id_list(),
    )
    async def _eightball(self, ctx: SlashContext, question: str):
        eight_ball = [
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

        random.shuffle(eight_ball)

        embed = build_embed(
            title="BotFrost Magic 8-Ball :8ball: says...",
            description="These are all 100% accurate. No exceptions! Unless an answer says anyone other than Nebraska is good.",
            inline=False,
            fields=[
                ["Question", question.capitalize()],
                ["Response", random.choice(eight_ball)],
            ],
            thumbnail="https://i.imgur.com/L5Gpu0z.png",
        )

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="police", description="You are under arrest!", guild_ids=guild_id_list()
    )
    async def _police(self, ctx: SlashContext, arestee: discord.Member):
        message = (
            f"**"
            f"🚨 NANI 🚨\n"
            f"..🚨 THE 🚨\n"
            f"...🚨 FUCK 🚨\n"
            f"....🚨 DID 🚨\n"
            f".....🚨 YOU 🚨\n"
            f"....🚨 JUST 🚨\n"
            f"...🚨 SAY 🚨\n"
            f"..🚨 {arestee.mention} 🚨\n"
            f"🏃‍♀️💨 🔫🚓🔫🚓🔫🚓\n"
            f"\n"
            f"👮‍📢 Information ℹ provided in the VIP 👑 Room 🏆 is intended for Husker247 🌽🎈 members only ‼🔫. Please do not copy ✏ and paste 🖨 or summarize this content elsewhere‼ Please try to keep all replies in this thread 🧵 for Husker247 members only! 🚫 ⛔ 👎 "
            f"🙅‍♀️Thanks for your cooperation. 😍🤩😘"
            f"**"
        )

        embed = build_embed(
            title="Wee woo wee woo!", inline=False, fields=[["Halt!", message]]
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="weather",
        description="Shows the weather for Husker games",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="city",
                description="City to search for",
                option_type=3,
                required=True,
            ),
            create_option(
                name="state",
                description="State to search. Format is two letter state code. AL, AK, AS, etc.",
                option_type=3,
                required=True,
            ),
            create_option(
                name="country",
                description="Country code",
                option_type=3,
                required=False,
            ),
        ],
    )
    async def _weather(
        self, ctx: SlashContext, city: str, state: str, country: str = "US"
    ):
        def shift_utc_tz(dt, shift):
            return dt + timedelta(seconds=shift)

        if not len(state) == 2:
            raise UserError("State input must be the two-digit state code.")

        found = False
        for item in US_STATES:
            if item.get("Code") == state.upper():
                found = True
                break
        if not found:
            raise UserError(
                f"Unable to find the state {state.upper()}. Please try again!"
            )

        weather_url = f"https://api.openweathermap.org/data/2.5/weather?appid={WEATHER_API_KEY}&units=imperial&lang=en&q={city},{state},{country}"
        response = requests.get(weather_url, headers=HEADERS)
        j = json.loads(response.content)

        weather = WeatherResponse(j)
        if weather.cod == "404":
            raise UserError(
                f"Unable to find {city.title()}, {state.upper()}. Try again!"
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
        hours = []
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

        embed = build_embed(
            title=f"Weather conditions for {city.title()}, {state.upper()}",
            description=f"It is currently {weather.weather[0].main} with {weather.weather[0].description}. {city.title()}, {state.upper()} is located at {weather.coord.lat}, {weather.coord.lon}.",
            fields=[
                ["Temperature", temp_str],
                ["Clouds", f"Coverage: {weather.clouds.all}%"],
                ["Wind", wind_str],
                ["Temp Next 4 Hours", hour_temp_str],
                ["Wind Next 4 Hours", hour_wind_str],
                ["Sun", sun_str],
            ],
            inline=False,
            thumbnail=f"https://openweathermap.org/img/wn/{weather.weather[0].icon}@4x.png",
        )

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="survey",
        description="Create a survey",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="question",
                description="Question for the survey",
                option_type=3,
                required=True,
            ),
            create_option(
                name="options",
                description="Space delimited option(s) for the survey",
                option_type=3,
                required=True,
            ),
        ],
    )
    async def _survey(self, ctx: SlashContext, question: str, options: str):
        await Survey(bot=ctx.bot, ctx=ctx, question=question, options=options).send()

    @commands.Cog.listener()
    async def on_component(self, ctx: ComponentContext):
        try:  # Avoid listening to events that don't apply to the vote command
            if "Q:" not in ctx.origin_message.embeds[0].title:
                return
        except:
            return

        embed = ctx.origin_message.embeds[0]
        voters = embed.fields[2].value
        voter_name = ctx.author.mention

        key = embed.footer.text
        if key not in ctx.component_id:  # Avoid over writing other votes
            return

        if voter_name in voters:
            await ctx.send("You cannot vote more than once!", hidden=True)
            return

        query = embed.title.split(": ")[1]
        up_vote_count = int(embed.fields[0].value)
        up_vote_label = ctx.origin_message.components[0]["components"][0]["label"]
        down_vote_count = int(embed.fields[1].value)
        down_vote_label = ctx.origin_message.components[0]["components"][1]["label"]

        if voters == "_":
            voters = voter_name
        else:
            voters += f", {voter_name}"

        if ctx.component_id == f"{key}_a":
            try:
                up_vote_count += 1
            except KeyError:
                raise CommandError(f"Error modifying [{up_vote_label}]")
        elif ctx.component_id == f"{key}_b":
            try:
                down_vote_count += 1
            except KeyError:
                raise CommandError(f"Error modifying [{down_vote_label}]")

        embed = build_embed(
            title=f"Question: {query.capitalize()}",
            description="Times out after 60 seconds.",
            inline=False,
            fields=[
                [up_vote_label, str(up_vote_count)],
                [down_vote_label, str(down_vote_count)],
                ["Voters", voters],
            ],
            footer=key,
        )
        new_buttons = ctx.origin_message.components[0]["components"]

        await ctx.edit_origin(
            content="", embed=embed, components=[create_actionrow(*new_buttons)]
        )


def setup(bot):
    bot.add_cog(TextCommands(bot))

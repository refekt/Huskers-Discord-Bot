import random
import re
from urllib import parse

import discord
import markovify
import requests
from bs4 import BeautifulSoup
from dinteractions_Paginator import Paginator
from discord.ext import commands
from discord_slash import ComponentContext
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow

from utilities.constants import CHAN_BANNED, CHAN_POSSUMS
from utilities.constants import command_error
from utilities.constants import guild_id_list
from utilities.embed import build_embed

buttons_ud = [
    create_button(
        style=ButtonStyle.gray,
        label="Previous",
        custom_id="ud_previous",
        disabled=True
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Next",
        custom_id="ud_next"
    )
]

buttons_voting = [
    create_button(
        style=ButtonStyle.green,
        label="Up Vote",
        custom_id="vote_up"
    ),
    create_button(
        style=ButtonStyle.red,
        label="Down Vote",
        custom_id="vote_down"
    )
]


def ud_embed(embed_word, embed_meaning, embed_example, embed_contributor):
    return build_embed(
        title="Urband Dictionary Result",
        inline=False,
        footer=embed_contributor,
        fields=[
            [embed_word, embed_meaning],
            ["Example", embed_example],
            ["Link", f"https://www.urbandictionary.com/define.php?term={parse.quote(string=embed_word)}"]
        ]
    )


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
        name="urbanddictionary",
        description="Look up a word on Urban Dictionary",
        guild_ids=guild_id_list()
    )
    async def _urbandictionary(self, ctx: SlashContext, *, word: str):
        r = requests.get(f"http://www.urbandictionary.com/define.php?term={word}")
        soup = BeautifulSoup(r.content, features="html.parser")

        try:
            definitions = soup.find_all(name="div", attrs={"class": "def-panel"})
        except AttributeError:
            raise command_error(f"Unable to find [{word}] in Urban Dictionary.")

        del r, soup, definitions[1]  # Word of the day

        results = []
        for definition in definitions:
            results.append(self.Definition(
                lookup_word=definition.contents[1].contents[0].text,
                meaning=definition.contents[2].text,
                example=definition.contents[3].text,
                contributor=definition.contents[4].text
            ))

        pages = []
        for index, result in enumerate(results):
            pages.append(build_embed(
                title=f"Searched for: {result.lookup_word}",
                description=f"Definition #{index + 1} from Urban Dictionary",
                fields=[
                    ["Meaning", result.meaning],
                    ["Example", result.example],
                    ["Contributor", result.contributor]
                ]
            ))

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
            indexStyle=ButtonStyle.gray
        )

    @cog_ext.cog_slash(
        name="vote",
        description="Ask the community for their opinion in votes",
        guild_ids=guild_id_list()
    )
    async def _vote(self, ctx: SlashContext, *, query: str):
        embed = build_embed(
            title="Vote",
            inline=False,
            fields=[
                ["Question", query.capitalize()],
                ["Up Votes", "0"],
                ["Down Votes", "0"],
                ["Voters", "_"]
            ]
        )
        vote_actionrow = create_actionrow(*buttons_voting)
        await ctx.send(content="", embed=embed, components=[vote_actionrow])

    @cog_ext.cog_component(components=buttons_voting)
    async def process_voting_buttons(self, ctx: ComponentContext):
        # await ctx.defer()

        voters = ctx.origin_message.embeds[0].fields[3].value
        if str(ctx.author.mention) in voters:
            return

        query = ctx.origin_message.embeds[0].fields[0].value
        up_vote_count = int(ctx.origin_message.embeds[0].fields[1].value)
        down_vote_count = int(ctx.origin_message.embeds[0].fields[2].value)

        if voters == "_":
            voters = ""

        voters += f" {str(ctx.author.mention)} "

        if ctx.custom_id == "vote_up":
            try:
                up_vote_count += 1
                embed = build_embed(
                    title="Vote",
                    inline=False,
                    fields=[
                        ["Question", query.capitalize()],
                        ["Up Votes", up_vote_count],
                        ["Down Votes", down_vote_count],
                        ["Voters", voters]
                    ]
                )
                await ctx.edit_origin(content="", embed=embed, components=[create_actionrow(*buttons_voting)])
            except KeyError:
                raise command_error("Error modifying Up Votes")
        elif ctx.custom_id == "vote_down":
            try:
                down_vote_count += 1
                embed = build_embed(
                    title="Vote",
                    inline=False,
                    fields=[
                        ["Question", query.capitalize()],
                        ["Up Votes", up_vote_count],
                        ["Down Votes", down_vote_count],
                        ["Voters", voters]
                    ]
                )
                await ctx.edit_origin(content="", embed=embed, components=[create_actionrow(*buttons_voting)])
            except KeyError:
                raise command_error("Error modifying Down Votes")

    def check_channel_or_message(self, check_member: discord.Member, check_message: discord.Message = None):
        if check_message.content == "":
            return ""

        if check_message.channel.id in CHAN_BANNED:
            return ""

        if check_member.bot:
            return ""

        return "\n" + str(check_message.content.capitalize())

    def cleanup_source_data(self, source_data: str):
        regex_strings = [
            r"(<@\d{18}>|<@!\d{18}>|<:\w{1,}:\d{18}>|<#\d{18}>)",  # All Discord mentions
            r"((Http|Https|http|ftp|https)://|)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"  # All URLs
        ]

        new_source_data = source_data

        for regex in regex_strings:
            new_source_data = re.sub(regex, "", new_source_data, flags=re.IGNORECASE)

        regex_new_line = r"(\r\n|\r|\n){1,}"  # All new lines
        new_source_data = re.sub(regex_new_line, "\n", new_source_data, flags=re.IGNORECASE)

        regex_front_new_line = r"^\n"
        new_source_data = re.sub(regex_front_new_line, "", new_source_data, flags=re.IGNORECASE)

        regex_multiple_whitespace = r"\s{2,}"
        new_source_data = re.sub(regex_multiple_whitespace, " ", new_source_data, flags=re.IGNORECASE)

        return new_source_data

    @cog_ext.cog_slash(
        name="markov",
        description="Attempts to create a meaningful sentence from old messages",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="channel",
                description="Discord text channel",
                option_type=7,
                required=False
            ),
            create_option(
                name="member",
                description="Discord member",
                option_type=6,
                required=False
            )
        ]
    )
    async def _markov(self, ctx: SlashContext, channel=None, member=None):
        await ctx.defer()

        sources = []
        if channel is not None:
            sources.append(channel)

        if member is not None:
            sources.append(member)

        source_data = ""

        compiled_message_history = []

        CHAN_HIST_LIMIT = 1000

        if not sources:  # Uses current channel for source data
            compiled_message_history = await ctx.channel.history(limit=CHAN_HIST_LIMIT).flatten()  # potential discord vs discord_slash issue
            for message in compiled_message_history:
                source_data += self.check_channel_or_message(ctx.author, message)
        else:
            for source in sources:
                if type(source) == discord.Member:  # Use current channel and source Discord Member
                    compiled_message_history = await ctx.channel.history(limit=CHAN_HIST_LIMIT).flatten()
                    for message in compiled_message_history:
                        if message.author == source:
                            source_data += self.check_channel_or_message(message.author, message)
                elif type(source) == discord.TextChannel:
                    compiled_message_history = await source.history(limit=CHAN_HIST_LIMIT).flatten()
                    for message in compiled_message_history:
                        source_data += self.check_channel_or_message(message.author, message)

        if not source_data == "":
            source_data = self.cleanup_source_data(source_data)
        else:
            await ctx.send(f"There was not enough information available to make a Markov chain.")

        chain = markovify.NewlineText(source_data, well_formed=True)
        markov_output = chain.make_sentence(max_overlap_ratio=.9, max_overlap_total=27, min_words=7, tries=100)

        if markov_output is None:
            await ctx.send(f"Creating a Markov chain failed.")
        else:
            punctuation = ("!", ".", "?", "...")
            markov_output += random.choice(punctuation)
            await ctx.send(markov_output)

    @cog_ext.cog_slash(
        name="possumdroppings",
        description="Only the most secret and trustworthy drops",
        guild_ids=guild_id_list()
    )
    async def _possumdroppings(self, ctx: SlashContext, message: str):
        await ctx.defer()

        if not ctx.channel_id == CHAN_POSSUMS:
            raise command_error(f"You can only use this command in [{ctx.guild.get_channel(CHAN_POSSUMS).mention}]")

        await ctx.send("Thinking...", delete_after=0)

        embed = build_embed(
            title="Possum Droppings",
            inline=False,
            thumbnail="https://cdn.discordapp.com/attachments/593984711706279937/875162041818693632/unknown.jpeg",
            footer="Created by a possum",
            fields=[
                ["Droppings", message]
            ]
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="eightball",
        description="Ask the magic 8-ball a qusetion",
        guild_ids=guild_id_list()
    )
    async def _eightball(self, ctx: SlashContext, question: str):
        eight_ball = [
            'As I see it, yes.',
            'Ask again later.',
            'Better not tell you now.',
            'Cannot predict now.',
            'Coach V\'s cigar would like this!',
            'Concentrate and ask again.',
            'Definitely yes!',
            'Don’t count on it...',
            'Frosty!',
            'Fuck Iowa!',
            'It is certain.',
            'It is decidedly so.',
            'Most likely...',
            'My reply is no.',
            'My sources say no.',
            'Outlook not so good and reply hazy',
            'Scott Frost approves!',
            'These are the affirmative answers.',
            'Try again...',
            'Without a doubt.',
            'Yes – definitely!',
            'You may rely on it.'
        ]

        random.shuffle(eight_ball)

        embed = build_embed(
            title="BotFrost Magic 8-Ball :8ball: says...",
            description="These are all 100% accurate. No exceptions! Unless an answer says anyone other than Nebraska is good.",
            inline=False,
            fields=[
                ["Question", question.capitalize()],
                ["Response", random.choice(eight_ball)]
            ],
            thumbnail="https://i.imgur.com/L5Gpu0z.png"
        )

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="police",
        description="You are under arrest!",
        guild_ids=guild_id_list()
    )
    async def _police(self, ctx: SlashContext, arestee: discord.Member):
        message = f"**" \
                  f"🚨 NANI 🚨\n" \
                  f"..🚨 THE 🚨\n" \
                  f"...🚨 FUCK 🚨\n" \
                  f"....🚨 DID 🚨\n" \
                  f".....🚨 YOU 🚨\n" \
                  f"....🚨 JUST 🚨\n" \
                  f"...🚨 SAY 🚨\n" \
                  f"..🚨 {arestee.mention} 🚨\n" \
                  f"🏃‍♀️💨 🔫🚓🔫🚓🔫🚓\n" \
                  f"\n" \
                  f"👮‍📢 Information ℹ provided in the VIP 👑 Room 🏆 is intended for Husker247 🌽🎈 members only ‼🔫. Please do not copy ✏ and paste 🖨 or summarize this content elsewhere‼ Please try to keep all replies in this thread 🧵 for Husker247 members only! 🚫 ⛔ 👎 " \
                  f"🙅‍♀️Thanks for your cooperation. 😍🤩😘" \
                  f"**"

        embed = build_embed(
            title="Wee woo wee woo!",
            inline=False,
            fields=[
                ["Halt!", message]
            ]
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TextCommands(bot))

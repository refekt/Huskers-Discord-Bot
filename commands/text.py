from urllib import parse

import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from discord_slash import ButtonStyle, ComponentContext
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_components import create_button, create_actionrow

from utilities.constants import command_error
from utilities.embed import build_embed
from utilities.server_detection import which_guid

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

results = []
result_index = 0


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
        guild_ids=[which_guid()]
    )
    async def _urbandictionary(self, ctx: SlashContext, *, word: str):
        r = requests.get(f"http://www.urbandictionary.com/define.php?term={word}")
        soup = BeautifulSoup(r.content, features="html.parser")

        try:
            definitions = soup.find_all(name="div", attrs={"class": "def-panel"})
        except AttributeError:
            raise command_error(f"Unable to find [{word}] in Urban Dictionary.")

        del r, soup, definitions[1]  # Word of the day

        for definition in definitions:
            results.append(self.Definition(
                lookup_word=definition.contents[1].contents[0].text,
                meaning=definition.contents[2].text,
                example=definition.contents[3].text,
                contributor=definition.contents[4].text
            ))

        global result_index
        result_index = 0

        embed = ud_embed(
            embed_word=results[result_index].lookup_word,
            embed_meaning=results[result_index].meaning,
            embed_example=results[result_index].example,
            embed_contributor=results[result_index].contributor
        )

        actionrow_ud = create_actionrow(*buttons_ud)
        await ctx.send(embed=embed, components=[actionrow_ud])

    @cog_ext.cog_component(components=buttons_ud)
    async def process_ud_buttons(self, ctx: ComponentContext):
        global results, result_index

        if ctx.custom_id == "ud_previous":
            if result_index == 0:
                return
            result_index -= 1
        elif ctx.custom_id == "ud_next":
            if result_index == len(results):
                return
            result_index += 1

        if 0 < result_index < (len(results) - 1):
            buttons_ud[0]["disabled"] = False
            buttons_ud[1]["disabled"] = False

        else:
            if result_index <= 0:
                buttons_ud[0]["disabled"] = True
            elif result_index >= len(results) - 1:
                buttons_ud[1]["disabled"] = True

        actionrow_ud = create_actionrow(*buttons_ud)

        edited_embed = ud_embed(
            embed_word=results[result_index].lookup_word,
            embed_example=results[result_index].example,
            embed_meaning=results[result_index].meaning,
            embed_contributor=results[result_index].contributor
        )

        await ctx.edit_origin(content="", embed=edited_embed, components=[actionrow_ud])

    @cog_ext.cog_slash(
        name="vote",
        description="Ask the community for their opinion in votes",
        guild_ids=[which_guid()]
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


def setup(bot):
    bot.add_cog(TextCommands(bot))

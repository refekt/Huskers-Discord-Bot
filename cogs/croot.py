import asyncio
import datetime

import discord
from discord.ext import commands

from utils.client import client
from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE
from utils.embed import build_embed, build_recruit_embed
from utils.recruit import FootballRecruit


class RecruitCommands(commands.Cog):
    @commands.command(aliases=["cb",])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def crootboot(self, ctx, year: int, *name):
        """ Retreive information about a recruit """
        if len(name) == 0:
            raise discord.ext.commands.UserInputError("A player's first and/or last name is required.")

        if len(str(year)) == 2:
            year += 2000

        if year > datetime.datetime.now().year + 5:
            raise discord.ext.commands.UserInputError("The search year must be within five years of the current class.")

        if year < 1869:
            raise discord.ext.commands.UserInputError("The search year must be after the first season of college football--1869.")

        edit_msg = await ctx.send("Loading...")
        search = FootballRecruit(year, name)

        if len(search) == 1:
            embed = build_recruit_embed(search[0])
            await edit_msg.edit(content="", embed=embed)
            return

        result_info = ""
        search_reactions = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4, "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8, "🔟": 9}

        index = 0

        for index, result in enumerate(search):
            if index < 10:
                result_info += f"{list(search_reactions.keys())[index]}: {result.year} - {'⭐' * result.rating_stars}{' - ' + result.position if result.rating_stars > 0 else result.position} - {result.name}\n"

        embed = build_embed(
            title=f"Search Results for [{year} {[n for n in name]}]",
            fields=[["Search Results", result_info]]
        )

        await edit_msg.edit(content="", embed=embed)

        for reaction in list(search_reactions.keys())[0:index + 1]:
            await edit_msg.add_reaction(reaction)

        def checking_reaction(reaction, user):
            if not user.bot:
                return reaction.emoji in search_reactions

        search_result_player = None

        try:
            reaction, user = await client.wait_for("reaction_add", check=checking_reaction)
        except asyncio.TimeoutError:
            pass
        else:
            search_result_player = search[search_reactions[reaction.emoji]]

        embed = build_recruit_embed(search_result_player)
        await edit_msg.edit(content="", embed=embed)

        try:
            await edit_msg.clear_reactions()
        except discord.HTTPException:
            print("Removing reactions from the message failed.")
        except discord.ClientException:
            print("Unable to remove reactions due to lack of permissions.")


def setup(bot):
    bot.add_cog(RecruitCommands(bot))


# print("### Recruit Commands loaded! ###")

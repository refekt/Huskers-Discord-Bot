import datetime

from discord.ext.commands import Cog
from discord_slash import ButtonStyle, ComponentContext
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.utils.manage_components import wait_for_component

from objects.FAP import initiate_fap, individual_predictions
from objects.Recruit import FootballRecruit
from utilities.constants import CROOT_SEARCH_LIMIT
from utilities.constants import GUILD_PROD, GUILD_TEST
from utilities.constants import user_error
from utilities.embed import build_embed, build_recruit_embed
from utilities.server_detection import production_server

if production_server():
    current_guild = [GUILD_PROD]
else:
    current_guild = [GUILD_TEST]


async def final_send_embed_fap_loop(ctx, target_recruit, bot, edit=False):
    embed = build_recruit_embed(target_recruit)

    fap_buttons = [
        create_button(
            style=ButtonStyle.gray,
            label="🔮",
            custom_id="crystal_ball"
        ),
        create_button(
            style=ButtonStyle.gray,
            label="📜",
            custom_id="scroll"
        )
    ]

    temp_fap_buttons = list(fap_buttons)  # Create a copy of list because python links lists if you do new_list = list.

    if target_recruit.committed == "Enrolled":
        del temp_fap_buttons[0]  # Don't dispaly the crystal ball if committed

    fap_action_row = create_actionrow(*temp_fap_buttons)

    if edit:
        await ctx.edit_origin(content="", embed=embed, components=fap_action_row)
    else:
        embed = build_recruit_embed(target_recruit)
        await ctx.send(embed=embed, components=[fap_action_row])

    button_contenxt: ComponentContext = await wait_for_component(bot, components=fap_action_row)

    if button_contenxt.custom_id == "crystal_ball":
        await initiate_fap(ctx.author, target_recruit, bot)

    elif button_contenxt.custom_id == "scroll":
        await individual_predictions(ctx=ctx, recruit=target_recruit)


def checking_reaction(search_reactions, reaction_used, user_initiated):
    if not user_initiated.bot:ed
        return reaction_used.emoji in search_reactions


class RecruitCog(Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="cb", description="Retreive information about a recruit", guild_ids=current_guild)
    async def _cb(self, ctx: SlashContext, year: int, name: str):
        if len(name) == 0:
            raise user_error("A player's first and/or last name is required.")

        if len(str(year)) == 2:
            year += 2000
        elif len(str(year)) == 1 or len(str(year)) == 3:
            raise user_error("The search year must be two or four digits long.")

        if year > datetime.datetime.now().year + 5:
            raise user_error("The search year must be within five years of the current class.")

        if year < 1869:
            raise user_error("The search year must be after the first season of college football--1869.")

        await ctx.defer()  # Similiar to sending a message with a loading screen to edit later on

        buttons = [
            create_button(
                style=ButtonStyle.blue,
                label="1",
                custom_id="result_1"
            ),
            create_button(
                style=ButtonStyle.blue,
                label="2",
                custom_id="result_2"
            ),
            create_button(
                style=ButtonStyle.blue,
                label="3",
                custom_id="result_3"
            ),
            create_button(
                style=ButtonStyle.blue,
                label="4",
                custom_id="result_4"
            ),
            create_button(
                style=ButtonStyle.blue,
                label="5",
                custom_id="result_5"
            )
        ]

        action_row = create_actionrow(*buttons)

        search = FootballRecruit(year, name)

        if len(search) == 1:
            await final_send_embed_fap_loop(ctx=ctx, target_recruit=search[0], bot=self.bot)
            return

        result_info = ""
        search_reactions = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4, "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8, "🔟": 9}

        for index, result in enumerate(search):
            if index < CROOT_SEARCH_LIMIT:
                result_info += f"{list(search_reactions.keys())[index]}: {result.year} - {'⭐' * result.rating_stars}{' - ' + result.position if result.rating_stars > 0 else result.position} - {result.name}\n"

        embed = build_embed(
            title=f"Search Results for [{year} {name}]",
            fields=[["Search Results", result_info]]
        )

        await ctx.send(embed=embed, components=[action_row])

        button_context: ComponentContext = await wait_for_component(self.bot, components=action_row)

        button_to_index = {"result_1": 1, "result_2": 2, "result_3": 3, "result_4": 4, "result_5": 5}

        await final_send_embed_fap_loop(ctx=ctx, target_recruit=search[button_to_index[button_context.custom_id]], bot=self.bot)

    # This may work but not having the `search` and `target_recruit` etc. variables persit makes it difficult
    # @commands.Cog.listener()
    # async def on_component(self, ctx: ComponentContext):
    #     if ctx.component_type == 1:  # Blue, searching
    #         button_to_index = {"result_1": 1, "result_2": 2, "result_3": 3, "result_4": 4, "result_5": 5}
    #
    #         await final_send_embed_fap_loop(ctx=ctx, target_recruit=search[button_to_index[button_context.custom_id]], bot=self.bot)
    #     elif ctx.component_type == 2:  # Gray, FAP
    #         if ctx.custom_id == "crystal_ball":
    #             await initiate_fap(ctx.author, target_recruit, bot)
    #
    #         elif ctx.custom_id == "scroll":
    #             await individual_predictions(ctx=ctx, recruit=target_recruit)


def setup(bot):
    bot.add_cog(RecruitCog(bot))

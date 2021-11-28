import datetime

from discord.ext import commands
from discord_slash import ButtonStyle, ComponentContext, SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import (
    create_actionrow,
    create_button,
    wait_for_component,
)

from objects.FAPing import individual_predictions, initiate_fap
from objects.Recruits import FootballRecruit
from utilities.constants import CROOT_SEARCH_LIMIT, TZ, UserError, guild_id_list
from utilities.embed import build_embed, build_recruit_embed


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### Croot Bot: {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ Croot Bot: {message}")


fap_buttons = [
    create_button(
        style=ButtonStyle.gray, label="🔮", custom_id="crystal_ball", disabled=True
    ),
    create_button(
        style=ButtonStyle.gray, label="📜", custom_id="scroll", disabled=False
    ),
]
fap_action_row = create_actionrow(*fap_buttons)

croot_search = []
fap_search = []
search_reactions = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4}

search_buttons = [
    create_button(style=ButtonStyle.blue, label="1", custom_id="result_1"),
    create_button(style=ButtonStyle.blue, label="2", custom_id="result_2"),
    create_button(style=ButtonStyle.blue, label="3", custom_id="result_3"),
    create_button(style=ButtonStyle.blue, label="4", custom_id="result_4"),
    create_button(style=ButtonStyle.blue, label="5", custom_id="result_5"),
]


def search_result_info(new_search) -> str:
    result_info = ""
    for index, recruit in enumerate(new_search):
        if index < CROOT_SEARCH_LIMIT:
            result_info += (
                f"{list(search_reactions.keys())[index]}: "
                f"{recruit.year} - "
                f"{'⭐' * recruit.rating_stars if recruit.rating_stars else 'N/R'} - "
                f"{recruit.position} - "
                f"{recruit.name}\n"
            )
    return result_info


async def final_send_embed_fap_loop(ctx, target_recruit, bot, edit: bool = False):
    embed = build_recruit_embed(target_recruit)

    if not target_recruit.committed == "Enrolled":
        fap_buttons[0]["disabled"] = False

    if edit:
        log(f"Editing message", 1)
        await ctx.edit_origin(content="", embed=embed, components=[fap_action_row])
    else:
        log(f"Sending message", 1)
        embed = build_recruit_embed(target_recruit)
        await ctx.send(embed=embed, components=[fap_action_row])

    button_context: ComponentContext = await wait_for_component(
        bot, components=fap_action_row
    )

    if button_context.custom_id == "crystal_ball":
        log(f"Crystal ball pressed for [{target_recruit.name.capitalize()}]", 0)
        await initiate_fap(ctx=ctx, user=ctx.author, recruit=target_recruit, client=bot)
        return

    elif button_context.custom_id == "scroll":
        log(f"Scroll pressed for [{target_recruit.name.capitalize()}]", 0)
        await individual_predictions(ctx=ctx, recruit=target_recruit)
        return


def checking_reaction(search_reactions, reaction_used, user_initiated):
    if not user_initiated.bot:
        return reaction_used.emoji in search_reactions


class RecruitCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="crootbot",
        description="Retreive information about a recruit",
        guild_ids=guild_id_list(),
    )
    async def _crootbot(self, ctx: SlashContext, year: int, search_name: str):
        print(f"[{datetime.datetime.now().astimezone(tz=TZ)}] ### Crootbot")

        if len(search_name) == 0:
            raise UserError("A player's first and/or last search_name is required.")

        if len(str(year)) == 2:
            year += 2000
        elif len(str(year)) == 1 or len(str(year)) == 3:
            raise UserError("The search year must be two or four digits long.")

        if year > datetime.datetime.now().year + 5:
            raise UserError(
                "The search year must be within five years of the current class."
            )

        if year < 1869:
            raise UserError(
                "The search year must be after the first season of college football--1869."
            )

        await ctx.defer()  # Similar to sending a message with a loading screen to edit later on

        log(f"Searching for [{year} {search_name.capitalize()}]", 1)

        global croot_search
        croot_search = FootballRecruit(year, search_name)

        log(f"Found [{len(croot_search)}] results", 1)

        if len(croot_search) == 1:
            return await final_send_embed_fap_loop(
                ctx=ctx, target_recruit=croot_search[0], bot=self.bot
            )

        result_info = search_result_info(croot_search)
        action_row = create_actionrow(*search_buttons)

        embed = build_embed(
            title=f"Search Results for [{year} {search_name.capitalize()}]",
            fields=[["Search Results", result_info]],
        )

        await ctx.send(embed=embed, components=[action_row])

        log(f"Sent search results for [{year} {search_name.capitalize()}]", 1)

    @cog_ext.cog_subcommand(
        name="predict",
        description="Place a FAP for a recruit's commitment",
        base="fap",
        base_description="Frost approved predictions",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="year",
                option_type=4,
                description="Year of the recruit",
                required=True,
            ),
            create_option(
                name="search_name",
                option_type=3,
                description="Name of the recruit",
                required=True,
            ),
        ],
    )
    async def _fap_predict(self, ctx: SlashContext, year: int, search_name: str):
        if len(str(year)) == 2:
            year += 2000

        if year > datetime.datetime.now().year + 5:
            raise UserError(
                "The search year must be within five years of the current class."
            )

        if year < 1869:
            raise UserError(
                "The search year must be after the first season of college football--1869."
            )

        await ctx.defer(hidden=True)

        global fap_search
        fap_search = FootballRecruit(year, search_name)

        if type(fap_search) == commands.UserInputError:
            return await ctx.send(content=fap_search, hidden=True)

        async def send_fap_convo(target_recruit):
            await initiate_fap(
                ctx=ctx, user=ctx.author, recruit=target_recruit, client=ctx.bot
            )

        if len(fap_search) == 1:
            return await send_fap_convo(fap_search[0])

        result_info = search_result_info(fap_search)
        action_row = create_actionrow(*search_buttons)

        embed = build_embed(
            title=f"Search Results for [{year} {search_name.capitalize()}]",
            fields=[["Search Results", result_info]],
        )

        await ctx.send(embed=embed, components=[action_row], hidden=True)

    @cog_ext.cog_subcommand(
        name="leaderboard",
        description="The FAP leaderboard",
        base="fap",
        base_description="Frost approved predictions",
        guild_ids=guild_id_list(),
    )
    async def _fap_leaderboard(self, ctx: SlashContext):
        # TODO All of this.
        await ctx.send("Work in progress!", hidden=True)

    @cog_ext.cog_component(components=search_buttons)
    async def process_croot_bot(self, ctx: ComponentContext):
        button_to_index = {
            "result_1": 0,
            "result_2": 1,
            "result_3": 2,
            "result_4": 3,
            "result_5": 4,
        }
        log(f"Button [{ctx.custom_id}] was pressed", 1)

        global croot_search, fap_search

        if croot_search is not None:
            await final_send_embed_fap_loop(
                ctx=ctx,
                target_recruit=croot_search[button_to_index[ctx.custom_id]],
                bot=self.bot,
                edit=True,
            )
            del croot_search
        if fap_search is not None:
            await initiate_fap(
                ctx=ctx,
                user=ctx.author,
                recruit=fap_search[button_to_index[ctx.custom_id]],
                client=ctx.bot,
            )

            del fap_search


def setup(bot):
    bot.add_cog(RecruitCog(bot))

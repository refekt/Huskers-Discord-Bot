import datetime
from discord.ext import commands
from discord_slash import ButtonStyle, ComponentContext
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.utils.manage_components import wait_for_component

from objects.FAP import initiate_fap, individual_predictions
from objects.Recruit import FootballRecruit
from utilities.constants import CROOT_SEARCH_LIMIT
from utilities.constants import user_error
from utilities.embed import build_embed, build_recruit_embed
from utilities.server_detection import which_guild


async def final_send_embed_fap_loop(ctx, target_recruit, bot, edit=False):
    embed = build_recruit_embed(target_recruit)

    fap_buttons = [
        create_button(
            style=ButtonStyle.gray,
            label="🔮",
            custom_id="crystal_ball",
            disabled=True
        ),
        create_button(
            style=ButtonStyle.gray,
            label="📜",
            custom_id="scroll",
            disabled=False
        )
    ]

    if not target_recruit.committed == "Enrolled":
        fap_buttons[0]["disabled"] = False

    fap_action_row = create_actionrow(*fap_buttons)

    if edit:
        print("### ~~~ Editing message ###")

        await ctx.edit_origin(content="", embed=embed, components=[fap_action_row])
    else:
        print("### ~~~ Sending message")

        embed = build_recruit_embed(target_recruit)
        await ctx.send(embed=embed, components=[fap_action_row])

    button_contenxt: ComponentContext = await wait_for_component(bot, components=fap_action_row)

    if button_contenxt.custom_id == "crystal_ball":
        print(f"### ~~~ Crystal ball pressed for [{target_recruit.name.capitalize()}]")
        await initiate_fap(ctx.author, target_recruit, bot)
        return

    elif button_contenxt.custom_id == "scroll":
        print(f"### ~~~ Scroll pressed for [{target_recruit.name.capitalize()}]")
        await individual_predictions(ctx=ctx, recruit=target_recruit)
        return


def checking_reaction(search_reactions, reaction_used, user_initiated):
    if not user_initiated.bot:
        return reaction_used.emoji in search_reactions


search = None

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


class RecruitCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="crootbot",
        description="Retreive information about a recruit",
        guild_ids=[which_guild()]
    )
    async def _crootbot(self, ctx: SlashContext, year: int, name: str):
        print(f"### Crootbot ###")

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

        print(f"### ~~~ Searching for [{year} {name.capitalize()}] ###")

        global search
        search = FootballRecruit(year, name)

        print(f"### ~~~ Found [{len(search)}] results ###")

        action_row = create_actionrow(*buttons)

        if len(search) == 1:
            await final_send_embed_fap_loop(ctx=ctx, target_recruit=search[0], bot=self.bot)
            return

        result_info = ""
        search_reactions = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4}

        for index, result in enumerate(search):
            if index < CROOT_SEARCH_LIMIT:
                result_info += f"{list(search_reactions.keys())[index]}: {result.year} - {'⭐' * result.rating_stars}{' - ' + result.position if result.rating_stars > 0 else result.position} - {result.name}\n"

        embed = build_embed(
            title=f"Search Results for [{year} {name.capitalize()}]",
            fields=[["Search Results", result_info]]
        )

        await ctx.send(embed=embed, components=[action_row])

        print(f"### ~~~ Sent search results for [{year} {name.capitalize()}] ###")

    @cog_ext.cog_component(components=buttons)
    async def process_searches(self, ctx: ComponentContext):
        button_to_index = {"result_1": 0, "result_2": 1, "result_3": 2, "result_4": 3, "result_5": 4}
        print(f"### ~~~ Button [{ctx.custom_id}] was pressed ###")
        global search
        await final_send_embed_fap_loop(ctx=ctx, target_recruit=search[button_to_index[ctx.custom_id]], bot=self.bot, edit=True)


def setup(bot):
    bot.add_cog(RecruitCog(bot))

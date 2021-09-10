from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from utilities.constants import guild_id_list
from discord_surveys.survey import SurveyOption, Survey


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ {message}")


class TestCommand(commands.Cog):
    @cog_ext.cog_slash(
        name="test",
        description="Test command",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="question",
                description="Question for the survey",
                option_type=3,
                required=True
            ),
            create_option(
                name="options",
                description="Space deliminated option(s) for the survey",
                option_type=3,
                required=True
            )
        ]
    )
    async def _test(self, ctx: SlashContext, question: str, options: str):
        options = options.strip()
        if " " in options:
            options = options.split()
        else:
            options = [options]

        for index, opt in enumerate(options):
            options[index] = SurveyOption(opt)

        await ctx.defer()
        await Survey(
            bot=ctx.bot,
            ctx=ctx,
            question=question,
            options=options
        ).send()


def setup(bot):
    bot.add_cog(TestCommand(bot))

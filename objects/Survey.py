import hashlib
import random
import string
import typing
from asyncio import TimeoutError as TE
from discord import (
    Embed
)
from discord.ext.commands import (
    AutoShardedBot,
    Bot
)
from discord_slash.context import (
    ComponentContext,
    SlashContext
)
from discord_slash.model import (
    ButtonStyle
)
from discord_slash.utils.manage_components import (
    create_actionrow,
    create_button,
    wait_for_component
)


def generate_random_key() -> str:
    return "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))


class SurveyOption:
    def __init__(self, label: typing.AnyStr):
        assert isinstance(label, str), ValueError("Label must be a string!")

        key = generate_random_key()
        self.custom_id: typing.AnyStr = f"{key}_label"
        self.label: typing.AnyStr = label
        self.value: int = 0


class Survey:
    def __init__(self,
                 bot: typing.Union[AutoShardedBot, Bot],
                 ctx: SlashContext,
                 options: typing.Union[str, SurveyOption],
                 question: typing.AnyStr,
                 timeout: int = 120,
                 ):

        options = options.strip()
        if " " in options:
            options = options.split()
        else:
            options = [options]

        assert len(options) == len(set(options)), ValueError(f"You cannot use the same option more than once!")

        for index, opt in enumerate(options):
            options[index] = SurveyOption(opt)

        max_options = 3

        assert isinstance(question, str), ValueError("Question must be a string!")
        assert [isinstance(opt, SurveyOption) for opt in options], ValueError("Options must be a SurveyOption object!")
        assert 2 <= len(options) <= max_options, ValueError(f"You must have at least 2 and less than {max_options} options!")

        self.bot: typing.Union[AutoShardedBot, Bot] = bot
        self.ctx: SlashContext = ctx
        self.embed: Embed = Embed()
        self.options: typing.List[SurveyOption] = options
        self.question: typing.Union[typing.AnyStr, None] = question
        self.timeout = timeout

    def create_embed(self):
        embed = Embed(
            title="Survey",
            description=f"Please provide your feedback. This survey timesout in {self.timeout} seconds.",
        )
        embed.set_footer(
            text="Users:"
        )
        embed.add_field(
            name="Survey Question",
            value=self.question,
            inline=False
        )
        for index, opt in enumerate(self.options):
            embed.add_field(
                name=opt.label,
                value=str(opt.value),
                inline=False
            )
        self.embed = embed

    def update_embed(self, user_id: str, opt: str):
        hashed_user = hashlib.sha1(str(user_id).encode("UTF-8")).hexdigest()[:10]
        if hashed_user in self.embed.footer.text:
            return False

        for option in self.options:
            if option.label == opt:
                option.value += 1
                break

        footer_text = self.embed.footer.text
        self.create_embed()
        self.embed.set_footer(
            text=f"{footer_text} {hashed_user} "
        )
        return True

    async def close_survey(self, ctx: ComponentContext):
        await ctx.origin_message.edit(
            content="",
            embed=self.embed,
            components=None
        )

    def actionrow(self):
        buttons = []
        for opt in self.options:
            buttons.append(
                create_button(
                    style=ButtonStyle.gray,
                    label=opt.label,
                    custom_id=opt.custom_id
                )
            )
        return [create_actionrow(*buttons)]

    async def send(self):
        await self.ctx.defer()

        self.create_embed()
        await self.ctx.send(
            embed=self.embed,
            components=self.actionrow()
        )

        go = True
        btn_ctx: typing.Union[None, ComponentContext] = None

        while go:
            try:
                btn_ctx: ComponentContext = await wait_for_component(
                    client=self.bot,
                    timeout=self.timeout,
                    components=self.actionrow()
                )
                resp = self.update_embed(
                    user_id=btn_ctx.author_id,
                    opt=btn_ctx.component["label"]
                )
                await btn_ctx.origin_message.edit(
                    content="",
                    embed=self.embed,
                    components=self.actionrow()
                )
                if resp:
                    await btn_ctx.send("Added your vote, thank you!", hidden=True)
                else:
                    await btn_ctx.send("You cannot vote more than once!", hidden=True)
            except TE:
                go = False
                await self.close_survey(btn_ctx)

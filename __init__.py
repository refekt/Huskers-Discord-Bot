import discord  # noqa # Beta version thing
from discord.app_commands import CommandInvokeError

from objects.Client import HuskerClient
from objects.Logger import discordLogger

logger = discordLogger(__name__)

from helpers.constants import *  # noqa
from helpers.embed import *  # noqa
from helpers.encryption import *  # noqa
from helpers.fryer import *  # noqa
from helpers.misc import *  # noqa
from helpers.mysql import *  # noqa
from helpers.slowking import *  # noqa

from objects.Bets_Stats_Schedule import *  # noqa
from objects.Exceptions import *  # noqa
from objects.Paginator import *  # noqa
from objects.Recruits import *  # noqa
from objects.Survey import *  # noqa
from objects.Thread import *  # noqa
from objects.TweepyStreamListener import *  # noqa
from objects.Weather import *  # noqa
from objects.Winsipedia import *  # noqa

__all__ = ["client"]

intents = discord.Intents.all()
intents.typing = False
intents.presences = False

client = HuskerClient(
    command_prefix="$",
    fetch_offline_members=True,
    intents=intents,
    owner_id=MEMBER_GEE,
)

tree = client.tree


@tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: CommandInvokeError
) -> None:
    logger.info("app_command error detected!")
    err = DiscordError(error, interaction.data.get("options", None))
    logger.error(error, exc_info=True)

    embed = buildEmbed(
        title="",
        fields=[
            dict(
                name=f"Error Type: {err.error_type}",
                value=f"{err.message}",
            ),
            dict(
                name="Command",
                value=f"{'/' + err.command if not err.parent else '/' + err.parent.name + ' ' + err.command}",
            ),
            dict(
                name="Command Input",
                value=f"{', '.join(err.options) if err.options else 'None'}",
            ),
            dict(name="Originating Module", value=f"{err.module}"),
        ],
    )

    if interaction.response.is_done():
        await interaction.followup.send(content="", embed=embed, ephemeral=True)
    else:
        await interaction.channel.send(content="", embed=embed)


discord_loggers = ["discord", "discord.client", "discord.gateway"]
for d_l in discord_loggers:
    _ = logging.getLogger(d_l)
    _.disabled = True

client.run(PROD_TOKEN, log_handler=None)

from time import perf_counter

import discord  # noqa # Beta version thing
from discord.app_commands import CommandInvokeError

from objects.Client import HuskerClient
from objects.Logger import discordLogger

start = perf_counter()

logger = discordLogger(__name__)

logger.info("Loading helpers")

# Helper Functions
from helpers.constants import *  # noqa
from helpers.embed import *  # noqa
from helpers.encryption import *  # noqa
from helpers.fryer import *  # noqa
from helpers.misc import *  # noqa
from helpers.mysql import *  # noqa
from helpers.slowking import *  # noqa

logger.info("Helpers loaded. Loading objects")

# Objects/classes
from objects.Bets import *  # noqa
from objects.Exceptions import *  # noqa
from objects.Karma import *  # noqa
from objects.Logger import *  # noqa
from objects.Paginator import *  # noqa
from objects.Schedule import *  # noqa
from objects.Thread import *  # noqa
from objects.TweepyStreamListener import *  # noqa
from objects.Weather import *  # noqa
from objects.Winsipedia import *  # noqa

# Start the bot
logger.info("Objects loaded. Starting the bot!")

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
    logger.exception(str(error.original.args[0]), exc_info=False)
    embed = buildEmbed(
        title="Command Error Received",
        fields=[
            dict(
                name=f"Error Type: {type(error.original)}",
                value=str(error.original.args[0]),
            ),
            dict(
                name="Input",
                value=f"This error originated from '{error.command.qualified_name}'{' with the following data passed: ' + str(interaction.data['options']) if interaction.data.get('options', False) else ''}",
            ),
        ],
    )
    if interaction.response.is_done():
        await interaction.followup.send(content="", embed=embed)
    else:
        await interaction.response.send_message(content="", embed=embed, ephemeral=True)


end = perf_counter()
logger.info(f"The bot initialized in {end - start:,.2f} seconds")

__all__ = ["client"]


# v2.0 loop
async def main() -> None:
    async with client:
        await client.start(PROD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

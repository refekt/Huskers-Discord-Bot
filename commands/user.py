import enum
import logging
from typing import Optional, Union

import discord
from discord import app_commands, Forbidden, HTTPException
from discord.ext import commands

from helpers.constants import (
    GUILD_PROD,
    ROLE_ADMIN_PROD,
    ROLE_EVERYONE_PROD,
    ROLE_HYPE_MAX,
    ROLE_HYPE_NO,
    ROLE_HYPE_SOME,
    ROLE_MOD_PROD,
    ROLE_TIME_OUT,
    ROLE_BLUE_NAME,
)
from helpers.embed import buildEmbed
from helpers.misc import discordURLFormatter
from objects.Client import GUILD_ROLES
from objects.Logger import discordLogger, is_debugging

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

dict_roles: dict = {}

for index, role in enumerate(GUILD_ROLES):
    if index == 25:
        break

    if (
        "/r/huskers mod" in role.name
        or "Booster" in role.name
        or "Politics time out" in role.name
        or "Server Historian" in role.name
        or role.id == ROLE_ADMIN_PROD
        or role.id == ROLE_BLUE_NAME
        or role.id == ROLE_EVERYONE_PROD
        or role.id == ROLE_MOD_PROD
        or role.id == ROLE_TIME_OUT
        or role.name == "Bot Creators"
        or role.name == "Dyno"
        or role.name == "Statbot"
    ):
        continue

    dict_roles[role.name] = float(role.id)

GuildRoles = enum.Enum("Role", dict_roles)


# Depreciated
# class HypeRoles(str, enum.Enum):
#     MaxHype = "Max Hype"
#     SomeHype = "Some Hype"
#     NoHype = "No Hype"
#
#     def __str__(self) -> str:
#         return str(self.value)


class UserCog(commands.Cog, name="User Commands"):
    group_submit: app_commands.Group = app_commands.Group(
        name="submit",
        description="Submit a bug or feature request for the bot",
        guild_ids=[GUILD_PROD],
    )

    @group_submit.command(name="bug", description="Submit a bug")
    async def submit_bug(self, interaction: discord.Interaction) -> None:
        embed: discord.Embed = buildEmbed(
            title="Bug Reporter",
            description=discordURLFormatter(
                "Submit a bug report here",
                "https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=bug&template=bug_report.md&title=%5BBUG%5D+",
            ),
        )
        await interaction.response.send_message(embed=embed)

    @group_submit.command(name="feature", description="Submit a feature")
    async def submit_feature(self, interaction: discord.Interaction) -> None:
        embed: discord.Embed = buildEmbed(
            title="Feature Request",
            description=discordURLFormatter(
                "Submit a feature request here",
                "https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=request&template=feature_request.md&title=%5BREQUEST%5D+",
            ),
        )
        await interaction.response.send_message(embed=embed)

    # Depreciated
    @app_commands.command(name="hype", description="Add a hype role")
    # @app_commands.describe(apply_role="The hype role you want to apply")
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def hype(
        self,
        interaction: discord.Interaction,  # , apply_role: HypeRoles
    ) -> None:
        await interaction.response.send_message(
            "This command has been replaced by `/roles`.", ephemeral=True
        )

        # await interaction.response.defer(ephemeral=True)
        #
        # hype_roles = (
        #     interaction.guild.get_role(ROLE_HYPE_MAX),
        #     interaction.guild.get_role(ROLE_HYPE_SOME),
        #     interaction.guild.get_role(ROLE_HYPE_NO),
        # )
        #
        # new_role: Optional[discord.Role] = None
        #
        # try:
        #     await interaction.user.remove_roles(
        #         *hype_roles, reason="Clearing old hype roles"
        #     )
        #
        #     if apply_role == HypeRoles.MaxHype:
        #         new_role = interaction.guild.get_role(ROLE_HYPE_MAX)
        #     elif apply_role == HypeRoles.SomeHype:
        #         new_role = interaction.guild.get_role(ROLE_HYPE_SOME)
        #     elif apply_role == HypeRoles.NoHype:
        #         new_role = interaction.guild.get_role(ROLE_HYPE_NO)
        #
        #     await interaction.user.add_roles(*[new_role])
        #
        # except (Forbidden, HTTPException):
        #     logger.exception("Unable to clear user's roles")
        # finally:
        #     await interaction.followup.send(
        #         f"You have added the {new_role.mention} role"
        #     )

    @app_commands.command(name="roles", description="Add or remove a server role")
    @app_commands.describe(selected_role="Select a role you want to add or remove")
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def roles(self, interaction: discord.Interaction, selected_role: GuildRoles):
        logger.debug(
            f"Attempting to add [{selected_role.name}] role to [{interaction.user.name}#{interaction.user.discriminator}]"
        )

        await interaction.response.defer(ephemeral=True)

        author: str = f"{interaction.user.name}#{interaction.user.discriminator}"

        new_role: Optional[Union[discord.Role, list[discord.Role]]] = None

        try:
            _ = interaction.guild.roles
            new_role: list[discord.Role] = [
                check_role for check_role in _ if check_role.name == selected_role.name
            ]
        except:  # noqa
            pass

        if new_role:
            new_role: discord.Role = new_role[0]

        logger.debug(f"Generated [{new_role.name}] role object")

        hype_roles: tuple[Optional[discord.Role], ...] = (
            interaction.guild.get_role(ROLE_HYPE_MAX),
            interaction.guild.get_role(ROLE_HYPE_SOME),
            interaction.guild.get_role(ROLE_HYPE_NO),
        )

        logger.debug("Generated hype role objects")

        logger.debug(f"Checking if [{new_role.name}] already exists for [{author}]")

        if new_role in interaction.user.roles:
            logger.debug(f"Attempting to remove [{role.name}] role")

            try:
                await interaction.user.remove_roles(
                    new_role, reason="/roles - Removing role"
                )
            except (Forbidden, HTTPException):
                logger.exception("Unable to clear user's roles")
            finally:
                await interaction.followup.send(
                    f"You have removed the {new_role.mention} role"
                )

            logger.debug(f"Removed [{new_role.name}] role")
        else:
            logger.debug(f"Attempting to add [{new_role.name}] role")

            if new_role in hype_roles:
                try:
                    await interaction.user.remove_roles(
                        *hype_roles, reason="/roles - Clearing old hype roles"
                    )
                except (Forbidden, HTTPException):
                    logger.exception("Unable to clear user's roles")

                logger.debug("Removed old hype roles")

            try:
                await interaction.user.add_roles(
                    *[new_role], reason="/roles - Adding role"
                )
            except (Forbidden, HTTPException):
                logger.exception("Unable to clear user's roles")
            finally:
                await interaction.followup.send(
                    f"You have added the {new_role.mention} role"
                )

            logger.debug(f"Added [{selected_role.name}] role to [{author}]")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserCog(bot), guilds=[discord.Object(id=GUILD_PROD)])


logger.info(f"{str(__name__).title()} module loaded!")

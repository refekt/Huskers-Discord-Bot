import platform
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord_slash import ButtonStyle, cog_ext
from discord_slash.context import SlashContext, ComponentContext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission
from discord_slash.utils.manage_components import create_button, create_actionrow, create_select_option, create_select

from utilities.constants import CHAN_BANNED
from utilities.constants import ROLE_ADMIN_PROD, ROLE_ADMIN_TEST, ROLE_MOD_PROD, ROLE_HYPE_MAX, ROLE_HYPE_SOME, ROLE_HYPE_NO
from utilities.constants import ROLE_POTATO, ROLE_ASPARAGUS, ROLE_RUNZA, ROLE_ALDIS, ROLE_QDOBA
from utilities.constants import command_error
from utilities.embed import build_embed as build_embed
from utilities.server_detection import which_guid

buttons_roles_hype = [
    create_button(
        style=ButtonStyle.gray,
        label="Max",
        custom_id="role_hype_max",
        emoji="📈"
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Some",
        custom_id="role_hype_some",
        emoji="⚠"
    ),
    create_button(
        style=ButtonStyle.gray,
        label="No",
        custom_id="role_hype_no",
        emoji="⛔"
    )
]

select_roles_food = create_select(
    options=[
        create_select_option(
            label="Potato Gang",
            value=str(ROLE_POTATO),
            emoji="🥔",
        ),
        create_select_option(
            label="Asparagang",
            value=str(ROLE_ASPARAGUS),
            emoji="💚",
        ),
        create_select_option(
            label="Runza",
            value=str(ROLE_RUNZA),
            emoji="🥪",
        ),
        create_select_option(
            label="Qdoba's Witness",
            value=str(ROLE_QDOBA),
            emoji="🌯",
        ),
        create_select_option(
            label="Aldi's Nuts",
            value=str(ROLE_ALDIS),
            emoji="🥜",
        )
    ],
    placeholder="Choose your food roles",
    min_values=1,
    max_values=5,
    custom_id="select_roles_food"
)

buttons_roles_culture = [
    create_button(
        style=ButtonStyle.gray,
        label="Meme Team",
        emoji="😹",
        custom_id="role_culture_meme"
    ),
    create_button(
        style=ButtonStyle.gray,
        label="He Man Isms Hater Club",
        emoji="♣",
        custom_id="role_culture_isms"
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Packer Backer",
        emoji="🧀",
        custom_id="role_culture_packer"
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Pixel Gang",
        emoji="☎",
        custom_id="role_culture_pixel"
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Airpod Gang",
        emoji="🎧",
        custom_id="role_culture_airpod"
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Minecraft",
        emoji="🪓",
        custom_id="role_culture_minecraft"
    )
]


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="about",
        description="All about Bot Frost!",
        guild_ids=[which_guid()]
    )
    async def _about(self, ctx: SlashContext):
        """ All about Bot Frost """
        await ctx.send(
            embed=build_embed(
                title="About Me",
                inline=False,
                fields=[
                    ["History", "Bot Frost was created and developed by [/u/refekt](https://reddit.com/u/refekt) and [/u/psyspoop](https://reddit.com/u/psyspoop). Jeyrad and ModestBeaver assisted with the creation greatly!"],
                    ["Source Code", "[GitHub](https://www.github.com/refekt/Husker-Bot)"],
                    ["Hosting Location", f"{'Local Machine' if 'Windows' in platform.platform() else 'Virtual Private Server'}"],
                    ["Hosting Status", "https://status.hyperexpert.com/"],
                    ["Latency", f"{self.bot.latency * 1000:.2f} ms"],
                    ["Username", self.bot.user.mention],
                    ["Feeling generous?", f"Check out `{self.bot.command_prefix}donate` to help out the production and upkeep of the bot."]
                ]
            )
        )

    @cog_ext.cog_slash(
        name="quit",
        description="Admin only: Turn off the bot",
        guild_ids=[which_guid()],
        permissions={
            which_guid(): [
                create_permission(ROLE_ADMIN_PROD, SlashCommandPermissionType.ROLE, True),
                create_permission(ROLE_ADMIN_TEST, SlashCommandPermissionType.ROLE, True),
                create_permission(ROLE_MOD_PROD, SlashCommandPermissionType.ROLE, False)
            ]
        }
    )
    async def _uit(self, ctx: SlashContext):
        await ctx.send("Good bye world! 😭")
        print(f"User `{ctx.author}` turned off the bot.")
        await self.bot.logout()

    @cog_ext.cog_slash(
        name="donate",
        description="Donate to the cause!",
        guild_ids=[which_guid()]
    )
    async def _donate(self, ctx: SlashContext):
        """ Donate to the cause """

        await ctx.send(
            embed=build_embed(
                title="Donation Information",
                inline=False,
                fields=[
                    ["About", "I hate asking for donations; however, the bot has grown to the point where official server hosting is required. Server hosting provides 99% uptime and hardware performance I cannot provide with my own hardware. I will be paying for upgraded hosting but donations will help offset any costs."],
                    ["Terms", "(1) Final discretion of donation usage is up to the creator(s). "
                              "(2) Making a donation to the product(s) and/or service(s) does not garner any control or authority over product(s) or service(s). "
                              "(3) No refunds. "
                              "(4) Monthly subscriptions can be terminated by either party at any time. "
                              "(5) These terms can be changed at any time. Please read before each donation. "
                              "(6) Clicking the donation link signifies your agreement to these terms."],
                    ["Donation Link", "[Click Me](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=refekt%40gmail.com&currency_code=USD&source=url)"]
                ]
            ),
            hidden=True
        )

    @cog_ext.cog_subcommand(
        base="purge",
        name="everything",
        description="Admin only: Deletes up to 100 of the previous messages",
        guild_ids=[which_guid()],
        base_permissions={
            which_guid(): [
                create_permission(ROLE_ADMIN_PROD, SlashCommandPermissionType.ROLE, True),
                create_permission(ROLE_ADMIN_TEST, SlashCommandPermissionType.ROLE, True)
            ]
        }
    )
    async def _everything(self, ctx: SlashContext):
        if ctx.subcommand_passed is not None:
            return

        if ctx.channel.id in CHAN_BANNED:
            return

        try:
            max_age = datetime.now() - timedelta(days=13, hours=23, minutes=59)  # Discord only lets you delete 14 day old messages
            deleted = await ctx.channel.purge(after=max_age, bulk=True)
            print(f"Bulk delete of {len(deleted)} messages successful.")
        except discord.ClientException:
            print("Cannot delete more than 100 messages at a time.")
        except discord.Forbidden:
            print("Missing permissions.")
        except discord.HTTPException:
            print("Deleting messages failed. Bulk messages possibly include messages over 14 days old.")

    @cog_ext.cog_subcommand(
        base="purge",
        name="bot",
        description="Admin only: Deletes previous bot messages",
        guild_ids=[which_guid()],
        base_permissions={
            which_guid(): [
                create_permission(ROLE_ADMIN_PROD, SlashCommandPermissionType.ROLE, True),
                create_permission(ROLE_ADMIN_TEST, SlashCommandPermissionType.ROLE, True)
            ]
        }
    )
    async def _bot(self, ctx: SlashContext):
        if ctx.subcommand_passed is not None:
            return

        if ctx.channel.id in CHAN_BANNED:
            return

        try:
            def is_bot(message: discord.Message):
                return message.author.bot

            max_age = datetime.now() - timedelta(days=13, hours=23, minutes=59)  # Discord only lets you delete 14 day old messages
            deleted = await ctx.channel.purge(after=max_age, bulk=True, check=is_bot)
            print(f"Bulk delete of {len(deleted)} messages successful.")
        except discord.ClientException:
            print("Cannot delete more than 100 messages at a time.")
        except discord.Forbidden:
            print("Missing permissions.")
        except discord.HTTPException:
            print("Deleting messages failed. Bulk messages possibly include messages over 14 days old.")

    @cog_ext.cog_slash(
        name="bug",
        description="Submit a bug report for the bot",
        guild_ids=[which_guid()]
    )
    async def _bug(self, ctx: SlashContext):
        embed = build_embed(
            title=f"Bug Reporter",
            fields=[
                ["Report Bugs", "https://github.com/refekt/Bot-Frost/issues/new?assignees=&labels=bug&template=bug_report.md&title="]
            ]
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_subcommand(
        base="roles",
        name="hype",
        description="Assign hype roles",
        guild_ids=[which_guid()]
    )
    async def _roles_hype(self, ctx: SlashContext):
        print("### Roles: Hype Squad ###")

        hype_action_row = create_actionrow(*buttons_roles_hype)

        embed = build_embed(
            title="Which Nebraska hype squad do you belong to?",
            description="Selecting a squad assigns you a role",
            inline=False,
            fields=[
                ["📈 Max Hype", "Squad info"],
                ["⚠ Some Hype", "Squad info"],
                ["⛔ No Hype", "Squad info"]
            ]
        )

        await ctx.send(embed=embed, hidden=True, components=[hype_action_row])

    @cog_ext.cog_component(components=buttons_roles_hype)
    async def process_roles_hype(self, ctx: ComponentContext):
        await ctx.defer()

        print("### ~~~ Gathering roles ###")

        hype_max = ctx.guild.get_role(ROLE_HYPE_MAX)
        hype_some = ctx.guild.get_role(ROLE_HYPE_SOME)
        hype_no = ctx.guild.get_role(ROLE_HYPE_NO)

        if any([hype_max, hype_some, hype_no]) is None:
            raise command_error("Unable to locate role!")

        if ctx.custom_id == "role_hype_max":
            await ctx.author.add_roles(hype_max, reason="Hype squad")
            await ctx.author.remove_roles(hype_some, hype_no, reason="Hype squad")

            await ctx.send(f"{ctx.author.mention} is now on team Max Hype!")
        elif ctx.custom_id == "role_hype_some":
            await ctx.author.add_roles(hype_some, reason="Hype squad")
            await ctx.author.remove_roles(hype_max, hype_no, reason="Hype squad")

            await ctx.send(f"{ctx.author.mention} is now on team Some Hype!")
        elif ctx.custom_id == "role_hype_no":
            await ctx.author.add_roles(hype_no, reason="Hype squad")
            await ctx.author.remove_roles(hype_some, hype_max, reason="Hype squad")

            await ctx.send(f"{ctx.author.mention} is now on team No Hype!")
        else:
            return

        print("### Roles: Hype Squad")

    @cog_ext.cog_subcommand(
        base="roles",
        name="food",
        description="Assign food roles",
        guild_ids=[which_guid()]
    )
    async def _roles_food(self, ctx: SlashContext):
        print("### Roles: Food ###")

        embed = build_embed(
            title="Which Nebraska hype squad do you belong to?",
            description="Selecting a squad assigns you a role",
            inline=False,
            fields=[
                ["🥔 Potato Gang", "Info"],
                ["💚 Asparagang", "Info"],
                ["🥪 Runza", "Info"],
                ["🌯 Qdoba's Witness", "Info"],
                ["🥜 Aldi's Nuts", "Info"],
            ]
        )

        food_action_row = create_actionrow(select_roles_food)

        await ctx.send(embed=embed, hidden=True, components=[food_action_row])

    @cog_ext.cog_component(components=select_roles_food)
    async def process_roles_food(self, ctx: ComponentContext):
        roles_food = {}
        for selection in select_roles_food["options"]:
            roles_food[selection["value"]] = ctx.guild.get_role(role_id=int(selection["value"]))

        # Remove old food roles
        for role in roles_food:
            # try:
            await ctx.author.remove_roles(roles_food[role], reason="Food roles")
            # except:
            #     continue

        # Add selected roles
        joined_roles = ""

        for selected in ctx.selected_options:
            try:
                await ctx.author.add_roles(roles_food[selected], reason="Food roles")

                joined_roles += roles_food[selected].name + "\n"
            except:
                continue

        if joined_roles == "":
            raise command_error("Unable to join any of the selected roles!")

        embed = build_embed(
            title="Food Roles",
            inline=False,
            fields=[
                ["Welcome!", f"[{ctx.author.mention}] has joined the following food roles"],
                ["Roles", joined_roles]
            ]
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AdminCommands(bot))

    # @commands.command(hidden=True)
    # @commands.has_any_role(ROLE_ADMIN_TEST, ROLE_ADMIN_PROD, ROLE_MOD_PROD)
    # async def iowa(self, ctx, who: discord.Member, *, reason: str):
    #     """ Removes all roles from a user, applies the @Time Out role, and records the user's ID to prevent leaving and rejoining to remove @Time Out """
    #     if not who:
    #         raise AttributeError("You must include a user!")
    #
    #     if not reason:
    #         raise AttributeError("You must include a reason why!")
    #
    #     timeout = ctx.guild.get_role(ROLE_TIME_OUT)
    #     iowa = ctx.guild.get_channel(CHAN_IOWA)
    #     added_reason = f"Time Out by {ctx.message.author}: "
    #
    #     roles = who.roles
    #     previous_roles = [str(role.id) for role in who.roles[1:]]
    #     if previous_roles:
    #         previous_roles = ",".join(previous_roles)
    #
    #     for role in roles:
    #         try:
    #             await who.remove_roles(role, reason=added_reason + reason)
    #         except discord.Forbidden:
    #             pass
    #         except discord.HTTPException:
    #             pass
    #
    #     try:
    #         await who.add_roles(timeout, reason=added_reason + reason)
    #     except discord.Forbidden:
    #         pass
    #     except discord.HTTPException:
    #         pass
    #
    #     Process_MySQL(
    #         query=sqlInsertIowa,
    #         values=(who.id, added_reason + reason, previous_roles)
    #     )
    #
    #     await iowa.send(f"[ {who.mention} ] has been sent to {iowa.mention}.")
    #     await ctx.send(
    #         f"[ {who} ] has had all roles removed and been sent to Iowa. Their User ID has been recorded and {timeout.mention} will be reapplied on rejoining the server.")
    #     await who.send(f"You have been moved to [ {iowa.mention} ] for the following reason: {reason}.")
    #
    # @commands.command(hidden=True)
    # @commands.has_any_role(ROLE_ADMIN_TEST, ROLE_ADMIN_PROD, ROLE_MOD_PROD)
    # async def nebraska(self, ctx, who: discord.Member):
    #     if not who:
    #         raise AttributeError("You must include a user!")
    #
    #     timeout = ctx.guild.get_role(ROLE_TIME_OUT)
    #     await who.remove_roles(timeout)
    #
    #     previous_roles_raw = Process_MySQL(
    #         query=sqlRetrieveIowa,
    #         values=who.id,
    #         fetch="all"
    #     )
    #
    #     previous_roles = previous_roles_raw[0]["previous_roles"].split(",")
    #
    #     try:
    #         if previous_roles:
    #             for role in previous_roles:
    #                 new_role = ctx.guild.get_role(int(role))
    #                 await who.add_roles(new_role, reason="Returning from Iowa")
    #     except discord.Forbidden:
    #         pass
    #     except discord.HTTPException:
    #         pass
    #
    #     Process_MySQL(
    #         query=sqlRemoveIowa,
    #         values=who.id
    #     )
    #
    #     iowa = ctx.guild.get_channel(CHAN_IOWA)
    #
    #     await ctx.send(f"[ {who} ] is welcome back to Nebraska.")
    #     await iowa.send(f"[ {who.mention} ] has been sent back to Nebraska.")

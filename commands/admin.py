import asyncio
import platform
from datetime import (
    datetime,
    timedelta
)

import discord
from dinteractions_Paginator import Paginator
from discord.ext import commands
from discord_slash import ButtonStyle, cog_ext
from discord_slash.context import SlashContext, ComponentContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import (
    create_actionrow,
    create_button,
    create_select,
    create_select_option,
    spread_to_rows
)

from utilities.constants import (
    BOT_FOOTER_SECRET,
    CAT_GAMEDAY,
    CAT_GENERAL,
    CHAN_BANNED,
    CHAN_GENERAL,
    CHAN_HYPE_GROUP,
    CHAN_IOWA,
    CHAN_SCOTT,
    CHAN_WAR_ROOM,
    CommandError,
    ROLE_ALDIS,
    ROLE_AIRPOD,
    ROLE_ASPARAGUS,
    ROLE_EVERYONE_PROD,
    ROLE_HYPE_MAX,
    ROLE_HYPE_NO,
    ROLE_HYPE_SOME,
    ROLE_ISMS,
    ROLE_MEME,
    ROLE_PACKER,
    ROLE_PIXEL,
    ROLE_POTATO,
    ROLE_QDOBA,
    ROLE_RUNZA,
    ROLE_TARMAC,
    ROLE_TIME_OUT,
    UserError,
    admin_mod_perms,
    admin_perms,
    guild_id_list
)
from utilities.embed import build_embed as build_embed
from utilities.mysql import (
    Process_MySQL,
    sqlInsertIowa,
    sqlRemoveIowa,
    sqlRetrieveIowa
)

console_buttons = [
    create_button(
        style=ButtonStyle.primary,
        label="SMMS",
        emoji="🦝",
        custom_id="SMMS"
    )
]

console_chan_select = create_select(
    options=[
        create_select_option(
            label="General",
            value="SMMS_general"
        ),
        create_select_option(
            label="Recruiting",
            value="SMMS_recruiting"
        ),
        create_select_option(
            label="War Room",
            value="SMMS_war"
        )
    ],
    custom_id="SMMS_select",
    min_values=1,
    max_values=1,
    placeholder="What channel do you want to send to?"
)

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
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Tarmac",
        custom_id="role_hype_tarmac",
        emoji="🛫"
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Remove Hype Roles",
        custom_id="role_hype_none",
        emoji="🕳"
    )
]

buttons_roles_food = [
    create_button(
        style=ButtonStyle.gray,
        label="Potato Gang",
        custom_id="role_food_potato",
        emoji="🥔",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Asparagang",
        custom_id="role_food_asparagang",
        emoji="💚",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Runza",
        custom_id="role_food_runza",
        emoji="🥪",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Qdoba's Witness",
        custom_id="role_food_qdoba",
        emoji="🌯",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Aldi's Nuts",
        custom_id="role_food_aldi",
        emoji="🥜",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Remove Food Roles",
        custom_id="roles_food_remove",
        emoji="🕳"
    )
]

buttons_roles_culture = [
    create_button(
        style=ButtonStyle.gray,
        label="Meme Team",
        custom_id="role_culture_meme",
        emoji="😹",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="He Man Isms Hater Club",
        custom_id="role_culture_isms",
        emoji="♣",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Packer Backer",
        custom_id="role_culture_packer",
        emoji="🧀",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Pixel Gang",
        custom_id="role_culture_pixel",
        emoji="📱",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Airpod Gang",
        custom_id="role_culture_airpod",
        emoji="🎧",
    ),
    create_button(
        style=ButtonStyle.gray,
        label="Remove Culture Roles",
        custom_id="roles_culture_remove",
        emoji="🕳"
    )
]


async def process_gameday(mode: bool, guild: discord.Guild):
    gameday_category = guild.get_channel(CAT_GAMEDAY)
    general_category = guild.get_channel(CAT_GENERAL)
    everyone = guild.get_role(ROLE_EVERYONE_PROD)

    print(f"### ~~~ Creating permissions to be [{mode}]")

    perms_text = discord.PermissionOverwrite()
    perms_text.view_channel = mode
    perms_text.send_messages = mode
    perms_text.read_messages = mode

    perms_text_opposite = discord.PermissionOverwrite()
    perms_text_opposite.send_messages = not mode

    perms_voice = discord.PermissionOverwrite()
    perms_voice.view_channel = mode
    perms_voice.connect = mode
    perms_voice.speak = mode

    print("### ~~~ Permissions created")

    for channel in general_category.channels:

        if channel.id in CHAN_HYPE_GROUP:
            continue

        try:
            print(f"### ~~~ Attempting to changes permissions for [{channel}] to [{not mode}]")

            if channel.type == discord.ChannelType.text:
                await channel.set_permissions(everyone, overwrite=perms_text_opposite)
                print(f"### ~~~ Changed permissions for [{channel}] to [{not mode}]")
        except:
            print(f"### ~~~ Unable to change permissions for [{channel}] to [{not mode}]")
            continue

    for channel in gameday_category.channels:
        try:
            print(f"### ~~~ Attempting to changes permissions for [{channel}] to [{mode}]")

            if channel.type == discord.ChannelType.text:
                await channel.set_permissions(everyone, overwrite=perms_text)
            elif channel.type == discord.ChannelType.voice:
                await channel.set_permissions(everyone, overwrite=perms_voice)
            else:
                print(f"### ~~~ Unable to change permissions for [{channel}] to [{mode}]")
                continue
            print(f"### ~~~ Changed permissions for [{channel}] to [{mode}]")
        except discord.errors.Forbidden:
            raise CommandError("The bot does not have access to change permissions!")
        except:
            continue

    print("### ~~~ All permisisons changes applied")


class AdminCommands(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot

    @cog_ext.cog_slash(
        name="about",
        description="All about Bot Frost!",
        guild_ids=guild_id_list()
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
                    ["Birthday", f"I was born on {self.bot.user.created_at}"],
                    ["Feeling generous?", f"Check out `/donate` to help out the production and upkeep of the bot."]
                ]
            )
        )

    @cog_ext.cog_slash(
        name="quit",
        description="Admin or mod only: Turn off the bot",
        guild_ids=guild_id_list(),
        permissions=admin_mod_perms
    )
    async def _quit(self, ctx: SlashContext):
        await ctx.send(f"Good bye world! 😭 I was turned off by [{ctx.author}].")
        await self.bot.logout()

    @cog_ext.cog_slash(
        name="donate",
        description="Donate to the cause!",
        guild_ids=guild_id_list()
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
        base_description="Admin only: Delete messages",
        name="everything",
        description="Admin only: Deletes up to 100 of the previous messages",
        guild_ids=guild_id_list(),
        base_permissions=admin_perms
    )
    async def _everything(self, ctx: SlashContext):
        if ctx.subcommand_passed is not None:
            return

        if ctx.channel.id in CHAN_BANNED:
            return

        await ctx.defer(hidden=True)

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

        await ctx.send(hidden=True, content="Done!")

    @cog_ext.cog_subcommand(
        base="purge",
        base_description="Admin only: Delete messages",
        name="bot",
        description="Admin only: Deletes previous bot messages",
        guild_ids=guild_id_list(),
        base_permissions=admin_perms
    )
    async def _bot(self, ctx: SlashContext):
        if ctx.subcommand_passed is not None:
            return

        if ctx.channel.id in CHAN_BANNED:
            return

        await ctx.defer(hidden=True)

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

        await ctx.send(hidden=True, content="Done!")

    @cog_ext.cog_slash(
        name="submit",
        description="Report something on GitHub",
        guild_ids=guild_id_list(),
        # options=[
        #     create_option(
        #         name="bug",
        #         description="Submit a bug report",
        #         option_type=1,
        #         required=False
        #     ),
        #     create_option(
        #         name="feature",
        #         description="Submit feature request",
        #         option_type=1,
        #         required=False
        #     )
        # ]
    )
    async def _submit(self, ctx: SlashContext):
        pass

    @cog_ext.cog_subcommand(
        base="submit",
        name="bug",
        description="Submit a bug report",
        guild_ids=guild_id_list()
    )
    async def _submit_bug(self, ctx: SlashContext):
        embed = build_embed(
            title=f"Bug Reporter",
            description="[Submit a bug report here](https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=bug&template=bug_report.md&title=%5BBUG%5D+)",
            author=None,
            image=None,
            thumbnail=None
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_subcommand(
        base="submit",
        name="feature",
        description="Submit feature request",
        guild_ids=guild_id_list()
    )
    async def _submit_feature(self, ctx: SlashContext):
        embed = build_embed(
            title=f"Feature Request",
            description="[Submit a feature request here](https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=request&template=feature_request.md&title=%5BREQUEST%5D+)",
            author=None,
            image=None,
            thumbnail=None
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_subcommand(
        base="roles",
        base_description="Manage your roles",
        name="hype",
        description="Assign hype roles",
        guild_ids=guild_id_list()
    )
    async def _roles_hype(self, ctx: SlashContext):
        print("### Roles: Hype Squad")

        hype_action_row = create_actionrow(*buttons_roles_hype)

        embed = build_embed(
            title="Which Nebraska hype squad do you belong to?",
            description="Selecting a squad assigns you a role",
            inline=False,
            fields=[
                ["📈 Max Hype", "Believe Nebraska will be great always"],
                ["⚠ Some Hype", "Little hype or uncertain of Nebraska's performance"],
                ["⛔ No Hype", "Nebraska will not be good and I expect this"],
                ["🛫 Tarmac Gang", "FROST MUST BE LEFT ON THE TARMAC"],
                ["🕳 None", "Remove hype roles"]
            ]
        )

        await ctx.send(embed=embed, components=[hype_action_row])

    @cog_ext.cog_component(components=buttons_roles_hype)
    async def process_roles_hype(self, ctx: ComponentContext):
        await ctx.defer()

        print("### ~~~ Gathering roles")

        hype_max = ctx.guild.get_role(ROLE_HYPE_MAX)
        hype_some = ctx.guild.get_role(ROLE_HYPE_SOME)
        hype_no = ctx.guild.get_role(ROLE_HYPE_NO)
        hype_tarmac = ctx.guild.get_role(ROLE_TARMAC)

        if any([hype_max, hype_some, hype_no]) is None:
            raise CommandError("Unable to locate role!")

        if ctx.custom_id == "role_hype_max":
            await ctx.author.add_roles(hype_max, reason="Hype squad")
            await ctx.author.remove_roles(hype_tarmac, hype_some, hype_no, reason="Hype squad")
            chosen_hype = hype_max.mention
        elif ctx.custom_id == "role_hype_some":
            await ctx.author.add_roles(hype_some, reason="Hype squad")
            await ctx.author.remove_roles(hype_tarmac, hype_max, hype_no, reason="Hype squad")
            chosen_hype = hype_some.mention
        elif ctx.custom_id == "role_hype_no":
            await ctx.author.add_roles(hype_no, reason="Hype squad")
            await ctx.author.remove_roles(hype_tarmac, hype_some, hype_max, reason="Hype squad")
            chosen_hype = hype_no.mention
        elif ctx.custom_id == "role_hype_tarmac":
            await ctx.author.add_roles(hype_tarmac, reason="Hype squad")
            await ctx.author.remove_roles(hype_no, hype_some, hype_max, reason="Hype squad")
            chosen_hype = hype_tarmac.mention
        elif ctx.custom_id == "role_hype_none":
            await ctx.author.remove_roles(hype_tarmac, hype_no, hype_some, hype_max, reason="Hype squad")
            embed = build_embed(
                description=f"{ctx.author.mention} has left all hype roles.",
                image=None,
                thumbnail=None,
                author=None,
                footer="This message will disappear after 10 seconds."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        else:
            return

        embed = build_embed(
            description=f"{ctx.author.mention} has joined: {chosen_hype}.",
            image=None,
            thumbnail=None,
            author=None,
            footer="This message will disappear after 10 seconds."
        )
        await ctx.send(embed=embed, delete_after=10)

        print("### Roles: Hype Squad")

    @cog_ext.cog_subcommand(
        base="roles",
        base_description="Manage your roles",
        name="food",
        description="Assign food roles",
        guild_ids=guild_id_list()
    )
    async def _roles_food(self, ctx: SlashContext):
        print("### Roles: Food")

        embed = build_embed(
            title="Which food roles do you want?",
            description="Assign yourself a role",
            inline=False,
            fields=[
                ["🥔 Potato Gang", "Potatoes are better than asparagus"],
                ["💚 Asparagang", "Asparagus are better than potatoes"],
                ["🥪 Runza", "r/unza"],
                ["🌯 Qdoba's Witness", "Qdoba is better than Chipotle"],
                ["🥜 Aldi's Nuts", "Aldi Super Fan"],
                ["🕳 None", "Remove food roles"]
            ]
        )

        food_action_row = spread_to_rows(*buttons_roles_food, max_in_row=2)

        await ctx.send(embed=embed, components=food_action_row)

    @cog_ext.cog_component(components=buttons_roles_food)
    async def process_roles_food(self, ctx: ComponentContext):
        await ctx.defer()

        print("### ~~~ Gathering roles")

        food_potato = ctx.guild.get_role(ROLE_POTATO)
        food_asparagus = ctx.guild.get_role(ROLE_ASPARAGUS)
        food_runza = ctx.guild.get_role(ROLE_RUNZA)
        food_qdoba = ctx.guild.get_role(ROLE_QDOBA)
        food_aldi = ctx.guild.get_role(ROLE_ALDIS)

        if any([food_potato, food_asparagus, food_runza, food_qdoba, food_aldi]) is None:
            raise CommandError("Unable to locate role!")

        if ctx.custom_id == "role_food_potato":
            await ctx.author.add_roles(food_potato, reason="Hype squad")
            chosen_food = food_potato.mention
        elif ctx.custom_id == "role_food_asparagang":
            await ctx.author.add_roles(food_asparagus, reason="Hype squad")
            chosen_food = food_asparagus.mention
        elif ctx.custom_id == "role_food_runza":
            await ctx.author.add_roles(food_runza, reason="Hype squad")
            chosen_food = food_runza.mention
        elif ctx.custom_id == "role_food_qdoba":
            await ctx.author.add_roles(food_qdoba, reason="Hype squad")
            chosen_food = food_qdoba.mention
        elif ctx.custom_id == "role_food_aldi":
            await ctx.author.add_roles(food_aldi, reason="Hype squad")
            chosen_food = food_aldi.mention
        elif ctx.custom_id == "roles_food_remove":
            await ctx.author.remove_roles(food_potato, food_asparagus, food_runza, food_qdoba, food_aldi, reason="Hype squad")
            embed = build_embed(
                description=f"{ctx.author.mention} has left all food roles.",
                image=None,
                thumbnail=None,
                author=None,
                footer="This message will disappear after 10 seconds."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        else:
            return

        embed = build_embed(
            description=f"{ctx.author.mention} has joined: {chosen_food}.",
            image=None,
            thumbnail=None,
            author=None,
            footer="This message will disappear after 10 seconds."
        )
        await ctx.send(embed=embed, delete_after=10)

        print("### Roles: Food")

    @cog_ext.cog_subcommand(
        base="roles",
        base_description="Manage your roles",
        name="culture",
        description="Assign culture roles",
        guild_ids=guild_id_list()
    )
    async def _roles_culture(self, ctx: SlashContext):
        print("### Roles: Culture")

        embed = build_embed(
            title="Which culture roles do you want?",
            description="Assign yourself a role",
            inline=False,
            fields=[
                ["😹 Meme team", "Memes are life"],
                ["♣ He Man Isms Hater Club", "Idontbelieveinisms sucks"],
                ["🧀 Packer Backer", "Green Bay fan"],
                ["📱 Pixel Gang", "Android fan"],
                ["🎧 Airpod Gang", "Apple fan"],
                ["🕳 None", "Remove food roles"]
            ]
        )

        culture_action_row = spread_to_rows(*buttons_roles_culture, max_in_row=2)

        await ctx.send(embed=embed, components=culture_action_row)

    @cog_ext.cog_component(components=buttons_roles_culture)
    async def process_roles_culture(self, ctx: ComponentContext):
        await ctx.defer()

        print("### ~~~ Gathering roles")

        culture_meme = ctx.guild.get_role(ROLE_MEME)
        culture_isms = ctx.guild.get_role(ROLE_ISMS)
        culiture_packer = ctx.guild.get_role(ROLE_PACKER)
        culture_pixel = ctx.guild.get_role(ROLE_PIXEL)
        culture_airpod = ctx.guild.get_role(ROLE_AIRPOD)

        if any([culture_meme, culture_isms, culiture_packer, culture_pixel, culture_airpod]) is None:
            raise CommandError("Unable to locate role!")

        if ctx.custom_id == "role_culture_meme":
            await ctx.author.add_roles(culture_meme, reason="Hype squad")
            chosen_food = culture_meme.mention
        elif ctx.custom_id == "role_culture_isms":
            await ctx.author.add_roles(culture_isms, reason="Hype squad")
            chosen_food = culture_isms.mention
        elif ctx.custom_id == "role_culture_packer":
            await ctx.author.add_roles(culiture_packer, reason="Hype squad")
            chosen_food = culiture_packer.mention
        elif ctx.custom_id == "role_culture_pixel":
            await ctx.author.add_roles(culture_pixel, reason="Hype squad")
            chosen_food = culture_pixel.mention
        elif ctx.custom_id == "role_culture_airpod":
            await ctx.author.add_roles(culture_airpod, reason="Hype squad")
            chosen_food = culture_airpod.mention
        elif ctx.custom_id == "roles_culture_remove":
            await ctx.author.remove_roles(culture_meme, culture_isms, culiture_packer, culture_pixel, culture_airpod, reason="Hype squad")
            embed = build_embed(
                description=f"{ctx.author.mention} has left all culture roles.",
                image=None,
                thumbnail=None,
                author=None,
                footer="This message will disappear after 10 seconds."
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        else:
            return

        embed = build_embed(
            description=f"{ctx.author.mention} has joined: {chosen_food}.",
            image=None,
            thumbnail=None,
            author=None,
            footer="This message will disappear after 10 seconds."
        )
        await ctx.send(embed=embed, delete_after=10)

        print("### Roles: Culture")

    @cog_ext.cog_subcommand(
        base="gameday",
        base_description="Admin only: Turn game day mode on or off",
        name="on",
        description="Turn game day mode on",
        guild_ids=guild_id_list(),
        base_permissions=admin_perms
    )
    async def _gameday_on(self, ctx: SlashContext):
        print("### Game Day: On")
        await process_gameday(True, ctx.guild)
        embed = build_embed(
            title="Game Day Mode",
            inline=False,
            description="Game day mode is now on for the server! ",
            fields=[
                ["Live TV", "Live TV text and voice channels are for users who are watching live."],
                ["Streaming", "Streaming text and voice channels are for users who are streaming the game."],
                ["Info", "All game chat belongs in these channels until Game Day mode is turned off."]
            ]
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_subcommand(
        base="gameday",
        base_description="Admin only: Turn game day mode on or off",
        name="off",
        description="Turn game day mode off",
        guild_ids=guild_id_list(),
        base_permissions=admin_perms
    )
    async def _gameday_off(self, ctx: SlashContext):
        print("### Game Day: Off")
        await process_gameday(False, ctx.guild)
        embed = build_embed(
            title="Game Day Mode",
            inline=False,
            description="Game day mode is now off for the server! ",
            fields=[
                ["Info", "Normal discussion may resume outside game day channels."]
            ]
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="commands",
        description="Show all slash commands. This replaced $help",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="command_name",
                description="Name of the command you want to view",
                option_type=3,
                required=False
            )
        ]
    )
    async def _commands(self, ctx: SlashContext, command_name: str = None):
        def command_embed(cur_cmd, cur_options) -> discord.Embed:
            opts = ""
            for copt in cur_options:
                opts += f"» {copt['name']} ({'Required' if copt['required'] else 'Optional'}): {copt['description']}\n"
            return build_embed(
                title="Bot Frost Commands",
                fields=[
                    ["Command Name", cur_cmd.name],
                    ["Description", cur_cmd.description],
                    ["Options", opts if opts != "" else "N/A"]
                ]
            )

        if not command_name:
            pages = []
            for command in ctx.slash.commands:
                if not type(ctx.slash.commands[command]) == dict:
                    pages.append(
                        command_embed(
                            ctx.slash.commands[command],
                            ctx.slash.commands[command].options
                        )
                    )
            await Paginator(
                bot=ctx.bot,
                ctx=ctx,
                pages=pages,
                useSelect=False,
                useIndexButton=True
            ).run()
        else:
            command_name = command_name.lower()
            await ctx.send(
                embed=command_embed(
                    ctx.slash.commands[command_name],
                    ctx.slash.commands[command_name].options
                ),
                hidden=True
            )

    @cog_ext.cog_slash(
        name="iowa",
        description="Admin and Mod only: Sends members to Iowa",
        guild_ids=guild_id_list(),
        permissions=admin_mod_perms
    )
    async def _iowa(self, ctx: SlashContext, who: discord.Member, reason: str):
        await ctx.defer()

        if not who:
            raise UserError("You must include a user!")

        if not reason:
            raise UserError("You must include a reason why!")

        role_timeout = ctx.guild.get_role(ROLE_TIME_OUT)
        channel_iowa = ctx.guild.get_channel(CHAN_IOWA)
        full_reason = f"Time Out by {ctx.author}: " + reason

        previous_roles = [str(role.id) for role in who.roles[1:]]
        if previous_roles:
            previous_roles = ",".join(previous_roles)

        roles = who.roles
        for role in roles:
            try:
                await who.remove_roles(role, reason=full_reason)
            except (discord.Forbidden, discord.HTTPException):
                pass

        try:
            await who.add_roles(role_timeout, reason=full_reason)
        except (discord.Forbidden, discord.HTTPException):
            pass

        Process_MySQL(
            query=sqlInsertIowa,
            values=(who.id, full_reason, previous_roles)
        )

        await channel_iowa.send(f"[ {who.mention} ] has been sent to {channel_iowa.mention}.")

        embed = build_embed(
            title="Banished to Iowa",
            inline=False,
            fields=[
                ["Statement", f"[{who.mention}] has had all roles removed and been sent to Iowa. Their User ID has been recorded and {role_timeout.mention} will be reapplied on rejoining the server."],
                ["Reason", full_reason]
            ]
        )
        await ctx.send(embed=embed)
        await who.send(f"You have been moved to [ {channel_iowa.mention} ] for the following reason: {reason}.")

    @cog_ext.cog_slash(
        name="nebraska",
        description="Admin and Mod only: Bring a member back from Iowa",
        guild_ids=guild_id_list(),
        permissions=admin_mod_perms
    )
    async def _nebraska(self, ctx: SlashContext, who: discord.Member):
        await ctx.defer()

        if not who:
            raise UserError("You must include a user!")

        role_timeout = ctx.guild.get_role(ROLE_TIME_OUT)
        await who.remove_roles(role_timeout)

        previous_roles_raw = Process_MySQL(
            query=sqlRetrieveIowa,
            values=who.id,
            fetch="all"
        )

        previous_roles = previous_roles_raw[0]["previous_roles"].split(",")

        try:
            if previous_roles:
                for role in previous_roles:
                    new_role = ctx.guild.get_role(int(role))
                    await who.add_roles(new_role, reason="Returning from Iowa")
        except (discord.Forbidden, discord.HTTPException):
            pass

        Process_MySQL(
            query=sqlRemoveIowa,
            values=who.id
        )

        iowa = ctx.guild.get_channel(CHAN_IOWA)

        embed = build_embed(
            title="Return to Nebraska",
            inline=False,
            fields=[
                ["Welcome back!", f"[{who.mention}] is welcomed back to Nebraska!"],
                ["Welcomed by", ctx.author.mention]
            ]
        )
        await ctx.send(embed=embed)
        await iowa.send(f"[ {who.mention} ] has been sent back to Nebraska.")

    @cog_ext.cog_slash(
        name="console",
        description="Admin or Mod only",
        guild_ids=guild_id_list(),
        permissions=admin_mod_perms
    )
    async def _console(self, ctx: SlashContext):

        console_actionrow = create_actionrow(*console_buttons)
        await ctx.send(content="Shh..", hidden=True)
        await ctx.send(content="Shh...", components=[console_actionrow], hidden=True)

    @cog_ext.cog_component(components=console_buttons)
    async def process_console(self, ctx: ComponentContext):
        if ctx.custom_id == "SMMS":
            chan_select_actionrow = create_actionrow(console_chan_select)
            await ctx.send("Choose a channel.", hidden=True, components=[chan_select_actionrow])

    @cog_ext.cog_component(components=console_chan_select)
    async def process_console_channel(self, ctx: ComponentContext):
        await ctx.send("What is your message?", hidden=True)
        try:
            def validate(messsage):
                if messsage.channel.id == ctx.channel_id and messsage.author.id == ctx.author_id:
                    return True
                else:
                    return False

            user_input = await self.bot.wait_for("message", check=validate)
            user_msg = user_input.clean_content
            await user_input.delete()
            del user_input
        except asyncio.TimeoutError:
            return

        embed = build_embed(
            title="Secret Mammal Message System (SMMS)",
            thumbnail="https://i.imgur.com/EGC1qNt.jpg",
            footer=BOT_FOOTER_SECRET,
            fields=[
                ["Back Channel Communication", user_msg]
            ]
        )

        chan = None

        if ctx.values[0] == "SMMS_general":
            chan = ctx.guild.get_channel(CHAN_GENERAL)
        elif ctx.values[0] == "SMMS_recruiting":
            chan = ctx.guild.get_channel(CHAN_SCOTT)
        elif ctx.values[0] == "SMMS_war":
            chan = ctx.guild.get_channel(CHAN_WAR_ROOM)

        if chan is not None:
            await chan.send(embed=embed)
        else:
            await ctx.send("Hiccup!", hidden=True)


def setup(bot):
    bot.add_cog(AdminCommands(bot))

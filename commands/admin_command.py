import discord
from discord.ext import commands
from discord.ext.commands import Cog

from utilities.constants import CHAN_BOTLOGS, CHAN_NORTH_BOTTTOMS, CHAN_RULES, CHAN_IOWA
from utilities.constants import ROLE_ADMIN_PROD, ROLE_ADMIN_TEST
from utilities.constants import ROLE_MOD_PROD, ROLE_TIME_OUT
from utilities.embed import build_embed as build_embed
from utilities.mysql import Process_MySQL, sqlInsertIowa, sqlRemoveIowa, sqlRetrieveIowa


def not_botlogs(chan: discord.TextChannel):
    return chan.id == CHAN_BOTLOGS


class AdminCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.command(aliases=["gd", ])
    # @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    # async def gameday(self, ctx, toggle: str):
    #     toggle_options = ("on", "off")
    #
    #     if not toggle.lower() in toggle_options:
    #         raise AttributeError("Invalid toggle! Options are \"on\" or \"off\".")
    #
    #     # _now = datetime.datetime.now().astimezone(tz=TZ)
    #     # games, stats = HuskerSchedule(year=_now.year)
    #     # del stats
    #     #
    #     # for game in games:
    #     #     if game.game_date_time > _now:
    #     #         diff = game.game_date_time - _now
    #     #         _hour = 60 * 60
    #     #         if diff.seconds >= _hour:
    #     #             raise AttributeError("This command can only be turned on 1 hour before the schedule game start!")
    #     #         elif game.game_date_time > _now and diff.seconds <= -(_hour * 5):
    #     #             raise AttributeError("This command can only be turned off after 5 hours from kick off!")
    #
    #     ROLE_EVERYONE_ID = 440632686185414677
    #     ROLE_EVERYONE = ctx.guild.get_role(ROLE_EVERYONE_ID)
    #
    #     if ROLE_EVERYONE is None:
    #         raise AttributeError("Unable to find `@everyone` role!")
    #
    #     GAMEDAY_CATEGORY_ID = 768828439636606996
    #     GAMEDAY_CATEGORY = self.bot.get_channel(GAMEDAY_CATEGORY_ID)
    #
    #     perms = discord.PermissionOverwrite()
    #
    #     GENERAL_ID = 440868279150444544
    #     GENERAL_CHANNEL = self.bot.get_channel(GENERAL_ID)
    #
    #     if toggle.lower() == "on":
    #         perms.send_messages = True
    #         perms.read_messages = True
    #         perms.view_channel = True
    #         perms.connect = True
    #         perms.speak = True
    #
    #         await GENERAL_CHANNEL.send(f"🚨 ❗ Game day mode is now {toggle} for the server! Live TV text and voice channels are for users who are watching live. Streaming text and voice channels are for users who are streaming the game. All game chat belongs in these channels during the game. ❗ 🚨")
    #     elif toggle.lower() == "off":
    #         perms.send_messages = False
    #         perms.read_messages = False
    #         perms.view_channel = False
    #         perms.connect = False
    #         perms.speak = False
    #
    #         await GENERAL_CHANNEL.send(f"🚨 ❗ Game day mode is now {toggle} for the server! Normal server discussion may resume! ❗ 🚨")
    #
    #     await GAMEDAY_CATEGORY.set_permissions(ROLE_EVERYONE, overwrite=perms)

    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def rules(self, ctx):
        unmodded = self.bot.get_channel(id=CHAN_NORTH_BOTTTOMS)
        text = \
            f"""
        1️⃣ Be respectful\n
        2️⃣ Sending or linking any harmful material such as viruses, IP grabbers, etc. results in an immediate and permanent ban.\n
        3️⃣ Abusing mentions to @everyone, the admins, the moderators (Frost Approved) or a specific person without proper reason is prohibited.\n
        4️⃣ Act civil in all chats. {unmodded.mention} is the only unmoderated channel (with the exception of illegal activity).\n
        5️⃣ Post content in the correct channels.\n
        6️⃣ Absolutely no posting of personal information of others (doxxing).\n
        7️⃣ Do not post graphic text or pictures of minors (<18yo)\n
        8️⃣ Fuck Iowa, Colorado, Texas, Florida\n
        9️⃣ All NSFW Images must be spoiler tagged
        """
        rules_channel = self.bot.get_channel(CHAN_RULES)
        rules_title = "Huskers' Discord Rules"
        messages = await rules_channel.history().flatten()

        for message in messages:
            if message.author == self.bot.user and message.embeds[0].title == rules_title:
                new_embed = message.embeds[0]
                new_embed.clear_fields()
                new_embed.add_field(name="Rules", value=text)
                await message.edit(content="", embed=new_embed)

                return

        del messages

        await ctx.send(
            embed=build_embed(
                title=rules_title,
                fields=[["Rules", text]]
            )
        )

    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def roles(self, ctx):
        roles = """
        Below are a list of vanity roles you can add or remove whenever you like by reacting to this message:\n
        Potato Gang (🥔)\n
        Asparagang (💚)\n
        /r/unza (🥪)\n
        Meme Team (😹)\n
        He Man, Isms Hater Club (♣)\n
        Packer Backer (🧀)\n
        Pixel Gang (☎)\n
        Airpod Gang (🎧)\n
        Minecraft (🪓)
        """
        roles_emojis = ("🥔", "💚", "🥪", "😹", "♣", "🧀", "☎", "🎧", "🪓")

        rules_channel = self.bot.get_channel(CHAN_RULES)
        messages = await rules_channel.history().flatten()
        roles_title = "Huskers' Discord Roles"

        for message in messages:
            if message.author == self.bot.user and message.embeds[0].title == roles_title:
                new_embed = message.embeds[0]
                new_embed.clear_fields()
                new_embed.add_field(name="Rules", value=roles)
                await message.edit(content="", embed=new_embed)
                await message.clear_reactions()
                for emoji in roles_emojis:
                    await message.add_reaction(emoji)

                return

        del messages

        rules_message = await rules_channel.send(
            embed=build_embed(
                title=roles_title,
                fields=[["Roles", roles]]
            )
        )

        for emoji in roles_emojis:
            await rules_message.add_reaction(emoji)

    # @commands.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_TEST, ROLE_ADMIN_PROD, ROLE_MOD_PROD)
    async def iowa(self, ctx, who: discord.Member, *, reason: str):
        """ Removes all roles from a user, applies the @Time Out role, and records the user's ID to prevent leaving and rejoining to remove @Time Out """
        if not who:
            raise AttributeError("You must include a user!")

        if not reason:
            raise AttributeError("You must include a reason why!")

        timeout = ctx.guild.get_role(ROLE_TIME_OUT)
        iowa = ctx.guild.get_channel(CHAN_IOWA)
        added_reason = f"Time Out by {ctx.message.author}: "

        roles = who.roles
        previous_roles = [str(role.id) for role in who.roles[1:]]
        if previous_roles:
            previous_roles = ",".join(previous_roles)

        for role in roles:
            try:
                await who.remove_roles(role, reason=added_reason + reason)
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

        try:
            await who.add_roles(timeout, reason=added_reason + reason)
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        Process_MySQL(
            query=sqlInsertIowa,
            values=(who.id, added_reason + reason, previous_roles)
        )

        await iowa.send(f"[ {who.mention} ] has been sent to {iowa.mention}.")
        await ctx.send(
            f"[ {who} ] has had all roles removed and been sent to Iowa. Their User ID has been recorded and {timeout.mention} will be reapplied on rejoining the server.")
        await who.send(f"You have been moved to [ {iowa.mention} ] for the following reason: {reason}.")

    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_TEST, ROLE_ADMIN_PROD, ROLE_MOD_PROD)
    async def nebraska(self, ctx, who: discord.Member):
        if not who:
            raise AttributeError("You must include a user!")

        timeout = ctx.guild.get_role(ROLE_TIME_OUT)
        await who.remove_roles(timeout)

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
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        Process_MySQL(
            query=sqlRemoveIowa,
            values=who.id
        )

        iowa = ctx.guild.get_channel(CHAN_IOWA)

        await ctx.send(f"[ {who} ] is welcome back to Nebraska.")
        await iowa.send(f"[ {who.mention} ] has been sent back to Nebraska.")

    # @commands.command()
    # async def bug(self, ctx):
    #     await ctx.send(embed=build_embed(
    #         title=f"Bug Reporter",
    #         fields=[
    #             ["Report Bugs",
    #              "https://github.com/refekt/Bot-Frost/issues/new?assignees=&labels=bug&template=bug_report.md&title="]
    #         ]
    #     ))


def setup(bot):
    bot.add_cog(AdminCommands(bot))

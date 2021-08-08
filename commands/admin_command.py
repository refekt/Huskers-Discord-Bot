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



def setup(bot):
    bot.add_cog(AdminCommands(bot))

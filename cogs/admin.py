import datetime

import discord
from discord.ext import commands

from utils.consts import CHAN_RULES, CHAN_BOTLOGS, CHAN_NORTH_BOTTTOMS, CHAN_IOWA
from utils.consts import EMBED_TITLE_HYPE
from utils.consts import GUILD_PROD
from utils.consts import REACITON_HYPE_SQUAD
from utils.consts import ROLE_ADMIN_PROD, ROLE_ADMIN_TEST, ROLE_HYPE_SOME, ROLE_HYPE_NO, ROLE_HYPE_MAX, ROLE_MOD_PROD, \
    ROLE_TIME_OUT
from utils.consts import TZ
from utils.embed import build_embed as build_embed
from utils.games import HuskerSchedule
from utils.mysql import process_MySQL, sqlInsertIowa, sqlRemoveIowa, sqlRetrieveIowa


def not_botlogs(chan: discord.TextChannel):
    return chan.id == CHAN_BOTLOGS


class AdminCommands(commands.Cog, name="Admin Commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["gd", ])
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def gameday(self, ctx, toggle: str):
        toggle_options = ("on", "off")

        if not toggle.lower() in toggle_options:
            raise AttributeError("Invalid toggle! Options are \"on\" or \"off\".")

        _now = datetime.datetime.now().astimezone(tz=TZ)
        games, stats = HuskerSchedule(year=_now.year)
        del stats

        for game in games:
            if game.game_date_time > _now:
                diff = game.game_date_time - _now
                _hour = 60 * 60
                if diff.seconds >= _hour:
                    raise AttributeError("This command can only be turned on 1 hour before the schedule game start!")
                elif diff.seconds <= -(_hour * 5):
                    raise AttributeError("This command can only be turned off after 5 hours from kick off!")

        ROLE_EVERYONE_ID = 440632686185414677
        ROLE_EVERYONE = ctx.guild.get_role(ROLE_EVERYONE_ID)

        if ROLE_EVERYONE is None:
            raise AttributeError("Unable to find `@everyone` role!")

        GAMEDAY_CATEGORY_ID = 768828439636606996
        GAMEDAY_CATEGORY = self.bot.get_channel(GAMEDAY_CATEGORY_ID)

        perms = discord.PermissionOverwrite()

        GENERAL_ID = 440868279150444544
        GENERAL_CHANNEL = self.bot.get_channel(GENERAL_ID)

        if toggle.lower() == "on":
            perms.send_messages = True
            perms.read_messages = True
            perms.view_channel = True
            perms.connect = True
            perms.speak = True

            await GENERAL_CHANNEL.send(f"🚨 ❗ Game day mode is now {toggle} for the server! Live TV text and voice channels are for users who are watching live. Streaming text and voice channels are for users who are streaming the game. All game chat belongs in these channels during the game. ❗ 🚨")
        elif toggle.lower() == "off":
            perms.send_messages = False
            perms.read_messages = False
            perms.view_channel = False
            perms.connect = False
            perms.speak = False

            await GENERAL_CHANNEL.send(f"🚨 ❗ Game day mode is now {toggle} for the server! Normal server discussion may resume! ❗ 🚨")

        await GAMEDAY_CATEGORY.set_permissions(ROLE_EVERYONE, overwrite=perms)

    @commands.command()
    async def about(self, ctx):
        """ All about Bot Frost """
        import platform

        await ctx.send(
            embed=build_embed(
                title="About Me",
                inline=False,
                fields=[
                    ["History",
                     "Bot Frost was created and developed by [/u/refekt](https://reddit.com/u/refekt) and [/u/psyspoop](https://reddit.com/u/psyspoop). Jeyrad and ModestBeaver assisted with the creation greatly!"],
                    ["Source Code", "[GitHub](https://www.github.com/refekt/Husker-Bot)"],
                    ["Hosting Location",
                     f"{'Local Machine' if 'Windows' in platform.platform() else 'Virtual Private Server'}"],
                    ["Hosting Status", "https://status.hyperexpert.com/"],
                    ["Latency", f"{self.bot.latency * 1000:.2f} ms"],
                    ["Username", self.bot.user.mention],
                    ["Feeling generous?",
                     f"Check out `{self.bot.command_prefix}donate` to help out the production and upkeep of the bot."]
                ]
            )
        )

    @commands.command()
    async def donate(self, ctx):
        """ Donate to the cause """

        await ctx.send(
            embed=build_embed(
                title="Donation Information",
                inline=False,
                thumbnail="https://i.imgur.com/53GeCvm.png",
                fields=[
                    ["About",
                     "I hate asking for donations; however, the bot has grown to the point where official server hosting is required. Server hosting provides 99% uptime and hardware "
                     "performance I cannot provide with my own hardware. I will be paying for upgraded hosting but donations will help offset any costs."],
                    ["Terms", "(1) Final discretion of donation usage is up to the creator(s). "
                              "(2) Making a donation to the product(s) and/or service(s) does not garner any control or authority over product(s) or service(s). "
                              "(3) No refunds. "
                              "(4) Monthly subscriptions can be terminated by either party at any time. "
                              "(5) These terms can be changed at any time. Please read before each donation. "
                              "(6) Clicking the donation link signifies your agreement to these terms."],
                    ["Donation Link",
                     "[Click Me](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=refekt%40gmail.com&currency_code=USD&source=url)"]
                ]
            )
        )

    @donate.after_invoke
    async def after_donate(self, ctx):
        from utils.mysql import process_MySQL, sqlLogUser
        process_MySQL(query=sqlLogUser,
                      values=(f"{ctx.message.author.name}#{ctx.message.author.discriminator}", "after_donate", "N/A"))

    @commands.group(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def purge(self, ctx):
        """ Deletes up to 100 bot messages """
        if ctx.subcommand_passed:
            return

        if not_botlogs(ctx.message.channel):  # prevent from deleting #botlogs
            return

        msgs = []
        try:
            max_age = datetime.datetime.now() - datetime.timedelta(days=13, hours=23,
                                                                   minutes=59)  # Discord only lets you delete 14 day old messages
            async for message in ctx.message.channel.history(limit=100):
                if message.created_at >= max_age and message.author.bot:
                    msgs.append(message)
            await ctx.message.channel.delete_messages(msgs)
            print(f"Bulk delete of {len(msgs)} messages successful.")
        except discord.ClientException:
            print("Cannot delete more than 100 messages at a time.")
        except discord.Forbidden:
            print("Missing permissions.")
        except discord.HTTPException:
            print("Deleting messages failed. Bulk messages possibly include messages over 14 days old.")

    @purge.command()
    async def last(self, ctx):
        """ Delete the last bot message """
        if not_botlogs(ctx.message.channel):  # prevent from deleting #botlogs
            return

        async for message in ctx.message.channel.history(limit=3, oldest_first=False):
            await message.delete()

    @purge.command()
    async def everything(self, ctx):
        """ Delete up to 100 messages in the current channel """
        if not_botlogs(ctx.message.channel):  # prevent from deleting #botlogs
            return

        msgs = []
        try:
            max_age = datetime.datetime.now() - datetime.timedelta(days=13, hours=23,
                                                                   minutes=59)  # Discord only lets you delete 14 day old messages
            async for message in ctx.message.channel.history(limit=100):
                if message.created_at >= max_age:
                    msgs.append(message)
            await ctx.message.channel.delete_messages(msgs)
            print(f"Bulk delete of {len(msgs)} messages successful.")
        except discord.ClientException:
            print("Cannot delete more than 100 messages at a time.")
        except discord.Forbidden:
            print("Missing permissions.")
        except discord.HTTPException:
            print("Deleting messages failed. Bulk messages possibly include messages over 14 days old.")

    @commands.command(aliases=["q", ], hidden=True)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def quit(self, ctx):
        await ctx.send("Good bye world! 😭")
        print(f"User `{ctx.author}` turned off the bot.")
        await self.bot.logout()

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

    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_TEST, ROLE_ADMIN_PROD)
    async def hypesquad(self, ctx):
        chan_rules = self.bot.get_channel(id=CHAN_RULES)
        guild = self.bot.get_guild(GUILD_PROD)

        role_max = guild.get_role(ROLE_HYPE_MAX)
        role_some = guild.get_role(ROLE_HYPE_SOME)
        role_no = guild.get_role(ROLE_HYPE_NO)

        fields = ["What side are you on!?", f"📈 {role_max.mention} believes rationale is a lie and there is only hype.\n"
                                            f"\n"
                                            f"⚠ {role_some.mention} believes in the numbers.\n"
                                            f"\n"
                                            f"⛔ {role_no.mention} is about knowledge, statistics, and models. "]

        rule_messages = await chan_rules.history().flatten()
        for hist in rule_messages:
            if hist.author == self.bot.user and hist.embeds[0].title == EMBED_TITLE_HYPE:
                new_embed = hist.embeds[0]
                new_embed.clear_fields()
                new_embed.add_field(
                    name=fields[0],
                    value=fields[1]
                )

                await hist.edit(content="", embed=new_embed)

                return

        hype_msg = await chan_rules.send(
            embed=build_embed(
                title=EMBED_TITLE_HYPE,
                fields=[
                    fields
                ]
            )
        )

        for reaction in REACITON_HYPE_SQUAD:
            await hype_msg.add_reaction(reaction)

    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def repeat(self, ctx, *, message=""):
        if ctx.channel.type == discord.ChannelType.private:
            channels_list = [channel for channel in self.bot.get_all_channels() if channel.type == discord.ChannelType.text]

            nl = "\n"

            await ctx.message.author.send(f"Which channel:\n{nl.join([c.name.lower() for c in channels_list])}")

            def check_chan(m):
                if m.channel.type == discord.ChannelType.private:
                    for c in channels_list:
                        if c.name.lower() == m.content.lower():
                            return c.id

                return False

            msg = await self.bot.wait_for("message", check=check_chan)

            if msg:
                repeat_channel = None

                for c in channels_list:
                    if c.name.lower() == msg.content.lower():
                        repeat_channel = c
                        break

                if repeat_channel:
                    await ctx.message.author.send("What should I say?")

                    def check_message(m):
                        if m.channel.type == discord.ChannelType.private:
                            return m.content

                    output = await self.bot.wait_for("message", check=check_message)
                    await repeat_channel.send(output.content)
                else:
                    print("wat")
            else:
                await ctx.message.author.send("Not a valid channel.  Start over!")
        else:
            await ctx.send(message)
            await ctx.message.delete()

    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def repeathistory(self, ctx, quantity=20):
        history = await ctx.message.channel.history(limit=quantity).flatten()
        output = [""]
        index = len(output) - 1
        nl = '\n'
        for message in history:

            newmessage = f"▶ Author: {message.author}, Content: {message.clean_content.replace('`', '').replace(nl, '')}\n"

            if len(newmessage) > 2000:
                continue

            comblen = len(output[index] + newmessage)

            if comblen > 2000:
                output.append(newmessage)
                index += 1
            output[index] += newmessage

        message = ""
        for index in output:
            comblen = len(message + index)

            if len(message + index) < 2000:
                message += index
            else:
                await ctx.send(f"```\n{message}\n```")
                message = ""

        await ctx.send(f"```\n{message}\n```")

    @commands.command(hidden=True)
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

        process_MySQL(
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

        previous_roles_raw = process_MySQL(
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

        process_MySQL(
            query=sqlRemoveIowa,
            values=who.id
        )

        iowa = ctx.guild.get_channel(CHAN_IOWA)

        await ctx.send(f"[ {who} ] is welcome back to Nebraska.")
        await iowa.send(f"[ {who.mention} ] has been sent back to Nebraska.")

    @commands.command()
    async def bug(self, ctx):
        await ctx.send(embed=build_embed(
            title=f"Bug Reporter",
            fields=[
                ["Report Bugs",
                 "https://github.com/refekt/Bot-Frost/issues/new?assignees=&labels=bug&template=bug_report.md&title="]
            ]
        ))


def setup(bot):
    bot.add_cog(AdminCommands(bot))

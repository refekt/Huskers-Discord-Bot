import datetime
from utils.consts import chan_rules, chan_botlogs

import discord
from discord.ext import commands

from utils.client import client
from utils.consts import admin_prod, admin_test
from utils.embed import build_embed as build_embed


def not_botlogs(chan: discord.TextChannel):
    return chan.id == chan_botlogs


class AdminCommands(commands.Cog, name="Admin Commands"):
    @commands.command()
    async def about(self, ctx):
        """ All about Bot Frost """
        import platform

        await ctx.send(
            embed=build_embed(
                title="About Me",
                inline=False,
                fields=[
                    ["History", "Bot Frost was created and developed by [/u/refekt](https://reddit.com/u/refekt) and [/u/psyspoop](https://reddit.com/u/psyspoop). Jeyrad and ModestBeaver assisted with the creation greatly!"],
                    ["Source Code", "[GitHub](https://www.github.com/refekt/Husker-Bot)"],
                    ["Hosting Location", f"{'Local Machine' if 'Windows' in platform.platform() else 'Virtual Private Server'}"],
                    ["Latency", f"{client.latency * 1000:.2f} ms"],
                    ["Username", client.user.mention]
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
                    ["About", "I hate asking for donations; however, the bot has grown to the point where official server hosting is required. Server hosting provides 99% uptime and hardware "
                              "performance I cannot provide with my own machiens. Donations will go toward the payment of server cost. A top end server will be about $15 a month."],
                    ["Donation Link", "[Click Me](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=refekt%40gmail.com&currency_code=USD&source=url)"]
                ]
            )
        )

    @commands.group(hidden=True)
    @commands.has_any_role(admin_prod, admin_test)
    async def purge(self, ctx):
        """ Deletes up to 100 bot messages """
        if ctx.subcommand_passed:
            return

        if not_botlogs(ctx.message.channel):  # prevent from deleting #botlogs
            return

        msgs = []
        try:
            max_age = datetime.datetime.now() - datetime.timedelta(days=13, hours=23, minutes=59)  # Discord only lets you delete 14 day old messages
            async for message in ctx.message.channel.history(limit=100):
                if message.created_at >= max_age and message.author.bot:
                    msgs.append(message)
            await ctx.message.channel.delete_messages(msgs)
            print("Bulk delete of {} messages successful.".format(len(msgs)))
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
            max_age = datetime.datetime.now() - datetime.timedelta(days=13, hours=23, minutes=59)  # Discord only lets you delete 14 day old messages
            async for message in ctx.message.channel.history(limit=100):
                if message.created_at >= max_age:
                    msgs.append(message)
            await ctx.message.channel.delete_messages(msgs)
            print("Bulk delete of {} messages successful.".format(len(msgs)))
        except discord.ClientException:
            print("Cannot delete more than 100 messages at a time.")
        except discord.Forbidden:
            print("Missing permissions.")
        except discord.HTTPException:
            print("Deleting messages failed. Bulk messages possibly include messages over 14 days old.")

    @commands.command(aliases=["q",], hidden=True)
    @commands.has_any_role(admin_prod, admin_test)
    async def quit(self, ctx):
        await ctx.send("Good bye world! 😭")
        print(f"User `{ctx.author}` turned off the bot.")
        await client.logout()

    @commands.command(hidden=True)
    @commands.has_any_role(admin_prod, admin_test)
    async def rules(self, ctx):
        text = \
        """
        1️⃣ Be respectful\n
        2️⃣ Sending or linking any harmful material such as viruses, IP grabbers, etc. results in an immediate and permanent ban.\n
        3️⃣ Abusing mentions to @everyone, the admins, the moderators (Frost Approved) or a specific person without proper reason is prohibited.\n
        4️⃣ Act civil in all chats. #kingdom-of-no-hype-and-all-moaming is the only authorized channel for overt negative comments.\n
        5️⃣ Post content in the correct channels.\n
        6️⃣ Absolutely no posting of personal information of others (doxxing).\n
        7️⃣ Do not post graphic text or pictures of minors (<18yo)\n
        8️⃣ Fuck Iowa, Colorado, Texas, Florida\n
        9️⃣ All NSFW Images must be spoiler tagged
        """

        rules_channel = client.get_channel(chan_rules)
        rules_title = "Huskers' Discord Rules"
        messages = await rules_channel.history().flatten()

        for message in messages:
            if message.author == client.user and message.embeds[0].title == rules_title:
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
    @commands.has_any_role(admin_prod, admin_test)
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
        """
        roles_emojis = ("🥔", "💚", "🥪", "😹", "♣", "🧀", "☎", "🎧")

        messages = await chan_rules.history().flatten()
        roles_title = "Huskers' Discord Roles"

        for message in messages:
            if message.author == client.user and message.embeds[0].title == roles_title:
                new_embed = message.embeds[0]
                new_embed.clear_fields()
                new_embed.add_field(name="Rules", value=roles)
                await message.edit(content="", embed=new_embed)
                await message.clear_reactions()
                for emoji in roles_emojis:
                    await message.add_reaction(emoji)

                return

        del messages

        rules_message = await chan_rules.send(
            embed=build_embed(
                title=roles_title,
                fields=[["Roles", roles]]
            )
        )

        for emoji in roles_emojis:
            await rules_message.add_reaction(emoji)


def setup(bot):
    bot.add_cog(AdminCommands(bot))


print("### Admin Commands loaded! ###")

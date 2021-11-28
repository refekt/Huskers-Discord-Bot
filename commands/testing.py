import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from utilities.constants import guild_id_list
from datetime import datetime


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### Testing: {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ Testing: {message}")


class TestCommand(commands.Cog):
    @cog_ext.cog_slash(
        name="test",
        description="Test command",
        guild_ids=guild_id_list(),
    )
    async def _test(self, ctx: SlashContext):
        husks_messages = ""
        all_history = []

        await ctx.defer(hidden=True)

        print(datetime.now())

        for index, channel in enumerate(ctx.guild.channels):
            if channel.type == discord.ChannelType.text:
                print(f"[{index} / {len(ctx.guild.channels)}] Searching {channel}")
                all_history.append(await channel.history(limit=2000).flatten())

            # if index == 10:
            #     break

        print(datetime.now())

        history = [value for sublist in all_history for value in sublist]

        for message in history:
            if message.author.id == 598039388148203520:
                if not str(message.clean_content).startswith("http"):
                    husks_messages += f"{message.clean_content}\n"

        husks_messages = str(husks_messages).encode("UTF-8", "ignore")

        f = open("husk_messages.txt", "wb")
        f.write(husks_messages)
        f.close()

        await ctx.send("Done!", hidden=True)


def setup(bot):
    bot.add_cog(TestCommand(bot))

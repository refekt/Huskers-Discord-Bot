# TODO
# * Bot status updates
# * Client events
# * Hall of Fame/Shame
# * Iowa checks
# * Reminders
# * Twitter stream
# * Welcome message
# TODO

import interactions
from interactions import CommandContext
from logging import CRITICAL

from helpers.constants import PROD_TOKEN, GUILD_PROD
from helpers.misc import getUserMention, getBotUser, getGuild, getCurrentGuildID


# threshold: int = 999


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### Main: {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ Main: {message}")


bot = interactions.Client(
    token=PROD_TOKEN, intents=interactions.Intents.ALL, log_level=CRITICAL
)

del PROD_TOKEN


@bot.command(
    name="abc",
    description="Testing sdfkljasdf;lkasjd;fljaskdfasd",
    scope=GUILD_PROD,
)
async def abc(ctx: CommandContext):
    await ctx.send(
        f"You have applied a command onto user {getUserMention(ctx.author.user)}!"
    )


@bot.event
async def on_ready():
    log("Performing on_ready commands...", 1)

    # await bot.synchronize()

    # botUser = await getBotUser(bot)
    # curGuildID = await getCurrentGuildID(bot)
    # curGuild = await getGuild(bot, curGuildID)
    # threshold = curGuild.member_count * 0.0035

    log("on_ready commands complete!", 1)


@bot.event
async def on_connect():
    log("on_connect activated", 0)


@bot.event
async def on_disconnect():
    log("on_disconnect activated", 0)


@bot.event
async def on_message(message):
    log(f"on_message, {message}", 0)


@bot.event
async def on_message_reaction_add(MessageReaction):
    log(f"on_message_reaction_add, {MessageReaction}", 0)


@bot.event
async def message_reaction_add(MessageReaction):
    log(f"message_reaction_add, {MessageReaction}", 0)


@bot.event
async def message_reaction(MessageReaction):
    log(f"message_reaction, {MessageReaction}", 0)


@bot.event
async def on_error(error):
    log(f"on_error, {error}", 0)


log("Starting bot...", 0)

bot.start()

log("Bot finished!", 0)

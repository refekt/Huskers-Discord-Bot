# TODO
# * Bot status updates
# * Client events
# * Hall of Fame/Shame
# * Iowa checks
# * Reminders
# * Twitter stream
# * Welcome message
# TODO

import inspect
from logging import CRITICAL

import interactions

from helpers.constants import PROD_TOKEN


# threshold: int = 999


def log(level: int, message: str):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### Main: {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ Main: {message}")


bot = interactions.Client(
    token=PROD_TOKEN, intents=interactions.Intents.ALL, log_level=CRITICAL
)

del PROD_TOKEN


@bot.event
async def on_ready():
    log(0, f"The bot is ready!")


@bot.event
async def on_channel_pins_update(pin: interactions.ChannelPins):
    log(1, f"A a pin was updated in {pin.channel_id}")


# d-p-i.py bug
# CRITICAL:gateway:(ln.303):You're missing a data model for the event thread_create: module 'interactions' has no attribute 'Thread'
# CRITICAL:gateway:You're missing a data model for the event thread_create: module 'interactions' has no attribute 'Thread'
#
# @bot.event
# async def on_thread_create(
#     channel: interactions.Channel, thread_member: interactions.ThreadMember = None
# ):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_update(channel: interactions.Channel):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_delete(channel: interactions.Channel):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_list_sync():
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_member_update(thread_member: interactions.ThreadMember):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_members_update(thread_member: interactions.ThreadMember):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_create(guild: interactions.Guild):
    log(0, f"Establishing guild connection to: {guild.name}")


@bot.event
async def on_guild_update(guild: interactions.Guild):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_delete(guild: interactions.Guild):
    log(0, f"Loaded {inspect.stack()[0][3]}")


# d-p-i.py bug
# @bot.event
# async def on_guild_ban_add(user: interactions.User):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_guild_ban_remove(user: interactions.User):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_emojis_update(emojis: interactions.GuildEmojis):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_stickers_update(stickers: interactions.GuildStickers):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_member_add(guild_member: interactions.GuildMember):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_member_remove(guild_member: interactions.GuildMember):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_member_update(guild_member: interactions.GuildMember):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_role_create(role: interactions.Role):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_role_update(role: interactions.Role):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_role_delete(role: interactions.Role):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_create(
    scheduled_event: interactions.ScheduledEvents,
):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_update(
    scheduled_event: interactions.ScheduledEvents,
):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_delete(
    scheduled_event: interactions.ScheduledEvents,
):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_user_add(
    scheduled_event: interactions.ScheduledEvents,
    user: interactions.User,
    guild: interactions.Guild,
):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_user_remove(
    scheduled_event: interactions.ScheduledEvents,
    user: interactions.User,
    guild: interactions.Guild,
):
    log(0, f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_invite_create(
    invite: interactions.Invite,
):
    inviter = invite._json.get("inviter")
    code = invite._json.get("code")

    log(
        1,
        f"{inviter['username']}#{inviter['discriminator']} created the {'permanent' if invite.temporary else 'temporary'} invite code {code} at {invite.created_at}.",
    )


@bot.event
async def on_invite_delete(invite: interactions.Invite):
    log(1, f"The invite code {invite._json.get('code')} was deleted.")


# TODO Capture metrics for guild karma
# @bot.event
# async def on_message_create(message: interactions.Message):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)


# TODO Botlogs record?
# @bot.event
# async def on_message_update(message: interactions.Message):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)


# TODO Botlogs record?
# @bot.event
# async def on_message_delete(message: interactions.Message):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)


# TODO Purge commands?
# @bot.event
# async def on_message_delete_bulk(
#     message_ids, channel: interactions.Channel, guild: interactions.Guild
# ):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)


# TODO d-p-i.py bug
# CRITICAL:gateway:(ln.303):You're missing a data model for the event message_reaction_add: module 'interactions' has no attribute 'MessageReaction'
# CRITICAL:gateway:You're missing a data model for the event message_reaction_add: module 'interactions' has no attribute 'MessageReaction'
# @bot.event
# async def on_message_reaction_add(
#     reaction: interactions.Reaction,
# ):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#     # log(f"{user.username} added {emoji.name} in {channel.name}", 1)
#
#
# @bot.event
# async def on_message_reaction_remove(
#     reaction: interactions.Reaction
# ):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_message_reaction_remove_all(
#     channel: interactions.Channel,
#     message: interactions.Message,
#     guild: interactions.Guild,
# ):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_message_reaction_remove_emoji(
#     channel: interactions.Channel,
#     message: interactions.Message,
#     guild: interactions.Guild,
#     emoji: interactions.Emoji = None,
# ):
#     log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_user_update(user: interactions.User):
    log(0, f"Loaded {inspect.stack()[0][3]}")


log(0, "Initializing the bot...")

bot.start()

log(0, "Bot finished!")

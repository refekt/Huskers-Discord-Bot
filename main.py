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
import inspect

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


@bot.event
async def on_ready():
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_resumed(resume):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_reconnect():
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_channel_create(channel: interactions.Channel):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_channel_update(channel: interactions.Channel):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_channel_delete(channel: interactions.Channel):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_channel_pins_update(channel: interactions.Channel):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_thread_create(
    channel: interactions.Channel, thread_member: interactions.ThreadMember = None
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_thread_update(channel: interactions.Channel):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_thread_delete(channel: interactions.Channel):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_thread_list_sync():
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_thread_member_update(thread_member: interactions.ThreadMember):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_thread_members_update(thread_member: interactions.ThreadMember):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_create(guild: interactions.Guild):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_update(guild: interactions.Guild):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_delete(guild: interactions.Guild):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_ban_add(guild: interactions.Guild, user: interactions.User):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_ban_remove(guild: interactions.Guild, user: interactions.User):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_emojis_update(
    guild: interactions.Guild, emojis: interactions.GuildEmojis
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_stickers_update(
    guild: interactions.Guild, stickers: interactions.GuildStickers
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_integrations_update(guild: interactions.Guild):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_member_add(guild_member: interactions.GuildMember):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_member_remove(guild_member: interactions.GuildMember):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_member_update(guild_member: interactions.GuildMember):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_role_create(guild: interactions.Guild, role: interactions.Role):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_role_update(guild: interactions.Guild, role: interactions.Role):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_role_delete(guild: interactions.Guild, role: interactions.Role):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_scheduled_event_create(
    scheduled_event: interactions.ScheduledEvents,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_scheduled_event_update(
    scheduled_event: interactions.ScheduledEvents,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_scheduled_event_delete(
    scheduled_event: interactions.ScheduledEvents,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_scheduled_event_user_add(
    scheduled_event: interactions.ScheduledEvents,
    user: interactions.User,
    guild: interactions.Guild,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_guild_scheduled_event_user_remove(
    scheduled_event: interactions.ScheduledEvents,
    user: interactions.User,
    guild: interactions.Guild,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_invite_create(
    channel: interactions.Channel,
    code: str,
    created_at,
    guild: interactions.Guild,
    inviter: interactions.User,
    max_age: int,
    max_uses: int,
    target_type: int,
    target_user: interactions.User,
    target_application: interactions.Application,
    temporary: bool,
    uses: int,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_invite_delete(
    channel: interactions.Channel, guild: interactions.Guild, code: str
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_message_create(message: interactions.Message):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_message_update(message: interactions.Message):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_message_delete(message: interactions.Message):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_message_delete_bulk(
    message_ids, channel: interactions.Channel, guild: interactions.Guild
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_message_reaction_add(
    user: interactions.User,
    channel: interactions.Channel,
    message: interactions.Message,
    guild: interactions.Guild,
    member: interactions.Member,
    emoji: interactions.Emoji,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_message_reaction_remove(
    user: interactions.User,
    channel: interactions.Channel,
    message: interactions.Message,
    guild: interactions.Guild,
    member: interactions.Member,
    emoji: interactions.Emoji,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_message_reaction_remove_all(
    channel: interactions.Channel,
    message: interactions.Message,
    guild: interactions.Guild,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_message_reaction_remove_emoji(
    channel: interactions.Channel,
    message: interactions.Message,
    guild: interactions.Guild,
    emoji: interactions.Emoji,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_presence_update(
    presence: interactions.Presence,
):

    if presence.activities is not None:
        activities = presence.activities[0].name
    else:
        activities = None

    if presence.client_status is not None:
        status = (
            f"{presence.client_status.web if not presence.client_status.web is None else None} | "
            f"{presence.client_status.desktop if not presence.client_status.desktop is None else None} | "
            f"{presence.client_status.mobile if not presence.client_status.mobile is None else None}"
        )
    else:
        status = None

    log(
        f"Presence update for {presence.user.id}: {presence.status}, {activities}, {status}",
        0,
    )


@bot.event
async def on_stage_instance_create(stage: interactions.StageInstance):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_stage_instance_delete(stage: interactions.StageInstance):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_stage_instance_update(stage: interactions.StageInstance):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_typing_start(
    channel: interactions.Channel,
    guild: interactions.Guild,
    user: interactions.User,
    timestamp: int,
    member: interactions.Member,
):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_user_update(user: interactions.User):
    log(f"Loaded {inspect.stack()[0][3]}", 0)


log("Starting bot!", 0)

bot.start()

log("Bot finished!", 0)

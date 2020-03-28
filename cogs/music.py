# -*- coding: utf-8 -*-
from discord.ext import commands
import discord
import asyncio
import youtube_dl
import logging
import logging.handlers
import os
import math
from urllib import request
from utils.consts import CHAN_RADIO_PROD, CHAN_RADIO_TEST
from utils.consts import change_my_status as change_status_nonlistening
from utils.consts import ROLE_MOD_PROD, ROLE_ADMIN_PROD, ROLE_ADMIN_TEST

YTDL_OPTS = {
    "default_search": "ytsearch",
    "format": "bestaudio/best",
    "quiet": True,
    "extract_flat": "in_playlist"
}


async def audio_playing(ctx):
    """Checks that audio is currently playing before continuing."""
    client = ctx.guild.voice_client
    if client and client.channel and client.source:
        return True
    else:
        raise commands.CommandError("Not currently playing any audio.")


async def in_voice_channel(ctx):
    """Checks that the command sender is in the same voice channel as the bot."""
    voice = ctx.author.voice
    bot_voice = ctx.guild.voice_client
    if voice and bot_voice and voice.channel and bot_voice.channel and voice.channel == bot_voice.channel:
        return True
    else:
        raise commands.CommandError(
            "You need to be in the channel to do that.")


async def is_audio_requester(ctx):
    """Checks that the command sender is the song requester."""
    music = ctx.bot.get_cog("Music")
    state = music.get_state(ctx.guild)
    permissions = ctx.channel.permissions_for(ctx.author)
    if permissions.administrator or state.is_requester(ctx.author):
        return True
    else:
        raise commands.CommandError(
            "You need to be the song requester to do that.")


class Music(commands.Cog):
    """Bot commands to help play music."""

    def __init__(self, bot):
        self.bot = bot
        self.config = {'max_volume': 250,
                       'vote_skip': True,
                       'vote_skip_ratio': .5
                       }
        self.states = {}

    def get_state(self, guild):
        """Gets the state for `guild`, creating it if it does not exist."""
        if guild.id in self.states:
            return self.states[guild.id]
        else:
            self.states[guild.id] = GuildState()
            return self.states[guild.id]

    async def _nowplaying(self, ctx):  # Commented this out to turn into a function to be called here and automatically after a new song is playing
        state = self.get_state(ctx.guild)
        message = await ctx.send("", embed=state.now_playing.get_embed())
        await self._add_reaction_controls(message)

    @commands.command(aliases=["stop"])
    @commands.guild_only()
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST, ROLE_MOD_PROD)
    async def leave(self, ctx):
        """Leaves the voice channel, if currently in one."""
        client = ctx.guild.voice_client
        state = self.get_state(ctx.guild)
        if client and client.channel:
            await client.disconnect()
            state.playlist = []
            state.now_playing = None
        else:
            raise commands.CommandError("Not in a voice channel.")

    @commands.command(aliases=["resume", "p"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    @commands.check(is_audio_requester)
    async def pause(self, ctx):
        """Pauses any currently playing audio."""
        client = ctx.guild.voice_client
        self._pause_audio(client)

    def _pause_audio(self, client):
        if client.is_paused():
            client.resume()
        else:
            client.pause()

    @commands.command(aliases=["vol", "v"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    @commands.check(is_audio_requester)
    async def volume(self, ctx, volume: int):
        """Change the volume of currently playing audio (values 0-250)."""
        state = self.get_state(ctx.guild)

        # make sure volume is nonnegative
        if volume < 0:
            volume = 0

        max_vol = self.config["max_volume"]
        if max_vol > -1:  # check if max volume is set
            # clamp volume to [0, max_vol]
            if volume > max_vol:
                volume = max_vol

        client = ctx.guild.voice_client

        state.volume = float(volume) / 100.0
        client.source.volume = state.volume  # update the AudioSource's volume to match

    @commands.command()
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    async def skip(self, ctx):
        """Skips the currently playing song, or votes to skip it."""
        state = self.get_state(ctx.guild)
        client = ctx.guild.voice_client
        if ctx.channel.permissions_for(
                ctx.author).administrator or state.is_requester(ctx.author):
            # immediately skip if requester or admin
            client.stop()
        elif self.config["vote_skip"]:
            # vote to skip song
            channel = client.channel
            self._vote_skip(channel, ctx.author)
            # announce vote
            users_in_channel = len([
                member for member in channel.members if not member.bot
            ])  # don't count bots
            required_votes = math.ceil(
                self.config["vote_skip_ratio"] * users_in_channel)
            await ctx.send(
                f"{ctx.author.mention} voted to skip ({len(state.skip_votes)}/{required_votes} votes)"
            )
        else:
            raise commands.CommandError("Sorry, vote skipping is disabled.")

    def _vote_skip(self, channel, member):
        """Register a vote for `member` to skip the song playing."""
        logging.info(f"{member.name} votes to skip")
        state = self.get_state(channel.guild)
        state.skip_votes.add(member)
        users_in_channel = len([
            member for member in channel.members if not member.bot
        ])  # don't count bots
        if (float(len(state.skip_votes)) /
            users_in_channel) >= self.config["vote_skip_ratio"]:
            # enough members have voted to skip, so skip the song
            logging.info(f"Enough votes, skipping...")
            channel.guild.voice_client.stop()

    async def _play_song(self, client, state, song, ctx=None):
        state.now_playing = song

        # changes status to say listening to the title of the songs that's playing. Needed to do it real janky since _play is not a coroutine while change_presence is. Cleaning this is a potential todo
        async def change_status(song):
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=song.title))

        asyncio.run_coroutine_threadsafe(change_status(song), self.bot.loop)

        state.skip_votes = set()  # clear skip votes
        # await self._nowplaying(ctx) # Trying to show a message after a new song plays
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(song.stream_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'), volume=state.volume)

        def after_playing(err):
            if len(state.playlist) > 0:
                next_song = state.playlist.pop(0)
                self._play_song(client, state, next_song)
            else:
                asyncio.run_coroutine_threadsafe(client.disconnect(),
                                                 self.bot.loop)
                # uses the utils.consts.change_my_status (aliased) to change the status back to something else so it isn't stuck on the listening status for last song in the queue
                asyncio.run_coroutine_threadsafe(change_status_nonlistening(self.bot),
                                                 self.bot.loop)

        client.play(source, after=after_playing)
        # Commented this out to turn into a function to be called here and automatically after a new song is playing

    @commands.command(aliases=["np"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def nowplaying(self, ctx):
        """Displays information about the current song."""
        # Commented this out to turn into a function to be called here and automatically after a new song is playing
        # state = self.get_state(ctx.guild)
        # message = await ctx.send("", embed=state.now_playing.get_embed())
        # await self._add_reaction_controls(message)
        await self._nowplaying(ctx)

    @commands.command(aliases=["playlist"])
    @commands.guild_only()
    # @commands.check(audio_playing)
    async def queue(self, ctx):
        """Display the current play queue."""
        state = self.get_state(ctx.guild)
        await ctx.send(self._queue_text(state.playlist))

    def _queue_text(self, queue):
        """Returns a block of text describing a given song queue."""
        if len(queue) > 0:
            message = [f"{len(queue)} songs in queue:"]
            message += [
                f"  {index + 1}. **{song.title}** (requested by **{song.requested_by.name}**)"
                for (index, song) in enumerate(queue)
            ]  # add individual songs
            return "\n".join(message)
        else:
            return "The play queue is empty."

    @commands.command(aliases=["cq"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST, ROLE_MOD_PROD)
    async def clearqueue(self, ctx):
        """Clears the play queue without leaving the channel."""
        state = self.get_state(ctx.guild)
        state.playlist = []

    @commands.command(aliases=["jq"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST, ROLE_MOD_PROD)
    async def jumpqueue(self, ctx, song: int, new_index: int):
        """Moves song at an index to `new_index` in queue."""
        state = self.get_state(ctx.guild)  # get state for this guild
        if 1 <= song <= len(state.playlist) and 1 <= new_index:
            song = state.playlist.pop(song - 1)  # take song at index...
            state.playlist.insert(new_index - 1, song)  # and insert it.

            await ctx.send(self._queue_text(state.playlist))
        else:
            raise commands.CommandError("You must use a valid index.")

    @commands.command(brief="Plays audio from <url>.")
    @commands.guild_only()
    async def play(self, ctx, *, url):
        """Plays audio hosted at <url> (or performs a search for <url> and plays the first result)."""

        client = ctx.guild.voice_client
        state = self.get_state(ctx.guild)  # get the guild's state

        if client and client.channel:
            try:
                video = Video(url, ctx.author)
            except youtube_dl.DownloadError as e:
                logging.warn(f"Error downloading video: {e}")
                await ctx.send(
                    "There was an error downloading your video, sorry.")
                return
            state.playlist.append(video)
            message = await ctx.send(
                "Added to queue.", embed=video.get_embed())
            await self._add_reaction_controls(message)
        else:
            channel = ctx.guild.get_channel(channel_id=CHAN_RADIO_PROD)
            if not channel:
                channel = ctx.guild.get_channel(channel_id=CHAN_RADIO_TEST)
            try:
                video = Video(url, ctx.author)
            except youtube_dl.DownloadError as e:
                await ctx.send(
                    "There was an error downloading your video, sorry.")
                return
            client = await channel.connect()
            await self._play_song(client, state, video, ctx)
            message = await ctx.send("", embed=video.get_embed())
            await self._add_reaction_controls(message)
            logging.info(f"Now playing '{video.title}'")
            # else:
            # raise commands.CommandError(
            # "You need to be in a voice channel to do that.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        print(repr(reaction))
        print(repr(user))
        """Respods to reactions added to the bot's messages, allowing reactions to control playback."""
        message = reaction.message
        if user != self.bot.user and message.author == self.bot.user:
            await message.remove_reaction(reaction, user)
            if message.guild and message.guild.voice_client:
                user_in_channel = user.voice and user.voice.channel and user.voice.channel == message.guild.voice_client.channel
                permissions = message.channel.permissions_for(user)
                guild = message.guild
                state = self.get_state(guild)
                if permissions.administrator or (user_in_channel and state.is_requester(user)):
                    client = message.guild.voice_client
                    if reaction.emoji == "⏯":
                        # pause audio
                        self._pause_audio(client)
                    elif reaction.emoji == "⏭":
                        # skip audio
                        client.stop()
                    elif reaction.emoji == "⏮":
                        state.playlist.insert(
                            0, state.now_playing
                        )  # insert current song at beginning of playlist
                        client.stop()  # skip ahead
                elif reaction.emoji == "⏭" and self.config["vote_skip"] and user_in_channel and message.guild.voice_client and message.guild.voice_client.channel:
                    # ensure that skip was pressed, that vote skipping is enabled, the user is in the channel, and that the bot is in a voice channel
                    voice_channel = message.guild.voice_client.channel
                    self._vote_skip(voice_channel, user)
                    # announce vote
                    channel = message.channel
                    users_in_channel = len([
                        member for member in voice_channel.members
                        if not member.bot
                    ])  # don't count bots
                    required_votes = math.ceil(
                        self.config["vote_skip_ratio"] * users_in_channel)
                    await channel.send(
                        f"{user.mention} voted to skip ({len(state.skip_votes)}/{required_votes} votes)"
                    )

    async def _add_reaction_controls(self, message):
        """Adds a 'control-panel' of reactions to a message that can be used to control the bot."""
        CONTROLS = ["⏮", "⏯", "⏭"]
        for control in CONTROLS:
            await message.add_reaction(control)


class GuildState:
    """Helper class managing per-guild state."""

    def __init__(self):
        self.volume = 1.0
        self.playlist = []
        self.skip_votes = set()
        self.now_playing = None

    def is_requester(self, user):
        return self.now_playing.requested_by == user


class Video:
    """Class containing information about a particular video."""

    def __init__(self, url_or_search, requested_by):
        """Plays audio from (or searches for) a URL."""
        with youtube_dl.YoutubeDL(YTDL_OPTS) as ydl:
            video = self._get_info(url_or_search)

            # code originally just picked the first audio source, I added logic (commented out) to pick the audio format with largest filesize but I'm unsure if that's technically the "best" quality
            video_format = video["formats"][0]
            # for f in video["formats"]:
            # if 'audio only' in f['format']:
            # if f['filesize'] > video_format['filesize']:
            # video_format = f

            self.stream_url = video_format["url"]
            self.video_url = video["webpage_url"]
            self.title = video["title"]
            self.uploader = video["uploader"] if "uploader" in video else ""
            self.thumbnail = video[
                "thumbnail"] if "thumbnail" in video else None
            self.requested_by = requested_by

    def _get_info(self, video_url):
        with youtube_dl.YoutubeDL(YTDL_OPTS) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video = None
            if "_type" in info and info["_type"] == "playlist":
                return self._get_info(
                    info["entries"][0]["url"])  # get info for first video
            else:
                video = info
            return video

    def get_embed(self):
        """Makes an embed out of this Video's information."""
        embed = discord.Embed(
            title=self.title, description=self.uploader, url=self.video_url)
        embed.set_footer(
            text=f"Requested by {self.requested_by.name}",
            icon_url=self.requested_by.avatar_url)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed


def setup(bot):
    bot.add_cog(Music(bot))

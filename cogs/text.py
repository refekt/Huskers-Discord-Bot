import random
import re
import typing
from datetime import datetime, timedelta

import discord
import markovify
import requests
from discord.ext import commands

from utils.consts import ScheduleBackup
from utils.consts import Venue
from utils.consts import _global_per as _global_per
from utils.consts import _global_rate as _global_rate
from utils.consts import tz


class TextCommands(commands.Cog):
    @commands.command(aliases=["cd",])
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def countdown(self, ctx, *, team=None):
        """ Countdown to the most current or specific Husker game """
        now_cst = datetime.now().astimezone(tz=tz)

        def convert_seconds(n):
            secs = n % (24 * 3600)
            hour = secs // 3600
            secs %= 3600
            mins = secs // 60

            return hour, mins

        async def cd_next_season():
            for game in ScheduleBackup(year=datetime.now().year+1):
                if not "spring" in game.opponent.lower():
                    diff = game.game_date_time - now_cst
                    diff_cd = convert_seconds(diff.seconds)
                    await send_countdown(diff.days, diff_cd[0], diff_cd[1], game.opponent, game.game_date_time)
                    return

        async def send_countdown(days: int, hours: int, minutes: int, opponent: str, datetime: datetime):
            await ctx.send(f"📢 📅:There are __[ {days} days, {hours} hours, {minutes} minutes ]__ until the __[ {opponent} ]__ game at __[ {datetime.strftime('%B %d, %Y %I:%M %p')} ]__")

        if team is None:
            for game in ScheduleBackup(year=datetime.now().year):
                if game.game_date_time > now_cst:
                    diff = game.game_date_time - now_cst
                    diff_cd = convert_seconds(diff.seconds)
                    await send_countdown(diff.days, diff_cd[0], diff_cd[1], game.opponent, game.game_date_time)
                    break
        else:
            team = str(team)

            for game in ScheduleBackup(year=datetime.now().year):
                if team.lower() == game.opponent.lower():
                    diff = game.game_date_time - now_cst
                    diff_cd = convert_seconds(diff.seconds)
                    await send_countdown(diff.days, diff_cd[0], diff_cd[1], game.opponent, game.game_date_time)
                    break

        await cd_next_season()

    @commands.command(aliases=["mkv"])
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def markov(self, ctx, *what: typing.Union[discord.Member, discord.TextChannel]):
        """ Creates a Markov chain based off a user and/or text-channel """
        edit_msg = await ctx.send("Thinking...")
        source_data = ""

        if not what:
            async for msg in ctx.message.channel.history(limit=5000):
                if msg.content != "" and not msg.author.bot:
                    source_data += "\r\n" + msg.content
        else:
            bannedchannels = ["test-banned", "news-politics"]

            if len(what) > 5:
                await edit_msg.edit(content="...this might take awhile...be patient...")

            f = open("resources/scofro.txt", "r")
            scottFrost = ""

            for source in what:
                if type(source) == discord.Member:
                    if source.bot:
                        if f.mode == "r":
                            scottFrost += f.read()
                        source_data = re.sub(r'[^\x00-\x7f]', r'', scottFrost)
                    else:
                        async for msg in ctx.channel.history(limit=5000):
                            if msg.content != "" and str(msg.author) == str(source) and not msg.author.bot:
                                source_data += "\r\n" + str(msg.content).capitalize()
                elif type(source) == discord.TextChannel:
                    if source.name not in bannedchannels:
                        async for msg in source.history(limit=5000):
                            if msg.content != "" and not msg.author.bot:
                                source_data += "\r\n" + msg.content

            f.close()

        if not source_data:
            await edit_msg.edit(content="You broke me!")
            return

        chain = markovify.NewlineText(source_data, well_formed=True)
        sentence = chain.make_short_sentence(min_chars=45, max_chars=500)

        if sentence is None:
            await edit_msg.edit(content="You broke me!")
        else:
            await edit_msg.edit(content=sentence)

    @commands.group()
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def weather(self, ctx):
        """ Current weather for the next game day location """

        if ctx.subcommand_passed:
            return

        venues = Venue()
        embed = None
        edit_msg = None
        _venue_name = None
        _weather = None
        _x = None
        _y = None
        _opponent = None

        for game in ScheduleBackup(year=datetime.now().year):
            now_cst = datetime.now().astimezone(tz=tz)

            if now_cst < game.game_date_time.astimezone(tz=tz):
                if game.location == "Memorial Stadium":
                    _venue_name = venues[207]["name"]
                    _x = venues[207]["location"]["x"]
                    _y = venues[207]["location"]["y"]
                else:
                    for venue in venues:
                        if venue["city"].lower() == game.location[0].lower() and venue["state"].lower() == game.location[1].lower():
                            _venue_name = venue['name']
                            _x = venue['location']['x']
                            _y = venue['location']['y']

                            edit_msg = await ctx.send("Loading...")

                            break

                r = requests.get(url=f"https://api.weatherbit.io/v2.0/current?key={'39b7915267f04d5f88fa5fe6be6290e6'}&lang=en&units=I&lat={_x}&lon={_y}")
                _weather = r.json()

                embed = discord.Embed(
                    title=f"Weather Forecast for __[ {_venue_name} ]__ in __[ {_weather['data'][0]['city_name']}, {_weather['data'][0]['state_code']} ]__",
                    color=0xFF0000,
                    description=f"Nebraska's next opponent is __[ {game.opponent} ]__")

        if embed is None:
            await ctx.send("The season is over! No upcoming games found.")
            return

        embed.set_thumbnail(url=f"https://www.weatherbit.io/static/img/icons/{_weather['data'][0]['weather']['icon']}.png")
        embed.set_footer(text="There is a daily 500 call limit to the API used for this command. Do not abuse it.")
        embed.add_field(name="Temperature", value=f"{_weather['data'][0]['temp']} F", inline=False)
        embed.add_field(name="Cloud Coverage", value=f"{_weather['data'][0]['clouds']}%", inline=False)
        embed.add_field(name="Wind Speed", value=f"{_weather['data'][0]['wind_spd']} MPH / {_weather['data'][0]['wind_cdir']}", inline=False)
        embed.add_field(name="Snow Chance", value=f"{_weather['data'][0]['snow']:.2f}%", inline=False)
        embed.add_field(name="Precipitation Chance", value=f"{_weather['data'][0]['precip'] * 100:.2f}%", inline=False)

        if edit_msg is not None:
            await edit_msg.edit(content="", embed=embed)
        else:
            await ctx.send(embed=embed)

    # @weather.command()
    # async def forecast(self, ctx):
    #     edit_msg = await ctx.send("Loading...")
    #
    #     venues = Venue()
    #     _venue_name = None
    #     _weather = None
    #     _x = None
    #     _y = None
    #     _opponent = None
    #     game_dt_cst = None
    #
    #     for game in Schedule(year=datetime.now().year):
    #         game_dt_cst = dateutil.parser.parse(game.start_date)
    #         game_dt_cst = game_dt_cst.astimezone(tz=pytz.timezone("US/Central"))
    #         now_cst = datetime.now().astimezone(tz=pytz.timezone("US/Central"))
    #
    #         if now_cst < game_dt_cst:
    #             for venue in venues:
    #                 if game.venue_id == venue['id']:
    #                     _venue_name = venue['name']
    #                     _opponent = game.away_team if game.home_team == "Nebraska" else game.home_team
    #                     _x = venue['location']['x']
    #                     _y = venue['location']['y']
    #
    #                     break
    #
    #     if _venue_name is None:
    #         await edit_msg.edit(content="The season is over! No upcoming games found.")
    #         return
    #
    #     r = requests.get(url=f"https://api.weatherbit.io/v2.0/forecast/daily?key={'39b7915267f04d5f88fa5fe6be6290e6'}&lang=en&units=I&lat={_x}&lon={_y}&days=7")
    #     _weather = r.json()
    #
    #     for days in _weather["data"]:
    #         datetime_obj = datetime.strptime(days["datetime"], "%Y-%m-%d")
    #         if datetime_obj.weekday() == 5:
    #             embed = discord.Embed(
    #                 title=f"Game day forecast for __[ {_venue_name} ]__  in __[ {_weather['city_name']}, {_weather['state_code']} ]__",
    #                 color=0xFF0000,
    #                 description=f"Nebraska plays  __[ {_opponent} ]__ next on __[ {game_dt_cst.strftime('%c')} ]__ and the weather calls for __[ {days['weather']['description']} ]__")
    #
    #             embed.set_thumbnail(url="https://www.weatherbit.io/static/img/icons/{}.png".format(days["weather"]["icon"]))
    #             embed.add_field(name="Temperature", value=f"{_weather['data'][0]['temp']} F", inline=False)
    #             embed.add_field(name="Cloud Coverage", value=f"{_weather['data'][0]['clouds']}%", inline=False)
    #             embed.add_field(name="Wind Speed", value=f"{_weather['data'][0]['wind_spd']} MPH / {_weather['data'][0]['wind_cdir']}", inline=False)
    #             embed.add_field(name="Snow Chance", value=f"{_weather['data'][0]['snow']:.2f}%", inline=False)
    #             embed.add_field(name="Precipitation Chance", value=f"{_weather['data'][0]['precip'] * 100:.2f}%", inline=False)
    #
    #             await edit_msg.edit(content="", embed=embed)
    #
    #             break

    @commands.command(name="24hours", aliases=["24", "24hrs",])
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def _24hours(self, ctx):
        """ You have 24 hours to cheer or moam about the game """
        games = ScheduleBackup(year=datetime.now().year)

        for index, game in enumerate(reversed(games)):
            game_dt_cst = game.game_date_time.astimezone(tz=tz)
            now_cst = datetime.now().astimezone(tz=tz)
            _24hourspassed = game_dt_cst + timedelta(days=1)
            _24hourspassed = _24hourspassed.astimezone(tz=tz)

            if now_cst > game_dt_cst:
                try:
                    i = len(games) - (index + 1) if index < len(games) else len(games) - index
                    next_opponent = games[i + 1].opponent # Should avoid out of bounds

                    if now_cst < _24hourspassed:
                        await ctx.send(f"You have 24 hours to #moaming the __[ {game.opponent} ]__ game! That ends in __[ {_24hourspassed - now_cst} ]__!")
                    else:
                        await ctx.send(f"The 24 hours are up! No more #moaming. Time to focus on the __[ {next_opponent} ]__ game!")
                    break
                except IndexError:
                    await ctx.send("The season is over! No upcoming games found.")
                    return

    @commands.command()
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def orderjoined(self, ctx, who: discord.Member):
        """ When did you join the server? """
        from utils.client import client

        def sort_second(val):
            return val[1]

        users = client.get_all_members()
        users_sorted = []

        for user in users:
            users_sorted.append([user.name, user.joined_at])

        users_sorted.sort(key=sort_second)

        count = 10

        if not who:
            earliest = "```\n"
            for index, user in enumerate(users_sorted):
                if index < count:
                    earliest += f"#{index + 1:2} - {user[1]}: {user[0]}\n"
            earliest += "```"
            await ctx.send(earliest)
        else:
            for user in users_sorted:
                if user[0] == who.display_name:
                    await ctx.send(f"`{who.display_name} joined at {user[1]}`")
                    return

    @commands.command(aliases=["8b",])
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def eightball(self, ctx):
        """ Ask a Magic 8-Ball a question. """
        eight_ball = ['As I see it, yes', 'Ask again later', 'Better not tell you now', 'Cannot predict now', 'Coach V\'s cigar would like this', 'Concentrate and ask again', 'Definitely yes',
                      'Don’t count on it', 'Frosty', 'Fuck Iowa', 'It is certain', 'It is decidedly so', 'Most Likely', 'My reply is no', 'My sources say no', 'Outlook not so good, and very doubtful',
                      'Reply hazy', 'Scott Frost approves', 'These are the affirmative answers.', 'Try again', 'Try again', 'Without a doubt', 'Yes – definitely', 'You may rely on it']

        random.shuffle(eight_ball)
        dice_roll = random.randint(0, len(eight_ball) - 1)

        embed = discord.Embed(title="The HuskerBot 8-Ball :8ball: says...", description=eight_ball[dice_roll], color=0xFF0000)
        embed.set_thumbnail(url="https://i.imgur.com/L5Gpu0z.png")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TextCommands(bot))


print("### Text Commands loaded! ###")

from utils.embed import build_embed
import urbandict
import random
import re
import typing
from datetime import datetime, timedelta

import discord
import markovify
import requests
from discord.ext import commands

from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE, CHAN_BANNED
from utils.consts import TZ
from utils.games import ScheduleBackup
from utils.games import Venue


class TextCommands(commands.Cog):
    @commands.command(aliases=["cd", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def countdown(self, ctx, *, team=None):
        """ Countdown to the most current or specific Husker game """
        edit_msg = await ctx.send("Loading...")
        now_cst = datetime.now().astimezone(tz=TZ)

        def convert_seconds(n):
            secs = n % (24 * 3600)
            hour = secs // 3600
            secs %= 3600
            mins = secs // 60

            return hour, mins

        async def send_countdown(days: int, hours: int, minutes: int, opponent: str, datetime: datetime):
            await edit_msg.edit(content=f"📢 📅:There are __[ {days} days, {hours} hours, {minutes} minutes ]__ until the __[ {opponent} ]__ game at __[ {datetime.strftime('%B %d, %Y %I:%M %p')} ]__")

        games, stats = ScheduleBackup(year=now_cst.year)

        if team is None:
            for game in games:
                if game.game_date_time > now_cst:
                    diff = game.game_date_time - now_cst
                    diff_cd = convert_seconds(diff.seconds)
                    await send_countdown(diff.days, diff_cd[0], diff_cd[1], game.opponent, game.game_date_time)
                    break
        else:
            team = str(team)

            for game in games:
                if team.lower() == game.opponent.lower():
                    diff = game.game_date_time - now_cst
                    diff_cd = convert_seconds(diff.seconds)
                    await send_countdown(diff.days, diff_cd[0], diff_cd[1], game.opponent, game.game_date_time)
                    break

    @commands.command(aliases=["mkv"])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def markov(self, ctx, *sources: typing.Union[discord.Member, discord.TextChannel]):
        """ Attempts to create a meaningful sentence from provided sources. If no source is provided, attempt to create a meaningful sentence from current channel. If a bot is provided as a source, a quote from Scott Frost will be used. If a Discord Member (@mention) is provided, member's history in the current channel will be used. """

        edit_msg = await ctx.send("Thinking...")
        source_data = ""
        messages = []

        CHAN_HIST_LIMIT = 2250

        def check_message(auth: discord.Member, msg: discord.Message = None, bot_provided: bool = False):
            if bot_provided:
                f = open("resources/scofro.txt", "r")
                return re.sub(r'[^\x00-\x7f]', r'', f.read())
            else:
                from utils.client import client

                if not auth.bot and msg.channel.id not in CHAN_BANNED and not [ele for ele in client.all_commands.keys() if (ele in msg.content)]:
                    return "\n" + str(msg.content.capitalize())

            return ""

        def cleanup_source_data(source_data: str):
            new_source_data = source_data.replace("`", "")
            new_source_data = new_source_data.replace("\n\n", "\n")
            regex_url_finder = "((http|ftp|https)://|)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
            new_source_data = re.sub(regex_url_finder, "", new_source_data, flags=re.IGNORECASE)
            return new_source_data

        if not sources:
            messages = await ctx.message.channel.history(limit=CHAN_HIST_LIMIT).flatten()
            for msg in messages:
                source_data += check_message(auth=ctx.message.author, msg=msg, bot_provided=msg.author.bot)
        else:
            if len(sources) > 3:
                await edit_msg.edit(content=edit_msg.content + "...this might take awhile...be patient...")

            for item in sources:
                if type(item) == discord.Member:
                    if item.bot:
                        source_data += check_message(auth=ctx.message.author, bot_provided=item.bot)
                    else:
                        try:
                            messages = await ctx.message.channel.history(limit=CHAN_HIST_LIMIT).flatten()
                            for msg in messages:
                                if msg.author == item:
                                    source_data += check_message(auth=msg.author, msg=msg, bot_provided=msg.author.bot)
                        except discord.errors.Forbidden:
                            continue
                elif type(item) == discord.TextChannel:
                    messages = await item.history(limit=CHAN_HIST_LIMIT).flatten()
                    for msg in messages:
                        source_data += check_message(auth=msg.author, msg=msg, bot_provided=msg.author.bot)

        source_data = cleanup_source_data(source_data)

        broken_message = f"```\nYou broke me! Most likely because there is no source data.\nThe source data is: {repr(source_data)}```"

        if not source_data:
            await edit_msg.edit(content="Source data: " + broken_message)
            return

        chain = markovify.NewlineText(source_data, well_formed=True)
        sentence = chain.make_sentence(max_overlap_ratio=.9, max_overlap_total=27, min_words=7, tries=100)

        if sentence is None:
            await edit_msg.edit(content="Sentence: " + broken_message)
        else:
            await edit_msg.edit(content=sentence)

    @commands.group()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def weather(self, ctx):
        """ Current weather for the next game day location """

        if ctx.invoked_subcommand:
            return

        venues = Venue()
        embed = None
        edit_msg = None
        _venue_name = None
        _weather = None
        _x = None
        _y = None
        _opponent = None

        edit_msg = await ctx.send("Loading...")

        season, season_stats = ScheduleBackup(year=datetime.now().year)
        # season = reversed(season)

        for game in season:
            now_cst = datetime.now().astimezone(tz=TZ)

            if now_cst < game.game_date_time.astimezone(tz=TZ):
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
                            break

                r = requests.get(url=f"https://api.weatherbit.io/v2.0/current?key={'39b7915267f04d5f88fa5fe6be6290e6'}&lang=en&units=I&lat={_x}&lon={_y}")
                _weather = r.json()

                embed = discord.Embed(
                    title=f"Weather Forecast for the __[ {game.opponent} ]__ in __[ {_venue_name} / {_weather['data'][0]['city_name']}, {_weather['data'][0]['state_code']} ]__",
                    color=0xFF0000)  # ,
                # description=f"Nebraska's next opponent is __[ {game.opponent} ]__")

                break

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

    @commands.command(name="24hours", aliases=["24", "24hrs", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def _24hours(self, ctx):
        """ You have 24 hours to cheer or moam about the game """
        games = ScheduleBackup(year=datetime.now().year)

        for index, game in enumerate(reversed(games)):
            game_dt_cst = game.game_date_time.astimezone(tz=TZ)
            now_cst = datetime.now().astimezone(tz=TZ)
            _24hourspassed = game_dt_cst + timedelta(days=1)
            _24hourspassed = _24hourspassed.astimezone(tz=TZ)

            if now_cst > game_dt_cst:
                try:
                    i = len(games) - (index + 1) if index < len(games) else len(games) - index
                    next_opponent = games[i + 1].opponent  # Should avoid out of bounds

                    if now_cst < _24hourspassed:
                        await ctx.send(f"You have 24 hours to #moaming the __[ {game.opponent} ]__ game! That ends in __[ {_24hourspassed - now_cst} ]__!")
                    else:
                        await ctx.send(f"The 24 hours are up! No more #moaming. Time to focus on the __[ {next_opponent} ]__ game!")
                    break
                except IndexError:
                    await ctx.send("The season is over! No upcoming games found.")
                    return

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def whenjoined(self, ctx, who: discord.Member):
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

    @commands.command(aliases=["8b", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def eightball(self, ctx):
        """ Ask a Magic 8-Ball a question. """
        eight_ball = ['As I see it, yes', 'Ask again later', 'Better not tell you now', 'Cannot predict now', 'Coach V\'s cigar would like this', 'Concentrate and ask again', 'Definitely yes',
                      'Don’t count on it', 'Frosty', 'Fuck Iowa', 'It is certain', 'It is decidedly so', 'Most Likely', 'My reply is no', 'My sources say no', 'Outlook not so good, and very doubtful',
                      'Reply hazy', 'Scott Frost approves', 'These are the affirmative answers.', 'Try again', 'Try again', 'Without a doubt', 'Yes – definitely', 'You may rely on it']

        random.shuffle(eight_ball)

        embed = discord.Embed(title="The HuskerBot 8-Ball :8ball: says...", description=random.choice(eight_ball), color=0xFF0000)
        embed.set_thumbnail(url="https://i.imgur.com/L5Gpu0z.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def police(self, ctx, baddie: discord.Member):
        await ctx.send(f"**"
                       f"🚨 NANI 🚨\n"
                       f"\t🚨 THE 🚨\n"
                       f"\t\t🚨 FUCK 🚨\n"
                       f"\t\t\t🚨 DID 🚨\n"
                       f"\t\t\t\t🚨 YOU 🚨\n"
                       f"\t\t\t🚨 JUST 🚨\n"
                       f"\t\t🚨 SAY 🚨\n"
                       f"\t🚨 {baddie.mention} 🚨\n"
                       f"🏃‍♀️💨 🔫🚓🔫🚓🔫🚓"
                       f"\n"
                       f"👮‍📢 Information ℹ provided in the VIP 👑 Room 🏆 is intended for Husker247 🌽🎈 members only ‼🔫. "
                       f"Please do not copy ✏ and paste 🖨 or summarize this content elsewhere‼ Please try to keep all replies in this thread 🧵 for Husker247 members only! "
                       f"🚫 ⛔ 👎 🙅‍♀️Thanks for your cooperation. 😍🤩😘 **")

    @commands.command(aliases=["ud", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def urbandictionary(self, ctx, *, word: str):
        edit_msg = await ctx.send("Loading...")
        # definition = urbandict.define(word)
        #
        # await edit_msg.edit(
        #     text="",
        #     embed=build_embed(
        #         title="Urban Dictionary Definition",
        #         fields=[
        #             [definition[0]["word"], definition[0]["def"]]
        #         ]
        #     )
        # )

        from bs4 import BeautifulSoup
        r = requests.get(f"http://www.urbandictionary.com/define.php?term={word}")
        soup = BeautifulSoup(r.content)
        definition = soup.find("div", attrs={"class": "meaning"}).text

        await edit_msg.edit(
            text="",
            embed=build_embed(
                title=f"Urban Dictionary Definition",
                fields=[
                    [word, definition]
                ]
            )
        )

def setup(bot):
    bot.add_cog(TextCommands(bot))

# print("### Text Commands loaded! ###")

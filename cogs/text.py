import asyncio
import random
import re
import typing
from datetime import datetime, timedelta

import discord
import markovify
import requests
from discord.ext import commands

from bs4 import BeautifulSoup

from utils.client import client
from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE, CHAN_BANNED
from utils.consts import TZ
from utils.embed import build_embed
from utils.games import HuskerSchedule
from utils.mysql import process_MySQL
from utils.mysql import sqlRecordTasks
from utils.thread import send_reminder
from utils.consts import HEADERS


class TeamStatsWinsipediaTeam():

    def __init__(self, *, team_name: str):

        def all_time_record():
            atr = soup.find_all(attrs={"class": "ranking span2 item2"})
            return (
                atr[0].contents[1].contents[3].contents[1].text,
                atr[0].contents[3].contents[1].text.strip()
            )

        def championships():
            champs = soup.find_all(attrs={"class": "ranking span2 item3"})
            return (
                champs[0].contents[3].contents[1].text,
                champs[0].contents[5].contents[1].text
            )

        def conf_championships():
            conf = soup.find_all(attrs={"class": "ranking span2 item4h"})
            return (
                conf[0].contents[3].contents[1].text,
                conf[0].contents[5].contents[1].text
            )

        def bowl_games():
            bowl = soup.find_all(attrs={"class": "ranking span2 item5h"})
            return (
                bowl[0].contents[1].contents[1].text,
                bowl[0].contents[3].contents[1].text
            )

        def all_time_wins():
            atw = soup.find_all(attrs={"class": "ranking span2 item1"})
            return (
                atw[0].contents[1].contents[1].text,
                atw[0].contents[3].contents[1].text
            )

        def bowl_record():
            bowl = soup.find_all(attrs={"class": "ranking span2 item2"})
            return (
                bowl[1].contents[1].contents[3].contents[1].text,  #\n and \t
                bowl[1].contents[3].contents[1].text.strip()
            )

        def consensus_all_americans():
            caa = soup.find_all(attrs={"class": "ranking span2 item3"})
            return (
                caa[1].contents[1].contents[1].text,
                caa[1].contents[3].contents[1].text
            )

        def heisman_winners():
            hw = soup.find_all(attrs={"class": "ranking span2 item4"})
            return (
                hw[1].contents[3].contents[1].text,
                hw[1].contents[5].contents[1].text
            )

        def nfl_draft_picks():
            nfl_picks = soup.find_all(attrs={"class": "ranking span2 item5"})
            return (
                nfl_picks[1].contents[3].contents[1].text,
                nfl_picks[1].contents[5].contents[1].text
            )
        
        def weeks_ap_poll():
            ap_poll = soup.find_all(attrs={"class": "ranking span2 item6"})
            return (
                ap_poll[0].contents[3].contents[1].text,
                ap_poll[0].contents[5].contents[1].text
            )

        self.team_name = team_name.replace(" ", "-")
        self.url = f"http://www.winsipedia.com/{self.team_name}"

        re = requests.get(url=self.url, headers=HEADERS)
        soup = BeautifulSoup(re.content, features="html.parser")

        self.all_time_record = all_time_record()[0]
        self.all_time_record_rank = all_time_record()[1]
        self.championships = championships()[0]
        self.championships_rank = championships()[1]
        self.conf_championships = conf_championships()[0]
        self.conf_championships_rank = conf_championships()[1]
        self.bowl_games = bowl_games()[0]
        self.bowl_games_rank = bowl_games()[1]
        self.all_time_wins = all_time_wins()[0]
        self.all_time_wins_rank = all_time_wins()[1]
        self.bowl_record = bowl_record()[0]
        self.bowl_record_rank = bowl_record()[1]
        self.consensus_all_americans = consensus_all_americans()[0]
        self.consensus_all_americans_rank = consensus_all_americans()[1]
        self.heisman_winners = heisman_winners()[0]
        self.heisman_winners_rank = heisman_winners()[1]
        self.nfl_draft_picks = nfl_draft_picks()[0]
        self.nfl_draft_picks_rank = nfl_draft_picks()[1]
        self.week_in_ap_poll = weeks_ap_poll()[0]
        self.week_in_ap_poll_rank = weeks_ap_poll()[1]


class CompareWinsipediaTeam():
    name = None

    def __init__(self, name, largest_mov, largest_mov_date, longest_win_streak, largest_win_streak_date):
        self.name = name
        self.largest_mov = largest_mov
        self.largest_mov_date = largest_mov_date
        self.longest_win_streak = longest_win_streak
        self.largest_win_streak_date = largest_win_streak_date


class CompareWinsipedia:

    def __init__(self, compare: str, against: str):
        self.url = f"http://www.winsipedia.com/{compare.lower()}/vs/{against.lower()}"
        self.full_games_url = f"http://www.winsipedia.com/games/{compare.lower()}/vs/{against.lower()}"

        def mov(which: int):
            raw_mov = soup.find_all(attrs={"class": f"ranking span2 item{which}"})
            raw_mov = raw_mov[0].contents[3].text.replace("\n \n", ":").strip()
            return raw_mov.split(":")

        def win(which: int):
            raw_win = soup.find_all(attrs={"class": f"ranking span2 item{which}"})
            raw_win = raw_win[0].contents[3].text.replace("\n \n", ":").strip()
            return raw_win.split(":")

        def all_time_wins():
            wins = soup.find_all(attrs={"class": "titleItem left"})[0].contents[1].text
            ties = soup.find_all(attrs={"class": "titleItem center"})[0].contents[1].text
            losses = soup.find_all(attrs={"class": "titleItem right"})[0].contents[1].text

            return f"{wins} wins - {ties} ties - {losses} losses"

        re = requests.get(url=self.url, headers=HEADERS)
        soup = BeautifulSoup(re.content, features="html.parser")

        margin_of_victory = mov(1)
        win_stream = win(2)
        self.all_time_record = all_time_wins()
        self.compare = CompareWinsipediaTeam(name=compare, largest_mov=margin_of_victory[0], largest_mov_date=margin_of_victory[1], longest_win_streak=win_stream[0],
                                             largest_win_streak_date=win_stream[1])

        margin_of_victory = mov(6)
        win_stream = win(5)
        self.against = CompareWinsipediaTeam(name=compare, largest_mov=margin_of_victory[0], largest_mov_date=margin_of_victory[1], longest_win_streak=win_stream[0],
                                             largest_win_streak_date=win_stream[1])


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

        async def send_countdown(days: int, hours: int, minutes: int, opponent, datetime: datetime):
            if datetime.hour == 21 and datetime.minute == 58:
                await edit_msg.edit(content=f"📢 📅:There are __[ {days} days, {hours} hours, {minutes} minutes ]__ until the __[ {opponent.name} ]__ game at __["
                                            f" {datetime.strftime('%B %d, %Y')} ]__")
            else:
                await edit_msg.edit(content=f"📢 📅:There are __[ {days} days, {hours} hours, {minutes} minutes ]__ until the __[ {opponent.name} ]__ game at __["
                                            f" {datetime.strftime('%B %d, %Y %I:%M %p %Z')} ]__")

        games, stats = HuskerSchedule(year=now_cst.year)

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

                if not auth.bot and msg.channel.id not in CHAN_BANNED and not [ele for ele in client.all_commands.keys() if (ele in msg.content)]:
                    msg_content = str(msg.content.capitalize())
                    return "\n" + msg_content

            return ""

        def cleanup_source_data(source_data: str):
            regex_strings = [
                r"(<@\d{18}>|<@!\d{18}>|<:\w{1,}:\d{18}>|<#\d{18}>)",  # All Discord mentions
                r"((Http|Https|http|ftp|https)://|)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"  # All URLs
            ]

            new_source_data = source_data

            for regex in regex_strings:
                new_source_data = re.sub(regex, "", new_source_data, flags=re.IGNORECASE)

            regex_new_line = r"(\r\n|\r|\n){1,}"  # All new lines
            new_source_data = re.sub(regex_new_line, "\n", new_source_data, flags=re.IGNORECASE)

            regex_front_new_line = r"^\n"
            new_source_data = re.sub(regex_front_new_line, "", new_source_data, flags=re.IGNORECASE)

            regex_multiple_whitespace = r"\s{2,}"
            new_source_data = re.sub(regex_multiple_whitespace, " ", new_source_data, flags=re.IGNORECASE)

            return new_source_data

        if not sources:
            messages = await ctx.message.channel.history(limit=CHAN_HIST_LIMIT).flatten()
            for msg in messages:
                if not msg.author.bot:
                    source_data += check_message(auth=ctx.message.author, msg=msg, bot_provided=False)
        else:
            if len(sources) > 3:
                await edit_msg.edit(content=edit_msg.content + "Please be patient. Processing might take awhile.")

            for source in sources:
                if type(source) == discord.Member:
                    if source.bot:
                        continue
                    else:
                        try:
                            messages = await ctx.message.channel.history(limit=CHAN_HIST_LIMIT).flatten()
                            for msg in messages:
                                if msg.author == source:
                                    source_data += check_message(auth=msg.author, msg=msg, bot_provided=False)
                        except discord.errors.Forbidden:
                            continue
                elif type(source) == discord.TextChannel:
                    messages = await source.history(limit=CHAN_HIST_LIMIT).flatten()
                    for msg in messages:
                        source_data += check_message(auth=msg.author, msg=msg, bot_provided=False)
        fail_string = f"There was not enough information available to make a Markov chain for [ {[source.name for source in sources]} ]."
        if source_data:
            source_data = cleanup_source_data(source_data)
        else:
            await edit_msg.edit(content=fail_string)

        chain = markovify.NewlineText(source_data, well_formed=True)
        punctuation = ("!", ".", "?", "...")
        sentence = chain.make_sentence(max_overlap_ratio=.9, max_overlap_total=27, min_words=7, tries=100)

        if sentence is None:
            await edit_msg.edit(content=fail_string)
        else:
            sentence += random.choice(punctuation)
            await edit_msg.edit(content=sentence)

    # @commands.group()
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    # async def weather(self, ctx):
    #     """ Current weather for the next game day location """
    #
    #     if ctx.invoked_subcommand:
    #         return
    #
    #     venues = Venue()
    #     embed = None
    #     edit_msg = None
    #     _venue_name = None
    #     _weather = None
    #     _x = None
    #     _y = None
    #     _opponent = None
    #
    #     edit_msg = await ctx.send("Loading...")
    #
    #     season, season_stats = HuskerSchedule(year=datetime.now().year)
    #     # season = reversed(season)
    #
    #     for game in season:
    #         now_cst = datetime.now().astimezone(tz=TZ)
    #
    #         if now_cst < game.game_date_time.astimezone(tz=TZ):
    #             if game.location == "Memorial Stadium":
    #                 _venue_name = venues[207]["name"]
    #                 _x = venues[207]["location"]["x"]
    #                 _y = venues[207]["location"]["y"]
    #             else:
    #                 for venue in venues:
    #                     if venue["city"].lower() == game.location[0].lower() and venue["state"].lower() == game.location[1].lower():
    #                         _venue_name = venue['name']
    #                         _x = venue['location']['x']
    #                         _y = venue['location']['y']
    #                         break
    #
    #             r = requests.get(url=f"https://api.weatherbit.io/v2.0/current?key={'39b7915267f04d5f88fa5fe6be6290e6'}&lang=en&units=I&lat={_x}&lon={_y}")
    #             _weather = r.json()
    #
    #             embed = discord.Embed(
    #                 title=f"Weather Forecast for the __[ {game.opponent} ]__ in __[ {_venue_name} / {_weather['data'][0]['city_name']}, {_weather['data'][0]['state_code']} ]__",
    #                 color=0xFF0000)  # ,
    #             # description=f"Nebraska's next opponent is __[ {game.opponent} ]__")
    #
    #             break
    #
    #     if embed is None:
    #         await ctx.send("The season is over! No upcoming games found.")
    #         return
    #
    #     embed.set_thumbnail(url=f"https://www.weatherbit.io/static/img/icons/{_weather['data'][0]['weather']['icon']}.png")
    #     embed.set_footer(text="There is a daily 500 call limit to the API used for this command. Do not abuse it.")
    #     embed.add_field(name="Temperature", value=f"{_weather['data'][0]['temp']} F", inline=False)
    #     embed.add_field(name="Cloud Coverage", value=f"{_weather['data'][0]['clouds']}%", inline=False)
    #     embed.add_field(name="Wind Speed", value=f"{_weather['data'][0]['wind_spd']} MPH / {_weather['data'][0]['wind_cdir']}", inline=False)
    #     embed.add_field(name="Snow Chance", value=f"{_weather['data'][0]['snow']:.2f}%", inline=False)
    #     embed.add_field(name="Precipitation Chance", value=f"{_weather['data'][0]['precip'] * 100:.2f}%", inline=False)
    #
    #     if edit_msg is not None:
    #         await edit_msg.edit(content="", embed=embed)
    #     else:
    #         await ctx.send(embed=embed)

    @commands.command(name="24hours", aliases=["24", "24hrs", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def _24hours(self, ctx):
        """ You have 24 hours to cheer or moam about the game """
        games = HuskerSchedule(year=datetime.now().year)

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

    # @commands.command()
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    # async def whenjoined(self, ctx, who: discord.Member):
    #     """ When did you join the server? """
    #     from utils.client import client
    #
    #     def sort_second(val):
    #         return val[1]
    #
    #     users = client.get_all_members()
    #     users_sorted = []
    #
    #     for user in users:
    #         users_sorted.append([user.name, user.joined_at])
    #
    #     users_sorted.sort(key=sort_second)
    #
    #     count = 10
    #
    #     if not who:
    #         earliest = "```\n"
    #         for index, user in enumerate(users_sorted):
    #             if index < count:
    #                 earliest += f"#{index + 1:2} - {user[1]}: {user[0]}\n"
    #         earliest += "```"
    #         await ctx.send(earliest)
    #     else:
    #         for user in users_sorted:
    #             if user[0] == who.display_name:
    #                 await ctx.send(f"`{who.display_name} joined at {user[1]}`")
    #                 return

    @commands.command(aliases=["8b", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def eightball(self, ctx):
        """ Ask a Magic 8-Ball a question. """
        eight_ball = [
            'As I see it, yes.',
            'Ask again later.',
            'Better not tell you now.',
            'Cannot predict now.',
            'Coach V\'s cigar would like this!',
            'Concentrate and ask again.',
            'Definitely yes!',
            'Don’t count on it...',
            'Frosty!',
            'Fuck Iowa!',
            'It is certain.',
            'It is decidedly so.',
            'Most likely...',
            'My reply is no.',
            'My sources say no.',
            'Outlook not so good and reply hazy',
            'Scott Frost approves!',
            'These are the affirmative answers.',
            'Try again...',
            'Without a doubt.',
            'Yes – definitely!',
            'You may rely on it.'
        ]

        random.shuffle(eight_ball)

        embed = build_embed(
            title="BotFrost Magic 8-Ball :8ball: says...",
            description="These are all 100% accurate. No exceptions! Unless an answer says anyone other than Nebraska is good.",
            fields=[
                ["Response", random.choice(eight_ball)]
            ],
            thumbnail="https://i.imgur.com/L5Gpu0z.png"
        )

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
        from bs4 import BeautifulSoup
        r = requests.get(f"http://www.urbandictionary.com/define.php?term={word}")
        soup = BeautifulSoup(r.content, features="html.parser")
        try:
            definition = soup.find("div", attrs={"class": "meaning"}).text
        except AttributeError:
            definition = f"Sorry, we couldn't find: {word}"

        if len(definition) > 1024:
            definition = definition[:1020] + "..."

        import urllib.parse

        await ctx.send(
            embed=build_embed(
                title=f"Urban Dictionary Definition",
                inline=False,
                fields=[
                    [word, definition],
                    ["Link", f"https://www.urbandictionary.com/define.php?term={urllib.parse.quote(string=word)}"]
                ]
            )
        )

    @commands.command(aliases=["rm", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def remind(self, ctx, who: typing.Union[discord.TextChannel, discord.Member], when: str, *, message: str):
        """ Set a reminder for yourself or channel. Time format examples: 1d, 7h, 3h30m, 1d7h,15m """
        d_char = "d"
        h_char = "h"
        m_char = "m"
        s_char = "s"

        if type(who) == discord.Member and not ctx.author == who:
            raise ValueError("You cannot set reminders for anyone other than yourself!")
        elif type(who) == discord.TextChannel and who.id in CHAN_BANNED:
            raise ValueError(f"You cannot set reminders for {who}!")

        today = datetime.today()  # .astimezone(tz=TZ)

        def get_value(which: str, from_when: str):
            import re

            if which in from_when:
                raw = from_when.split(which)[0]
                if raw.isnumeric():
                    return int(raw)
                else:
                    try:
                        findall = re.findall(r"\D", raw)[-1]
                        return int(raw[raw.find(findall) + 1:])
                    except:
                        return 0
            else:
                return 0

        days = get_value(d_char, when)
        hours = get_value(h_char, when)
        minutes = get_value(m_char, when)
        seconds = get_value(s_char, when)

        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

        min_timer_allowed = 5

        if delta.total_seconds() < min_timer_allowed:
            raise ValueError(f"The duration entered is too short! The minimum allowed timer is {min_timer_allowed} seconds.")

        try:
            raw_when = today + delta
        except ValueError:
            raise ValueError("The duration entered is too large!")

        duration = raw_when - today

        alert = today + duration

        await ctx.send(f"Setting a timer for [{who}] in [{duration.total_seconds()}] seconds. The timer will go off at [{alert.strftime('%x %X')}].")
        author = f"{ctx.author.name}#{ctx.author.discriminator}"
        process_MySQL(sqlRecordTasks, values=(who.id, message, str(alert), 1, author))

        import nest_asyncio
        nest_asyncio.apply()
        asyncio.create_task(
            send_reminder(
                thread=1,
                duration=duration.total_seconds(),
                who=who,
                message=message,
                author=ctx.author,
                flag=str(alert)
            )
        )

    @commands.command()
    async def compare(self, ctx, compare: str, against: str):
        """Compare two team's record. Must use a dash (-) for teams with spaces.
        $compare Nebraska Ohio-State"""
        comparision = CompareWinsipedia(compare=compare, against=against)

        await ctx.send(embed=build_embed(
            title=f"Historical Records for [ {compare.title()} ] vs. [ {against.title()} ]",
            fields=[
                ["Links", f"[Full List of Games]({comparision.full_games_url})\n"
                          f"[{compare.title()} Games]({'http://www.winsipedia.com/' + compare.lower()})\n"
                          f"[{against.title()} Games]({'http://www.winsipedia.com/' + against.lower()})"],
                ["All Time Record", comparision.all_time_record],
                [f"{compare.title()}'s Largest MOV", f"{comparision.compare.largest_mov} ({comparision.compare.largest_mov_date})"],
                [f"{compare.title()}'s Longest Win Streak", f"{comparision.compare.longest_win_streak} ({comparision.compare.largest_win_streak_date})"],
                [f"{against.title()}'s Largest MOV", f"{comparision.against.largest_mov} ({comparision.against.largest_mov_date})"],
                [f"{against.title()}'s Longest Win Streak", f"{comparision.against.longest_win_streak} ({comparision.against.largest_win_streak_date})"]
            ],
            inline=False
        ))

    @commands.command()
    async def teamstats(self, ctx, *, team_name: str):
        edit_msg = await ctx.send("Loading...")

        team = TeamStatsWinsipediaTeam(team_name=team_name)

        await edit_msg.edit(content="", embed=build_embed(
            title=f"{team_name.title()} Historical Stats",
            fields=[
                ["All Time Record", f"{team.all_time_record} ({team.all_time_record_rank})"],
                ["All Time Wins", f"{team.all_time_wins} ({team.all_time_wins_rank})"],
                ["Bowl Games", f"{team.bowl_games} ({team.bowl_games_rank})"],
                ["Bowl Record", f"{team.bowl_record} ({team.bowl_record_rank})"],
                ["Championships", f"{team.championships} ({team.championships_rank})"],
                ["Conference Championships", f"{team.conf_championships} ({team.conf_championships_rank})"],
                ["Consensus All American", f"{team.conf_championships} ({team.conf_championships_rank})"],
                ["Heisman Winners", f"{team.heisman_winners} ({team.heisman_winners_rank})"],
                ["NFL Draft Picks", f"{team.nfl_draft_picks} ({team.nfl_draft_picks_rank})"],
                ["Weeks in AP Poll", f"{team.week_in_ap_poll} ({team.week_in_ap_poll})"]
            ],
            inline=False
        ))


def setup(bot):
    bot.add_cog(TextCommands(bot))

# print("### Text Commands loaded! ###")

import discord
from discord.ext import commands
import json
import dateutil
import datetime
import config
import requests
import mysql
import pytz

bet_emojis = ["⬆", "⬇", "❎", "⏫", "⏬", "❌", "🔼", "🔽", "✖"]
raw_username = ""
globalRate = 5
globalPer = 60
embed = None


def load_season_bets():
    f = open('season_bets.json', 'r')
    temp_json = f.read()
    config.season_bets = json.loads(temp_json)
    f.close()


def store_next_opponent(year):
    # Open previously generated JSON from $schedule.
    # To refresh change dump = True manually
    url = "https://api.collegefootballdata.com/games?year={}&seasonType=regular&team=nebraska".format(year)
    husker_schedule = None
    try:
        r = requests.get(url)
        husker_schedule = r.json()  # Actually imports a list
    except:
        print("Unable to pull data")

    dump = True
    if dump:
        with open("husker_schedule.json", "w") as fp:
            json.dump(husker_schedule, fp, sort_keys=True, indent=4)
        fp.close()

    # Find first game that is scheduled after now()
    counter = 1
    for events in husker_schedule:
        # The date/time is stored in ISO 8601 format. It sucks. Take raw data and manually convert it to the default format.
        check_date_raw = dateutil.parser.parse(events["start_date"])
        check_date = datetime.datetime(day=check_date_raw.day, month=check_date_raw.month, year=check_date_raw.year, hour=check_date_raw.hour, minute=check_date_raw.minute)

        check_now = datetime.datetime.now()
        if check_now <= check_date:
            config.current_game = []
            if events["home_team"] != "Nebraska":
                config.current_game.append(events["home_team"])
            else:
                config.current_game.append(events["away_team"])
            config.current_game.append(check_date)
            config.current_game.append(events["week"])

            print(config.current_game)
            break
        # Used for navigating season_bets JSON
        counter += 1


def game_number(team):
    # Retrieve the current game number
    with mysql.sqlConnection.cursor() as cursor:
        cursor.execute(config.sqlRetrieveGameNumber, (team.lower()))
        gameNumber = cursor.fetchone()
    mysql.sqlConnection.commit()
    gameNumber = int(gameNumber["game_number"])

    return int(gameNumber)


def create_embed():
    global embed
    embed = discord.Embed(title="Husker Game Betting", description="How do you think the Huskers will do in their next game? Place your bets below!", color=0xff0000)
    embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
    embed.set_footer(text=config.bet_footer)


def update_db_lines(line, gameNumber, spread):
    with mysql.sqlConnection.cursor() as cursor:
        cursor.execute(config.sqlUpdateLineInfo, (gameNumber, line["spread"], line["overUnder"], spread, line["overUnder"]))
    mysql.sqlConnection.commit()
    cursor.close()


class BetCommands(commands.Cog, name="Betting Commands"):
    @commands.group()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def bet(self, ctx):
        """ Allows users to place bets for Husker games."""
        dbAvailable = config.pingMySQL()
        if not dbAvailable:
            await ctx.send("The MySQL database is currently unavailable. Please try again later.")
            return

        apiAvailable = requests.get("https://api.collegefootballdata.com/lines?year=2019&week=9&seasonType=regular&team=nebraska")
        if apiAvailable.status_code == 502:  # TODO Add other status codes, idk what they are yet
            await ctx.send("The API services (https://api.collegefootballdata.com) is currently unavailable. Please try again later.")
            return

        # Load next opponent and bets
        store_next_opponent(datetime.datetime.now().year)
        load_season_bets()
        create_embed()

        global embed
        global raw_username
        raw_username = "{}".format(ctx.author)

        if ctx.subcommand_passed:
            return

        # Outputs the betting message to allow the user to see the upcoming opponent and voting reactions.
        url = "https://api.collegefootballdata.com/lines?year={}&week={}&seasonType=regular&team=nebraska".format(config.current_game[1].year, config.current_game[2])

        try:
            r = requests.get(url)
            game_data_raw = r.json()
        except:
            await ctx.send("An error occurred retrieving line data.")
            return

        lines = {}
        try:
            for lines_raw in game_data_raw:
                lines = lines_raw["lines"]
        except:
            pass

        game_dt_raw = config.current_game[1]
        game_dt_utc = pytz.timezone("UTC").localize(game_dt_raw)
        tz_target = pytz.timezone("CST6CDT")
        game_dt_cst = game_dt_utc.astimezone(tz_target)

        embed.add_field(name="Opponent", value="{}\n{}".format(config.current_game[0], game_dt_cst.strftime("%B %d, %Y at %H:%M %p CST")), inline=False)
        embed.add_field(name="Rules", value="1. All bets must be placed prior to kick off.\n2. The final odds are used for scoring purposes.\n3. Only one bet per user per game.\n4. Bets are stored by __Discord__ username.")
        embed.add_field(name="Scoring", value="1 Point : winning or losing the game.\n2 Points: covering or not covering the spread and total points.", inline=False)
        embed.add_field(name="Usage", value="$bet - Show this command\n$bet show - Shows your currently placed bets\n$bet all - Shows the current breakout of all bets placed\n$bet winners [opponent] - Shows the winners for the selected opponent.")

        if lines:
            formatted_spread = lines[0]["formattedSpread"]
            provider = lines[0]["provider"]
            spread = float(lines[0]["spread"])
            over_under = lines[0]["overUnder"]
            if over_under is None:
                over_under = "N/A"

            if lines[0]["formattedSpread"].startswith("Nebraska"):
                embed.add_field(name=f"Spread ({provider})", value=f"{formatted_spread}", inline=False)
            else:
                embed.add_field(name=f"Spread ({provider})", value=f"+{abs(spread)} Nebraska", inline=False)

            embed.add_field(name=f"Total Points/Over Under ({provider})", value=f"{over_under}", inline=False)

            if lines[0]["formattedSpread"].startswith("Nebraska"):
                update_db_lines(lines[0], config.current_game[2], spread)
            else:
                update_db_lines(lines[0], config.current_game[2], abs(spread))
        else:
            embed.add_field(name="Spread (TBD)", value="TBD")
            embed.add_field(name="Total Points/Over Under (TBD)", value="TBD")

        embed.add_field(name="Vote Instructions", value=
        "Bets winning (⬆) or losing (⬇) the game. Clear bet (❎).\n"
        "Bets Nebraska covers (⏫) or doesn't cover (⏬) the spread. Clear bet (❌).\n"
        "Bets over (🔼) or under (🔽) on total points. Clear bet (✖).\n", inline=False)

        # Store message sent in an object to allow for reactions afterwards
        check_now_raw = datetime.datetime.now()
        check_now = dateutil.parser.parse(str(check_now_raw))

        msg_sent = await ctx.send(embed=embed)
        check_game_datetime = config.current_game[1]

        print(check_now)

        # if check_now + datetime.timedelta(hours=5) < check_game_datetime:
        if check_now < check_game_datetime:
            for e in bet_emojis:
                await msg_sent.add_reaction(e)
        else:
            print("Reactions not applied because datetime is after kickoff.")

    @bet.command(aliases=["a", ])
    async def all(self, ctx, *, team=None):
        """Show all the bets for the current or provided opponent."""
        global embed

        if team is None:
            with mysql.sqlConnection.cursor() as cursor:
                cursor.execute(config.sqlRetrieveAllBet, (config.current_game[2]))
                userBetsDict = cursor.fetchall()
            mysql.sqlConnection.commit()
        else:
            gameNumber = game_number(team.lower())
            with mysql.sqlConnection.cursor() as cursor:
                cursor.execute(config.sqlRetrieveAllBet, (gameNumber))
                userBetsDict = cursor.fetchall()
            mysql.sqlConnection.commit()

        total_wins = 0
        total_losses = 0
        total_cover_spread = 0
        total_not_cover_spread = 0
        total_cover_moneyline = 0
        total_not_cover_moneyline = 0

        for userBet in userBetsDict:
            if userBet["win"] == 1:
                total_wins += 1
            elif userBet["win"] == 0:
                total_losses += 1

            if userBet["spread"] == 1:
                total_cover_spread += 1
            elif userBet["spread"] == 0:
                total_not_cover_spread += 1

            if userBet["moneyline"] == 1:
                total_cover_moneyline += 1
            elif userBet["moneyline"] == 0:
                total_not_cover_moneyline += 1

        total_winorlose = total_losses + total_wins
        total_spread = total_cover_spread + total_not_cover_spread
        total_moneyline = total_cover_moneyline + total_not_cover_moneyline

        # Creates the embed object for all messages within method
        embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
        embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
        embed.set_footer(text=config.bet_footer)
        if team is None:
            embed.add_field(name="Opponent", value=config.current_game[0], inline=False)
        else:
            embed.add_field(name="Opponent", value=str(team).capitalize(), inline=False)

        if total_wins and total_winorlose:
            embed.add_field(name="Wins", value="{} ({:.2f}%)".format(total_wins, (total_wins / total_winorlose) * 100))
            embed.add_field(name="Losses", value="{} ({:.2f}%)".format(total_losses, (total_losses / total_winorlose) * 100))
        else:
            embed.add_field(name="Wins", value="{} ({:.2f}%)".format(total_wins, 0))
            embed.add_field(name="Losses", value="{} ({:.2f}%)".format(total_losses, 0))

        if total_cover_spread and total_spread:
            embed.add_field(name="Cover Spread", value="{} ({:.2f}%)".format(total_cover_spread, (total_cover_spread / total_spread) * 100))
            embed.add_field(name="Not Cover Spread", value="{} ({:.2f}%)".format(total_not_cover_spread, (total_not_cover_spread / total_spread) * 100))
        else:
            embed.add_field(name="Cover Spread", value="{} ({:.2f}%)".format(total_cover_spread, 0))
            embed.add_field(name="Not Cover Spread", value="{} ({:.2f}%)".format(total_not_cover_spread, 0))

        if total_cover_spread and total_not_cover_moneyline:
            embed.add_field(name="Total Points Over", value="{} ({:.2f}%)".format(total_cover_moneyline, (total_cover_moneyline / total_moneyline) * 100))
            embed.add_field(name="Total Points Under", value="{} ({:.2f}%)".format(total_not_cover_moneyline, (total_not_cover_moneyline / total_moneyline) * 100))
        else:
            embed.add_field(name="Total Points Over", value="{} ({:.2f}%)".format(total_cover_moneyline, 0))
            embed.add_field(name="Total Points Under", value="{} ({:.2f}%)".format(total_not_cover_moneyline, 0))

        await ctx.send(embed=embed)

    @bet.command(aliases=["win", "w", ])
    async def winners(self, ctx, *, team):
        """Show the winners for the current or provided opponent."""
        if not team:
            await ctx.send("You must include a team. Example: `$bet winners south alabama`")
            return

        team = str(team).lower()
        global embed

        # Need to add check if command is run the day after the game
        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlGetWinWinners, team)
            winners_winorlose = cursor.fetchall()

            cursor.execute(config.sqlGetSpreadWinners, team)
            winners_spread = cursor.fetchall()

            cursor.execute(config.sqlGetMoneylineWinners, team)
            winners_moneyline = cursor.fetchall()

        mysql.sqlConnection.commit()

        def flattenList(param):
            flat = ""
            for item in param:
                flat += item["user"] + "\n"
            if not flat:
                flat = "N/A"
            return flat

        winners_winorlose = flattenList(winners_winorlose)
        winners_spread = flattenList(winners_spread)
        winners_moneyline = flattenList(winners_moneyline)

        embed.add_field(name="Win or Lose Winners", inline=True, value=winners_winorlose)
        embed.add_field(name="Spread Winners", inline=True, value=winners_spread)
        embed.add_field(name="Total Points Winners", inline=True, value=winners_moneyline)

        await ctx.send(embed=embed)

    @bet.command(aliases=["lb", ])
    async def leaderboard(self, ctx):
        """Shows the leaderboard for the season."""
        global embed

        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlLeaderboard)
            sqlLeaderboard = cursor.fetchmany(size=10)
        mysql.sqlConnection.commit()

        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlAdjustedLeaderboard)
            sqlAverageLeaderboard = cursor.fetchmany(size=10)
        mysql.sqlConnection.commit()

        strLeader = ""
        for user in sqlLeaderboard:
            strLeader += "[{} pts] {}\n".format(int(user["total_points"]), user["user"])

        strAdjustedLeader = ""
        for user in sqlAverageLeaderboard:
            strAdjustedLeader += "[{} pts] {}\n".format(int(user["avg_pts_per_game"]), user["user"])

        embed.add_field(name="Top 10 Ranking", value=strLeader)
        embed.add_field(name="Top 10 Average Points Ranking", value=strAdjustedLeader)
        await ctx.send(embed=embed)

    @bet.command(aliases=["s", ])
    async def show(self, ctx, *, team=None):
        """Shows the current or provided opponent placed bet(s)."""
        userBetWin = "N/A"
        userBetSpread = "N/A"
        userBetMoneyline = "N/A"
        global raw_username
        global embed

        messages = ("Win the game", "Lose the game", "Nebraska covers the spread", "Nebraska does not cover the spread", "The total points go over", "The total points go under")

        if team:
            gameNumber = game_number(team.lower())

            # Retrieve the user's bet
            with mysql.sqlConnection.cursor() as cursor:
                cursor.execute(config.sqlRetrieveSpecificBet, (gameNumber, raw_username))
                checkUserBet = cursor.fetchone()
            mysql.sqlConnection.commit()

            if checkUserBet["win"] == 1:
                userBetWin = messages[0]
            elif checkUserBet["win"] == 0:
                userBetWin = messages[1]

            if checkUserBet["spread"] == 1:
                userBetSpread = messages[2]
            elif checkUserBet["spread"] == 0:
                userBetSpread = messages[3]

            if checkUserBet["moneyline"] == 1:
                userBetMoneyline = messages[4]
            elif checkUserBet["moneyline"] == 0:
                userBetMoneyline = messages[5]

            try:
                lastUpdate = checkUserBet["date_updated"]
            except:
                lastUpdate = "N/A"

            opponentName = team.title()
        else:
            # Retrieve the user's bet
            with mysql.sqlConnection.cursor() as cursor:
                cursor.execute(config.sqlRetrieveBet, raw_username)
                userBetsDict = cursor.fetchall()
            mysql.sqlConnection.commit()

            checkUserBet = userBetsDict[len(userBetsDict) - 1]

            if checkUserBet["game_number"] == config.current_game[2]:
                if checkUserBet["win"] == 1:
                    userBetWin = messages[0]
                elif checkUserBet["win"] == 0:
                    userBetWin = messages[1]

                if checkUserBet["spread"] == 1:
                    userBetSpread = messages[2]
                elif checkUserBet["spread"] == 0:
                    userBetSpread = messages[3]

                if checkUserBet["moneyline"] == 1:
                    userBetMoneyline = messages[4]
                elif checkUserBet["moneyline"] == 0:
                    userBetMoneyline = messages[5]

                try:
                    lastUpdate = checkUserBet["date_updated"]
                except:
                    lastUpdate = "N/A"

                opponentName = config.current_game[0].title()
            else:
                await ctx.send("You have no bets for the next game against {}. Check out `$bet` to place your bets!".format(config.current_game[0].title()))
                return

        embed.add_field(name="Author", value=raw_username, inline=False)
        embed.add_field(name="Opponent", value=opponentName, inline=False)
        embed.add_field(name="Win or Loss", value=userBetWin, inline=True)
        embed.add_field(name="Spread", value=userBetSpread, inline=True)
        embed.add_field(name="Over/Under Total Points", value=userBetMoneyline, inline=True)
        embed.add_field(name="Time Placed", value=lastUpdate)
        await ctx.send(embed=embed)

    @bet.command(aliases=["line", "l", ])
    async def lines(self, ctx, *, team=None):
        """Shows the current or provided opponent lines."""
        global embed

        if team is None:
            gameNumber = game_number(config.current_game[0].lower())
        else:
            gameNumber = game_number(team.lower())

        url = "https://api.collegefootballdata.com/lines?year=2019&seasonType=regular&team=nebraska&week={}".format(gameNumber)

        try:
            r = requests.get(url)
            game_data_raw = r.json()
        except:
            await ctx.send("An error occurred retrieving line data.")
            return

        lines = {}
        try:
            for lines_raw in game_data_raw:
                lines = lines_raw["lines"]
        except:
            print("No lines available")

        if lines:
            for line in lines:
                if line["provider"] == "Bovada":
                    formatted_spread = line["formattedSpread"]
                    provider = line["provider"]
                    spread = float(line["spread"])
                    over_under = line["overUnder"]
                    if over_under is None:
                        over_under = "N/A"

                    if line["formattedSpread"].startswith("Nebraska"):
                        embed.add_field(name=f"Spread ({provider})", value=f"{formatted_spread}", inline=False)
                    else:
                        embed.add_field(name=f"Spread ({provider})", value=f"+{abs(spread)} Nebraska", inline=False)

                    embed.add_field(name=f"Total Points/Over Under ({provider})", value=f"{over_under}", inline=False)

                    if line["formattedSpread"].startswith("Nebraska"):
                        update_db_lines(line, config.current_game[2], spread)
                    else:
                        update_db_lines(line, config.current_game[2], abs(spread))
                    break
        else:
            embed.add_field(name="Spread", value="TBD")
            embed.add_field(name="Total Points/Over Under", value="TBD")

        await ctx.send(embed=embed)

    @bet.command(hidden=True)
    @commands.has_any_role(606301197426753536, 440639061191950336, 443805741111836693)
    async def scores(self, ctx, score, oppo_score, *, team):
        gameNumber = game_number(team.lower())

        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlUpdateScores, (gameNumber, score, oppo_score, score, oppo_score))
        mysql.sqlConnection.commit()
        cursor.close()

        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlRetrieveGameInfo, gameNumber)
            game_info = cursor.fetchone()
        mysql.sqlConnection.commit()
        cursor.close()

        result_winorlose = bool(
            int(game_info["score"]) > int(game_info["opponent_score"])
        )

        result_spread = None
        if game_info["spread_value"] > 0:
            result_spread = not bool(
                (game_info["opponent_score"] - game_info["score"]) > game_info["spread_value"]
            )
        elif game_info["spread_value"] < 0:
            result_spread = bool(
                (game_info["score"] - game_info["opponent_score"]) > abs(game_info["spread_value"])
            )

        result_moneyline = bool(
            int(
                (game_info["score"] + game_info["opponent_score"]) > game_info["moneyline_value"]
            )
        )

        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlUpdateAllBetCategories, (gameNumber, True, result_winorlose, result_spread, result_moneyline, True, result_winorlose, result_spread, result_moneyline))
            game_info = cursor.fetchone()
        mysql.sqlConnection.commit()

        await ctx.send("Updated! The results are:\nNebraska: {}\nOpponent: {}\nWin (Yes==True, No==False): {}\nSpread (): {}\nTotal Points: {}".format(
            score,
            oppo_score,
            result_winorlose,
            result_spread,
            result_moneyline
        ))


def setup(bot):
    bot.add_cog(BetCommands(bot))

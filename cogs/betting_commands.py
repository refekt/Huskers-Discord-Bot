import discord
from discord.ext import commands
import json
import dateutil
import datetime
import config
import requests
import mysql

bet_emojis = ["⬆", "⬇", "❎", "⏫", "⏬", "❌", "🔼", "🔽", "✖"]
stored_bets = dict()


# Load season bets
def load_season_bets():
    f = open('season_bets.json', 'r')
    temp_json = f.read()
    config.season_bets = json.loads(temp_json)
    f.close()


# Allows the ability to load next opponent for sub commands.
def store_next_opponent():
    # Open previously generated JSON from $schedule.
    # To refresh change dump = True manually
    f = open('husker_schedule.json', 'r')
    temp_json = f.read()
    husker_schedule = json.loads(temp_json)
    f.close()

    # Find first game that is scheduled after now()
    counter = 1
    for events in husker_schedule:
        # The date/time is stored in ISO 8601 format. It sucks. Take raw data and manually convert it to the default format.
        check_date_raw = dateutil.parser.parse(events["start_date"])
        check_date = datetime.datetime(day=check_date_raw.day, month=check_date_raw.month, year=check_date_raw.year, hour=check_date_raw.hour, minute=check_date_raw.minute)
        #check_date = check_date - datetime.timedelta(hours=5)

        check_now = datetime.datetime.now()
        # hourPadding = datetime.timedelta(hours=5)

        if check_now < check_date:
            if events["home_team"] != "Nebraska":
                config.current_game.append(events["home_team"])
            else:
                config.current_game.append(events["away_team"])
            config.current_game.append(check_date)
            config.current_game.append(counter)
            break
        # Used for navigating season_bets JSON
        counter += 1


class BetCommands(commands.Cog, name="Betting Commands"):
    @commands.command()
    async def bet(self, ctx, cmd=None, *, team=None):
        """ Allows users to place bets for Husker games.

        Command usage:
        $bet: show default message and place bets.
        $bet all: show all current bets.
        $bet lines: shows the current lines.
        $bet show <optional, team>: show your most recent bet or bet for another team
        $bet winners <team>: show all the winners of a specific game.
        """

        # Creates the embed object for all messages within method
        embed = discord.Embed(title="Husker Game Betting", description="How do you think the Huskers will do in their next game? Place your bets below!", color=0xff0000)
        embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
        embed.set_footer(text=config.bet_footer)

        # Load next opponent and bets
        store_next_opponent()
        load_season_bets()

        game = config.current_game[0].lower()
        season_year = int(datetime.date.today().year) - 2019  # Future proof
        raw_username = "{}".format(ctx.author)

        # Outputs the betting message to allow the user to see the upcoming opponent and voting reactions.
        if cmd is None:
            if not team:
                team = config.current_game[0].lower()

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
                print("No lines available")

            embed.add_field(name="Opponent", value="{}\n{}".format(config.current_game[0], config.current_game[1].strftime("%B %d, %Y at %H:%M %p CST")), inline=False)
            embed.add_field(name="Rules", value="1. All bets must be placed prior to kick off.\n"
                                                "2. The final odds are used for scoring purposes.\n"
                                                "3. Only one bet per user per game.\n"
                                                "4. Bets are stored by __Discord__ username.")
            embed.add_field(name="Scoring", value="1 Point: winning or losing the game.\n"
                                                  "2 Points: covering or not covering the spread and total points.\n"
                                                  "\nPrizes haven't been determined yet.", inline=False)
            embed.add_field(name="Usage", value="$bet - Show this command\n$bet show - Shows your currently placed bets\n$bet all - Shows the current breakout of all bets placed\n$bet winners [opponent] - Shows the winners for the selected opponent.")

            if lines:
                embed.add_field(name="Spread ({})".format(lines[0]["provider"]), value="{}".format(lines[0]["formattedSpread"]), inline=False)
                embed.add_field(name="Total Points/Over Under ({})".format(lines[0]["provider"]), value="{}".format(lines[0]["overUnder"]), inline=False)
            else:
                embed.add_field(name="Spread (TBD)", value="TBD")
                embed.add_field(name="Total Points/Over Under (TBD)", value="TBD")

            embed.add_field(name="Vote Instructions", value=""
                                                            "Bets winning (⬆) or losing (⬇) the game. Clear bet (❎).\n"
                                                            "Bets over (⏫) or under (⏬) on the spread. Clear bet (❌).\n"
                                                            "Bets over (🔼) or under (🔽) on total points. Clear bet (✖).\n", inline=False)

            # Store message sent in an object to allow for reactions afterwards
            check_now_raw = datetime.datetime.now()
            check_now = dateutil.parser.parse(str(check_now_raw))

            f = open('husker_schedule.json', 'r')
            temp_json = f.read()
            husker_schedule = json.loads(temp_json)
            f.close()

            msg_sent = await ctx.send(embed=embed)

            # debug_datetime = datetime.datetime.strptime("2019-08-20T16:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
            check_game_datetime = datetime.datetime.strptime(husker_schedule[(config.current_game[2] - 1)]["start_date"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if check_now < check_game_datetime:
                for e in bet_emojis:
                    await msg_sent.add_reaction(e)
            else:
                print("Reactions not applied because datetime is after kickoff.")

        # Show the user's current bet(s)
        elif cmd == "show":
            f = open('season_bets.json', 'r')
            temp_json = f.read()
            season_bets_JSON = json.loads(temp_json)
            f.close()

            if team:
                temp_dict = season_bets_JSON[season_year]['opponent'][team]['bets'][0]
            else:
                temp_dict = season_bets_JSON[season_year]['opponent'][game]['bets'][0]

            if len(temp_dict) == 0:
                await ctx.send("No placed bet(s) found for this game.")
                return

            # Creates the embed object for all messages within method
            embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
            embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
            embed.set_footer(text=config.bet_footer)

            if raw_username in temp_dict:
                try:
                    winorlose = temp_dict[raw_username]['winorlose']
                    if winorlose == "True":
                        winorlose = "Win"
                    elif winorlose == "False":
                        winorlose = "Lose"
                except:
                    winorlose = "N/A"

                try:
                    spread = temp_dict[raw_username]['spread']
                    if spread == "True":
                        spread = "Over"
                    elif spread == "False":
                        spread = "Under"
                except:
                    spread = "N/A"

                try:
                    moneyline = temp_dict[raw_username]['moneyline']
                    if moneyline == "True":
                        moneyline = "Over"
                    elif moneyline == "False":
                        moneyline = "Under"
                except:
                    moneyline = "N/A"

                embed.add_field(name="Author", value=raw_username, inline=False)
                if team:
                    embed.add_field(name="Opponent", value=str(team).capitalize(), inline=False)
                else:
                    embed.add_field(name="Opponent", value=config.current_game[0], inline=False)
                embed.add_field(name="Win or Loss", value=winorlose, inline=True)
                embed.add_field(name="Spread", value=spread, inline=True)
                embed.add_field(name="Total Points/Over Under", value=moneyline, inline=True)
                await ctx.send(embed=embed)
            else:
                print(raw_username)
                await ctx.send("You have no placed bet(s) on this game.")

        # Show all bets for the current game
        elif cmd == "all":
            # Creates the embed object for all messages within method
            embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
            embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
            embed.set_footer(text=config.bet_footer)

            temp_dict = config.season_bets[season_year]['opponent'][game]['bets'][0]
            if len(temp_dict) == 0:
                await ctx.send("No bets have been placed yet.")
                return

            total_wins = 0
            total_losses = 0
            total_cover_spread = 0
            total_not_cover_spread = 0
            total_cover_moneyline = 0
            total_not_cover_moneyline = 0

            for usr in temp_dict:
                if temp_dict[usr]['winorlose'] == "True":
                    total_wins += 1
                elif temp_dict[usr]['winorlose'] == "False":
                    total_losses += 1

                if temp_dict[usr]['spread'] == "True":
                    total_cover_spread += 1
                elif temp_dict[usr]['spread'] == "False":
                    total_not_cover_spread += 1

                if temp_dict[usr]['moneyline'] == "True":
                    total_cover_moneyline += 1
                elif temp_dict[usr]['moneyline'] == "False":
                    total_not_cover_moneyline += 1

            total_winorlose = total_losses + total_wins
            total_spread = total_cover_spread + total_not_cover_spread
            total_moneyline = total_cover_moneyline + total_not_cover_moneyline

            embed.add_field(name="Opponent", value=config.current_game[0], inline=False)
            embed.add_field(name="Wins", value="{} ({:.2f}%)".format(total_wins, (total_wins / total_winorlose) * 100))
            embed.add_field(name="Losses", value="{} ({:.2f}%)".format(total_losses, (total_losses / total_winorlose) * 100))

            embed.add_field(name="Cover Spread", value="{} ({:.2f}%)".format(total_cover_spread, (total_cover_spread / total_spread) * 100))
            embed.add_field(name="Not Cover Spread", value="{} ({:.2f}%)".format(total_not_cover_spread, (total_not_cover_spread / total_spread) * 100))

            embed.add_field(name="Total Points Over", value="{} ({:.2f}%)".format(total_cover_moneyline, (total_cover_moneyline / total_moneyline) * 100))
            embed.add_field(name="Total Points Under", value="{} ({:.2f}%)".format(total_not_cover_moneyline, (total_not_cover_moneyline / total_moneyline) * 100))
            await ctx.send(embed=embed)

        # Show all winners for game
        elif cmd == "winners":
            if not team:
                return

            # Need to add check if command is run the day after the game
            if team:
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

                embed.add_field(name="Win or Lose Winners", value=winners_winorlose)
                embed.add_field(name="Win or Lose Winners", value=winners_spread)
                embed.add_field(name="Win or Lose Winners", value=winners_moneyline)

                await ctx.send(embed=embed)
            #     try:
            #         # Creates the embed object for all messages within method
            #         embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
            #         embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
            #         embed.set_footer(text=config.bet_footer)
            #
            #         temp_dict = config.season_bets[season_year]['opponent'][team.lower()]['bets'][0]
            #
            #         outcome_winorlose = True
            #         outcome_spread = True
            #         outcome_moneyline = True
            #
            #         if config.season_bets[season_year]['opponent'][team.lower()]['outcome_winorlose'] == "None":
            #             outcome_winorlose = False
            #
            #         if config.season_bets[season_year]['opponent'][team.lower()]['outcome_spread'] == "None":
            #             outcome_spread = False
            #
            #         if config.season_bets[season_year]['opponent'][team.lower()]['outcome_moneyline'] == "None":
            #             outcome_moneyline = False
            #
            #         for usr in temp_dict:
            #             if temp_dict[usr]['winorlose'] == config.season_bets[season_year]['opponent'][team.lower()]['outcome_winorlose'] and outcome_winorlose:
            #                 winners_winorlose.append(usr)
            #
            #             if temp_dict[usr]['spread'] == config.season_bets[season_year]['opponent'][team.lower()]['outcome_spread'] and outcome_spread:
            #                 winners_spread.append(usr)
            #
            #             if temp_dict[usr]['moneyline'] == config.season_bets[season_year]['opponent'][team.lower()]['outcome_moneyline'] and outcome_moneyline:
            #                 winners_moneyline.append(usr)
            #
            #         win_winorlose_string = ""
            #         win_spread_string = ""
            #         win_moneyline_string = ""
            #
            #         if winners_winorlose:
            #             for winner in winners_winorlose:
            #                 win_winorlose_string = win_winorlose_string + "{}\n".format(winner)
            #
            #         if winners_spread:
            #             for winner in winners_spread:
            #                 win_spread_string = win_spread_string + "{}\n".format(winner)
            #
            #         if winners_moneyline:
            #             for winner in winners_moneyline:
            #                 win_moneyline_string = win_moneyline_string + "{}\n".format(winner)
            #
            #         embed.add_field(name="Opponent", value=team.title(), inline=False)
            #
            #         if win_winorlose_string:
            #             embed.add_field(name="⭐ Win/Loss Winners", value=win_winorlose_string, inline=True)
            #         else:
            #             embed.add_field(name="⭐ Win/Loss Winners", value="N/A", inline=True)
            #
            #         if win_spread_string:
            #             embed.add_field(name="⭐ Spread Winners", value=win_spread_string, inline=True)
            #         else:
            #             embed.add_field(name="⭐ Spread Winners", value="N/A", inline=True)
            #
            #         if win_moneyline_string:
            #             embed.add_field(name="⭐ Over Under/Total Points Winners", value=win_moneyline_string, inline=True)
            #         else:
            #             embed.add_field(name="⭐ Over Under/Total Points Winners", value="N/A", inline=True)
            #
            #         await ctx.send(embed=embed)
            #
            #     except discord.HTTPException as err:
            #         print("Embed Name: {}\nEmbed Value: {}".format(embed.fields[1].name, embed.fields[1].value))
            #         print("Error Text: {}".format(err.text))
            #         await ctx.send("Something happened in the backend of hte program. Please alert the bot owners!")
            #     except:
            #         await ctx.send("Cannot find the opponent \"{}\". Please verify the team is on the schedule for the {} season and it is spelled correctly. Opponents can be found by using `$schedule|shed {}`".format(team, 2019 + season_year, 2019 + season_year))
            # else:
            #     await ctx.send("An opponent team must be included. Example: `$bet winners South Alabama` or `$bet winners Iowa`")
            pass

        # Show the current leader board. +/- 1 point for winorlose, +/- 2 points for spread and total points
        elif cmd == "leaderboard" or cmd == "lb":
            # def createBlankLeaderboard():
            #     newLB = "{\"season\": \"2019\", \"users\": [{\"bot\": {\"winorlose\": 0, \"spread\": 0, \"moneyline\": 0, \"_total\": 0}}]}"
            #
            #     with open("season_leaderboard.json", "w") as json_file:
            #         json_file.seek(0)
            #         json_file.write(str(newLB))
            #
            # createBlankLeaderboard()  # Load a blank leaderboard -- erases everything
            #
            # f = open('season_leaderboard.json', 'r')
            # temp_json = f.read()
            # leaderboard = json.loads(temp_json)
            # f.close()
            #
            # def isInLeaderboard(user: str):
            #     if user in leaderboard["users"][0].keys():
            #         # print("User [{}] was found.".format(user))
            #         return True
            #
            #     # print("User [{}] was not found.".format(user))
            #     return False
            #
            # load_season_bets()
            #
            # seasonBets = config.season_bets[0]["opponent"]
            # # 1.  Loop through games for "finished" == "True"
            # for game in seasonBets:
            #     if config.season_bets[0]["opponent"][game]["finished"] == "True":
            #         # 1.1 Create a dictionary of usernames from bets within finished games
            #         for bets in config.season_bets[0]["opponent"][game]["bets"]:
            #             # Add put all points in
            #             for user in bets:
            #                 # 2.1 Loop through bets to compare "outcome_winorlose", add or subtract points for username
            #                 if config.season_bets[0]["opponent"][game]["outcome_winorlose"] == bets[user]["winorlose"]:
            #                     if isInLeaderboard(user):
            #                         leaderboard["users"][0][user] = dict(
            #                             moneyline=leaderboard["users"][0][user]["moneyline"],
            #                             spread=leaderboard["users"][0][user]["spread"],
            #                             winorlose=leaderboard["users"][0][user]["winorlose"] + 1,
            #                             _total=0
            #                         )
            #                     else:
            #                         leaderboard["users"][0][user] = dict(moneyline=0, spread=0, winorlose=1, total=0)
            #                 # 2.2 Loop through bets to compare "outcome_spread", add or subtract points for username
            #                 if config.season_bets[0]["opponent"][game]["outcome_spread"] == bets[user]["spread"]:
            #                     if isInLeaderboard(user):
            #                         leaderboard["users"][0][user] = dict(
            #                             moneyline=leaderboard["users"][0][user]["moneyline"],
            #                             spread=leaderboard["users"][0][user]["spread"] + 2,
            #                             winorlose=leaderboard["users"][0][user]["winorlose"],
            #                             _total=0
            #                         )
            #                     else:
            #                         leaderboard["users"][0][user] = dict(moneyline=0, spread=2, winorlose=0, total=0)
            #                 # 2.3 Loop through bets to compare "outcome_moneyline", add or subtract points for username
            #                 if config.season_bets[0]["opponent"][game]["outcome_moneyline"] == bets[user]["moneyline"]:
            #                     if isInLeaderboard(user):
            #                         leaderboard["users"][0][user] = dict(
            #                             moneyline=leaderboard["users"][0][user]["moneyline"] + 2,
            #                             spread=leaderboard["users"][0][user]["spread"],
            #                             winorlose=leaderboard["users"][0][user]["winorlose"],
            #                             _total=0
            #                         )
            #                     else:
            #                         leaderboard["users"][0][user] = dict(moneyline=2, spread=0, winorlose=0, total=0)
            #
            # # 3.  Print out the dictionary
            # del leaderboard["users"][0]["bot"]
            #
            # for user in leaderboard["users"][0]:
            #     if not user == "bot":
            #         total = \
            #             leaderboard["users"][0][user]["moneyline"] + \
            #             leaderboard["users"][0][user]["spread"] + \
            #             leaderboard["users"][0][user]["winorlose"]
            #
            #         leaderboard["users"][0][user]["_total"] = total
            #
            # def secondKey(elem):
            #     return elem[1]
            #
            # sortedLeaderboard = []
            #
            # for user in leaderboard["users"][0]:
            #     sortedLeaderboard += [(user, leaderboard["users"][0][user]["_total"])]
            # sortedLeaderboard = sorted(sortedLeaderboard, key=secondKey, reverse=True)
            #
            # sortedString = ""
            # for user in sortedLeaderboard:
            #     if user != "bot":
            #         sortedString += "{}: {}\n".format(user[0], user[1])
            #
            # #embed.add_field(name="Leaderboard", value=sortedString[:1024])
            # #await ctx.send(embed=embed)
            #
            # # 4 Save.
            # dump = True
            # if dump:
            #     with open("season_leaderboard.json", "w") as json_file:
            #         json.dump(leaderboard, json_file, sort_keys=True, indent=4)
            #     json_file.close()


            # try:
            with mysql.sqlConnection.cursor() as cursor:
                cursor.execute(config.sqlLeaderboard)
                # sqlLb = cursor.fetchall()
                sqlLb = cursor.fetchmany(size=10)

            mysql.sqlConnection.commit()
            # finally:
            #     mysql.sqlConnection.close()

            strLeader = ""
            for user in sqlLb:
                strLeader += "[{} pts] {}\n".format(int(user["total_points"]), user["user"])


            embed.add_field(name="Top 10 Ranking", value=strLeader)
            await ctx.send(embed=embed)

        # Show the current lines if available
        elif cmd == "lines":
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
                print("No lines available")

            if lines:
                embed.add_field(name="Spread ({})".format(lines[0]["provider"]), value="{}".format(lines[0]["formattedSpread"]), inline=False)
                embed.add_field(name="Total Points/Over Under ({})".format(lines[0]["provider"]), value="{}".format(lines[0]["overUnder"]), inline=False)
            else:
                embed.add_field(name="Spread (TBD)", value="TBD")
                embed.add_field(name="Total Points/Over Under (TBD)", value="TBD")

            await ctx.send(embed=embed)

        else:
            embed.add_field(name="Error", value="Unknown command. Please reference `$help bet`.")
            await ctx.send(embed=embed)

    @commands.command()
    async def procbets(self, ctx):
        pass


def setup(bot):
    bot.add_cog(BetCommands(bot))

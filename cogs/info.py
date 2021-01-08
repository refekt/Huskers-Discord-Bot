import discord
from discord.ext import commands
import requests
import json
from utils.misc import seperArgs

BASE_CFBD_URL = 'https://api.collegefootballdata.com'

class infoCommands(commands.Cog):
    pass
    # @commands.command()
    # async def matchup(self, ctx, *, arg):
        # '''Get historical record between two teams, separated by a comma. Pass only one team and get the historical record between that team and Nebraska.
        # '''
        # headers = {'accept' : 'application/json'}
        # teams = seperArgs(arg, ',')
        # if len(teams) > 2:
            # await ctx.send("You can't compare more than 2 teams!")
            # return
        # elif len(teams) == 1:
            # teams = ['Nebraska'] + teams
        # MATCHUP_URI = f"/teams/matchup?team1={teams[0]}&team2={teams[1]}"
        # matchup_response = requests.get(url=BASE_CFBD_URL+MATCHUP_URI, headers=headers)
        # matchup = json.loads(matchup_response.content)
        
        # team1 = matchup['team1'] if 'team1' in matchup else teams[0]
        # team2 = matchup['team2'] if 'team2' in matchup else teams[1]
        # matchup_string = f"{team1} {matchup['team1Wins']} - {matchup['ties']} - {matchup['team2Wins']} {team2}"
        # await ctx.send(matchup_string)

def setup(bot):
    bot.add_cog(infoCommands(bot))
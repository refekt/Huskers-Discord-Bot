import discord
from discord.ext import commands

from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE
from utils.embed import build_embed

signals = {
    "holding": "https://www.ducksters.com/sports/football/signal_holding.JPG",
    "delay": "https://www.ducksters.com/sports/football/signal_delay_of_game.JPG",
    "offside": "https://www.ducksters.com/sports/football/signal_offside.JPG",
    "facemask": "https://www.ducksters.com/sports/football/signal_facemask.JPG",
    "falsestart": "https://www.ducksters.com/sports/football/signal_false_start.JPG",
    "grounding": "https://www.ducksters.com/sports/football/signal_grounding.JPG",
    "clipping": "https://www.ducksters.com/sports/football/signal_clipping.JPG",
    "blockinback": "https://www.ducksters.com/sports/football/signal_illegal_block_in_back.JPG",
    "motion": "https://www.ducksters.com/sports/football/signal_illegal_motion.JPG",
    "passinterference": "https://www.ducksters.com/sports/football/signal_pass_interference.JPG",
    "personalfoul": "https://www.ducksters.com/sports/football/signal_personal_foul.JPG",
    "roughingkicker": "https://www.ducksters.com/sports/football/signal_roughing_kicker.JPG",
    "roughingpasser": "https://www.ducksters.com/sports/football/signal_roughing_passer.JPG",
    "unsportsmanlike": "https://www.ducksters.com/sports/football/signal_unsportsmanlike_conduct.JPG",
    "touchdown": "https://www.ducksters.com/sports/football/signal_touchdown.JPG",
    "safety": "https://www.ducksters.com/sports/football/signal_safety.JPG",
    "first": "https://www.ducksters.com/sports/football/signal_first_down.JPG",
    "timeout": "https://www.ducksters.com/sports/football/signal_30_second_illegal_touching.JPG",
    "touching": "https://www.ducksters.com/sports/football/signal_30_second_illegal_touching.JPG"
}


class Referee(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["ref", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def referee(self, ctx):
        """ A list of referee signals """
        if not ctx.invoked_subcommand:
            raise discord.ext.commands.CommandError(f"Missing a subcommand. Review '{self.bot.command_prefix}help {ctx.command.qualified_name}' to view subcommands.")

        scmd = ctx.invoked_subcommand

        try:
            await ctx.send(
                embed=build_embed(
                    title=f"Signal: {str(scmd).split(' ')[1].title()}",
                    description=f"Variations: {scmd.help}",
                    image=signals[str(scmd).split(' ')[1]]
                )
            )
        except KeyError:
            await ctx.send(
                embed=build_embed(
                    title=f"Signal: {str(scmd).split(' ')[1].title()}",
                    description=f"Variations: {scmd.help}"
                )
            )

    @referee.command(aliases=["untimed", ])
    async def ready(self, ctx):
        """
        Ready for play
        *Untimed down
        """
        pass

    @referee.command()
    async def start(self, ctx):
        """
        Start the clock
        """
        pass

    @referee.command()
    async def stop(self, ctx):
        """
        Stop the clock
        """
        pass

    @referee.command(aliases=["to", "tv", ])
    async def timeout(self, ctx):
        """
        TV/radio timeout
        """
        pass

    @referee.command(aliases=["td", "fieldgoal", "fg", ])
    async def touchdown(self, ctx):
        """
        Touchdown
        Field Goal
        """
        pass

    @referee.command()
    async def safety(self, ctx):
        """
        Safety
        """
        pass

    @referee.command(aliases=["dead", "touchback"])
    async def deadball(self, ctx):
        """
        Dead-ball foul
        Touchback
        """
        pass

    @referee.command()
    async def first(self, ctx):
        """
        First down
        """
        pass

    @referee.command(aliases=["loss", ])
    async def lossofdown(self, ctx):
        """
        Loss of down
        """
        pass

    @referee.command(aliases=["nogood", "declined"])
    async def incomplete(self, ctx):
        """
        Incomplete pass
        Unsuccessful try or field goal
        Penalty decliend
        Coin toss option deferred
        """
        pass

    @referee.command()
    async def end(self, ctx):
        """
        End of period
        """
        pass

    @referee.command()
    async def sideline(self, ctx):
        """
        Sideline warning
        """
        pass

    @referee.command()
    async def touching(self, ctx):
        """
        Illegal touching
        """
        pass

    @referee.command()
    async def offside(self, ctx):
        """
        Offside
        """
        pass

    @referee.command(aliases=["encroachment", "formation", ])
    async def falsestart(self, ctx):
        """
        False start
        Encroachment
        Illegal formation
        """
        pass

    @referee.command(aliases=["shift", ])
    async def motion(self, ctx):
        """
        Illegal motion
        Illegal shift
        """
        pass

    @referee.command()
    async def delay(self, ctx):
        """
        Delay of game
        """
        pass

    @referee.command()
    async def substitution(self, ctx):
        """
        Substitution infraction
        """
        pass

    @referee.command()
    async def equipment(self, ctx):
        """
        Equipment violation
        """
        pass

    @referee.command()
    async def targeting(self, ctx):
        """
        Targeting
        """
        pass

    @referee.command()
    async def horsecollar(self, ctx):
        """
        Horse-collar
        """
        pass

    @referee.command(aliases=["unsportsman", ])
    async def unsportsmanlike(self, ctx):
        """
        Unsportsmanlike conduct
        """
        pass

    @referee.command(aliases=["roughingkicker", ])
    async def runningkicker(self, ctx):
        """
        Running into or roughing the kicker or holder
        """
        pass

    @referee.command(aliases=["kicking", ])
    async def batting(self, ctx):
        """
        Illegal batting/kicking
        """
        pass

    @referee.command()
    async def roughingpasser(self, ctx):
        """
        Roughing the passer
        """
        pass

    @referee.command()
    async def illegalpass(self, ctx):
        """
        Illegal Pass
        Illegal forward handing
        """
        pass

    @referee.command()
    async def grounding(self, ctx):
        """
        Intentional grounding
        """
        pass

    @referee.command()
    async def ineligible(self, ctx):
        """
        Ineligible downfield on pass
        """
        pass

    @referee.command()
    async def personalfoul(self, ctx):
        """
        Personal foul
        """
        pass

    @referee.command()
    async def clipping(self, ctx):
        """
        Clipping
        """
        pass

    @referee.command()
    async def illegalblock(self, ctx):
        """
        Block below the waist
        Illegal block
        """
        pass

    @referee.command()
    async def chopblock(self, ctx):
        """
        Chop block
        """
        pass

    @referee.command()
    async def holding(self, ctx):
        """
        Holding
        Obstructing
        Illegal use of the hands or arms
        """
        pass

    @referee.command(aliases=["back", ])
    async def blockinback(self, ctx):
        """
        Illegal block in the back
        """
        pass

    @referee.command()
    async def facemask(self, ctx):
        """
        Grasping of the face mask or helmet opening
        """
        pass

    @referee.command()
    async def tripping(self, ctx):
        """
        Tripping
        """
        pass

    @referee.command(aliases=["dq", ])
    async def disqualification(self, ctx):
        """
        Disqualification
        """
        pass

    @referee.command(aliass=["pi", "dpi", "opi"])
    async def passinterference(self, ctx):
        """
        Pass interference
        """
        pass


def setup(bot):
    bot.add_cog(Referee(bot))

# print("### Referee Command loaded! ###")

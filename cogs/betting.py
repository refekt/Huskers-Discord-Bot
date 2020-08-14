import typing

import discord
from discord.ext import commands

from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE
from utils.consts import CURRENCY_NAME
from utils.consts import ROLE_ADMIN_PROD, ROLE_ADMIN_TEST
from utils.mysql import process_MySQL, sqlUpdateCurrency, sqlSetCurrency, sqlCheckCurrencyInit, sqlRetrieveUserCurrency


def full_author(context: typing.Union[discord.ext.commands.Context, discord.Member]):
    if type(context) == discord.ext.commands.Context:
        return f"{context.author.name.lower()}#{context.author.discriminator}"
    elif type(context) == discord.Member:
        return f"{context.name.lower()}#{context.discriminator}"


def check_author_initialized(context: typing.Union[discord.ext.commands.Context, discord.Member]):
    author_init = process_MySQL(
        fetch="all",
        query=sqlCheckCurrencyInit
    )

    try:
        if len(author_init) > 0:
            search = [author for author in author_init if author["username"] == full_author(context)]

            if len(search):
                return True
            else:
                return False
        else:
            return False
    except TypeError:
        return False


class BetCommands(commands.Cog, name="Betting Commands"):
    # @commands.group()
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    # async def bet(self, ctx):
    #     """ Allows users to place bets for Husker games."""
    #
    # @bet.command(aliases=["a", ])
    # async def all(self, ctx, *, team=None):
    #     """Show all the bets for the current or provided opponent."""
    #
    # @bet.command(aliases=["win", "w", ])
    # async def winners(self, ctx, *, team):
    #     """Show the winners for the current or provided opponent."""
    #
    # @bet.command(aliases=["lb", ])
    # async def leaderboard(self, ctx):
    #     """Shows the leaderboard for the season."""
    #
    # @bet.command(aliases=["s", ])
    # async def show(self, ctx, *, team=None):
    #     """Shows the current or provided opponent placed bet(s)."""
    #
    # @bet.command(aliases=["line", "l", ])
    # async def lines(self, ctx, *, team=None):
    #     """Shows the current or provided opponent lines."""
    #
    # @bet.command(hidden=True)
    # @commands.has_any_role(606301197426753536, 440639061191950336, 443805741111836693)
    # async def scores(self, ctx, score, oppo_score, *, team):
    #     """ Update the database """

    @commands.group(aliases=["b"])
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def bet(self, ctx):
        if ctx.subcommand_passed:
            return None
        else:
            raise AttributeError(f"A subcommand must be used. Review $help.")

    @bet.command()
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def create(self, ctx):
        pass

    @commands.group(aliases=["m", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def money(self, ctx):
        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A subcommand must be used. Review $help.")

    @money.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def new(self, ctx):
        if check_author_initialized(ctx):
            raise AttributeError(f"🔔🔔🔔 SHAME {ctx.author.mention} 🔔🔔🔔! You cannot initialize more than once!")

        starter_money = 100

        try:
            process_MySQL(
                query=sqlSetCurrency,
                values=(full_author(ctx), starter_money)
            )
        except:
            pass

        await ctx.send(f"Congratulations {ctx.author.mention}! You now have {starter_money} {CURRENCY_NAME}. Use it wisely!")

    @money.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def give(self, ctx, user: discord.Member, value: int):
        if not user:
            raise AttributeError("You must specific who this is going to!")

        if not value:
            raise AttributeError("You must specific how much to give!")

        if not check_author_initialized(user):
            raise AttributeError(f"{user.mention} has not initialized their account! This is completed by submitting the following command: `$money new`]")

        process_MySQL(
            query=sqlUpdateCurrency,
            values=(value, full_author(user))
        )

        await ctx.send(f"You have granted {user.mention} {value} {CURRENCY_NAME}!")

    @money.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def balance(self, ctx, user: discord.Member = None):
        if check_author_initialized(ctx):
            balance = process_MySQL(
                fetch="all",
                query=sqlRetrieveUserCurrency
            )
        else:
            raise AttributeError("Unable to find user! Establish a balance wiht `$money new`.")

        if balance is None:
            raise AttributeError("Unable to find user!")

        if user:
            bal = [username for username in balance if username["username"] == full_author(user)]
            await ctx.send(f"{user.mention}'s balance is {bal[0]['balance']} {CURRENCY_NAME}.")
        else:
            bal = [username for username in balance if username["username"] == full_author(ctx)]
            await ctx.send(f"{ctx.author.mention}'s balance is {bal[0]['balance']} {CURRENCY_NAME}.")


def setup(bot):
    bot.add_cog(BetCommands(bot))

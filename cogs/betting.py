import typing

import discord
import random
from discord.ext import commands

from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE
from utils.consts import CURRENCY_NAME
from utils.consts import ROLE_ADMIN_PROD, ROLE_ADMIN_TEST
from utils.mysql import process_MySQL, sqlUpdateCurrency, sqlSetCurrency, sqlCheckCurrencyInit, sqlRetrieveUserCurrency


class BetCommands(commands.Cog, name="Betting Commands"):
    def check_author_initialized(self, user: typing.Union[discord.ext.commands.Context, discord.Member]):
        author_init = process_MySQL(
            fetch="all",
            query=sqlCheckCurrencyInit
        )

        try:
            if len(author_init) > 0:
                search = [author for author in author_init if author["username"] == self.full_author(user)]

                if len(search):
                    return True
                else:
                    return False
            else:
                return False
        except TypeError:
            return False

    def check_balance(self, user: typing.Union[discord.ext.commands.Context, discord.Member]):
        if self.check_author_initialized(user):
            balance = process_MySQL(
                fetch="all",
                query=sqlRetrieveUserCurrency
            )
        else:
            raise AttributeError("Unable to find user! Establish a balance with `$money new`.")

        if balance is None:
            raise AttributeError("Unable to find user!")

        for bal in balance:
            if bal["username"] == self.full_author(user):
                return bal["balance"]

        raise AttributeError("Unable to find user!")

    def full_author(self, user: typing.Union[discord.ext.commands.Context, discord.Member]):
        if type(user) == discord.ext.commands.Context:
            return f"{user.author.name.lower()}#{user.author.discriminator}"
        elif type(user) == discord.Member:
            return f"{user.name.lower()}#{user.discriminator}"

    @commands.command(aliases=["rps", ])
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def rockpaperscissors(self, ctx, choice: str):
        """ Play Rock Paper Scissors for 5 server currency. Choices are 'rock', 'paper', or 'scissors' """
        if self.check_balance(ctx) <= 0:
            raise AttributeError(f"You do not have enough {CURRENCY_NAME} to play the game.")

        options = ["rock", "paper", "scissors"]

        def validate_choice():
            return choice.lower().strip() in options

        def award_currency():
            process_MySQL(
                query=sqlUpdateCurrency,
                values=(5, self.full_author(ctx))
            )

        def deduct_currency():
            process_MySQL(
                query=sqlUpdateCurrency,
                values=(-5, self.full_author(ctx))
            )

        if not validate_choice():
            raise AttributeError(f"You can only pick Rock, Paper, or Scissors. Your option was: {choice}.")

        throw = random.choice(options)

        if choice.lower() == throw:
            return await ctx.send(f"Draw! Computer also threw {throw}. No {CURRENCY_NAME} change.")
        else:
            win_string = f"Win! You threw [ {choice} ] and the computer threw [ {throw} ]. You have been awarded 5 {CURRENCY_NAME}."
            lose_string = f"Lose! You threw [ {choice} ] and the computer threw [ {throw} ]. You have been deducted 5 {CURRENCY_NAME}."

            if choice.lower() == options[0]:
                if throw == options[1]:
                    award_currency()
                    return await ctx.send(win_string)
                else:
                    deduct_currency()
                    return await ctx.send(lose_string)
            elif choice.lower() == options[1]:
                if throw == options[2]:
                    award_currency()
                    return await ctx.send(win_string)
                else:
                    deduct_currency()
                    return await ctx.send(lose_string)
            elif choice.lower() == options[2]:
                if throw == options[0]:
                    award_currency()
                    return await ctx.send(win_string)
                else:
                    deduct_currency()
                    return await ctx.send(lose_string)

    @commands.group(aliases=["m", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def money(self, ctx):
        """ Husker server currency """
        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A subcommand must be used. Review $help.")

    @money.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def new(self, ctx):
        """ Establish a wallet for server currency """
        if self.check_author_initialized(ctx):
            raise AttributeError(f"🔔🔔🔔 SHAME {ctx.author.mention} 🔔🔔🔔! You cannot initialize more than once!")

        starter_money = 100

        try:
            process_MySQL(
                query=sqlSetCurrency,
                values=(self.full_author(ctx), starter_money)
            )
        except:
            pass

        await ctx.send(f"Congratulations {ctx.author.mention}! You now have {starter_money} {CURRENCY_NAME}. Use it wisely!")

    @money.command(hidden=True)
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def grant(self, ctx, user: discord.Member, value: int):
        """ Admin command. Give user server currency """
        if not user:
            raise AttributeError("You must specific who this is going to!")

        if not value:
            raise AttributeError("You must specific how much to give!")

        if not self.check_author_initialized(user):
            raise AttributeError(f"{user.mention} has not initialized their account! This is completed by submitting the following command: `$money new`]")

        process_MySQL(
            query=sqlUpdateCurrency,
            values=(value, self.full_author(user))
        )

        await ctx.send(f"You have granted {user.mention} {value} {CURRENCY_NAME}!")

    @money.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def balance(self, ctx, user: discord.Member = None):
        """ Show current balance of server currency """
        balance = self.check_balance(ctx)

        if user:
            await ctx.send(f"{user.mention}'s balance is {balance} {CURRENCY_NAME}.")
        else:
            await ctx.send(f"{ctx.author.mention}'s balance is {balance} {CURRENCY_NAME}.")

    @money.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def give(self, ctx, user: discord.Member, value: int):
        """ Give some of your server currency to another member """
        if not user:
            raise AttributeError("You must specific who this is going to!")

        if not value:
            raise AttributeError("You must specific how much to give!")

        if self.check_author_initialized(user=ctx) and self.check_author_initialized(user=user):
            balance = self.check_balance(user=ctx.message.author)

            if type(balance) == AttributeError:
                await ctx.send(balance)
            elif balance >= value:
                process_MySQL(
                    query=sqlUpdateCurrency,
                    values=(-value, self.full_author(ctx.author))
                )

                process_MySQL(
                    query=sqlUpdateCurrency,
                    values=(value, self.full_author(user))
                )

                await ctx.send(f"You have sent {value} {CURRENCY_NAME} to {self.full_author(user)}!")
            else:
                raise AttributeError(f"You do not have {value} {CURRENCY_NAME} to send! Please review `$money balance` and try again.")
        else:
            raise AttributeError("This user has not established a wallet. Please have them set one up with `$money new`.")


def setup(bot):
    bot.add_cog(BetCommands(bot))

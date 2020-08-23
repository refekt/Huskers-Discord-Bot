import random
import re
import typing

import discord
from discord.ext import commands

from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE
from utils.consts import CURRENCY_NAME
from utils.consts import ROLE_ADMIN_PROD, ROLE_ADMIN_TEST
from utils.embed import build_embed
from utils.mysql import process_MySQL, sqlUpdateCurrency, sqlSetCurrency, sqlCheckCurrencyInit, sqlRetrieveCurrencyLeaderboard, sqlRetrieveCurrencyUser


class BetCommands(commands.Cog, name="Betting Commands"):
    def result_string(self, result, who: discord.Member, amount, **kwargs):
        output = ""

        if result == "win":
            output = "Win! "
            self.adjust_currency(who, amount)
        elif result == "lose":
            output = "Loser! "
            self.adjust_currency(who, amount)

        if kwargs["game"] == "rps":
            output += f"You threw [ {kwargs['mbr_throw']} ] and the computer threw [ {kwargs['cpu_throw']} ]. "
        elif kwargs["game"] == "rlt":
            output += f"The computer spun the wheel and it landed on [ {kwargs['wheel_spin']} ]."

        output += f" You have been {'awarded' if result == 'win' else 'deducted'} [ {abs(amount)} ] {CURRENCY_NAME}. Your current balance is [ {self.get_balance(who):,} ]."

        return output

    def check_author_initialized(self, user: discord.Member):
        author_init = process_MySQL(
            fetch="one",
            query=sqlCheckCurrencyInit,
            values=user.id
        )

        err = AttributeError(f"You have not established a wallet yet. This is accomplished by completing `$money new`.")

        if author_init is None:
            return False

        try:
            if author_init["init"] == 1:
                return True
            elif author_init["init"] == 0:
                return False
            else:
                return False
        except:
            return False

    def check_balance(self, user: discord.Member, amount_check):
        if self.check_author_initialized(user):
            balance = process_MySQL(
                fetch="one",
                query=sqlRetrieveCurrencyUser,
                values=user.id
            )
        else:
            raise AttributeError("Unable to find user! Establish a balance with `$money new`.")

        if balance is None:
            raise AttributeError("Unable to find user!")

        if balance["balance"] >= amount_check:
            return True
        else:
            raise AttributeError(f"You do not have enough {CURRENCY_NAME} to play the game.")

    def get_balance(self, user: discord.Member):
        if self.check_author_initialized(user):
            balance = process_MySQL(
                fetch="one",
                query=sqlRetrieveCurrencyUser,
                values=user.id
            )
        else:
            raise AttributeError("Unable to find user! Establish a balance with `$money new`.")

        if balance is None:
            raise AttributeError("Unable to find user!")

        return balance["balance"]

    def validate_bet_amount_syntax(self, bet_amount: typing.Union[int, str]):
        err = AttributeError(f"You submitted an incorrect amount to bet.")
        if type(bet_amount) == int and bet_amount > 0:
            return True
        elif type(bet_amount) == str:
            if bet_amount == "max":
                return True
            elif "%" in bet_amount:
                return True
            else:
                raise err
        else:
            return err

    def full_author(self, user: discord.Member):
        return f"{user.name.lower()}#{user.discriminator}"

    def adjust_currency(self, who: discord.Member, value):
        process_MySQL(
            query=sqlUpdateCurrency,
            values=(value, self.full_author(who))
        )

    def initiate_user(self, ctx, value):
        process_MySQL(
            query=sqlSetCurrency,
            values=(self.full_author(ctx.message.author), value, ctx.message.author.id,)
        )

    @commands.command(aliases=["rlt", ])
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def roulette(self, ctx, bet_amount: typing.Union[int, str], bet: typing.Union[int, str]):
        """ Win or lose some server currency playing roulette
        $roulette 10 red -- Bet a color
        $roulette 10 25 -- Bet a specific number (225% bonus)
        $roulette 10 1:17 -- Bet a specific number range (scaling bonus)
        $roulette 10 red1:36 -- Bet a color and number range
        """
        if bet_amount is None or bet is None:
            raise AttributeError(f"You must select a bet!")

        self.validate_bet_amount_syntax(bet_amount)

        if bet_amount == "max":
            bet_amount = self.get_balance(ctx.message.author)
        elif type(bet_amount) == str and "%" in bet_amount:
            perc = float(bet_amount.strip("%")) / 100
            bet_amount = int(self.get_balance(ctx.message.author) * perc)

        if bet_amount <= 0:
            raise AttributeError(f"You do not have enough server currency to place this bet.")

        def roll_color():
            return random.choice(colors)

        def validate_bet_range(bet_range):
            check_one = 1 <= bet_range[0] <= 36
            check_two = 1 <= bet_range[1] <= 36
            if check_one and check_two and bet_range[0] < bet_range[1]:
                return True
            else:
                raise AttributeError(f"Error in your bet format. Please review `$help roulette` for more information.")

        def convert_bet_range():
            raw_range = bet.split(bet_range_char)
            raw_map = map(int, raw_range)
            return list(raw_map)

        win = False
        result = None
        bet_range_char = ":"
        colors = ["red", "black"]

        if type(bet) == str:
            color_re = r"(red|black)"
            bet_color = re.search(color_re, bet.lower())
            if bet_color is not None:
                bet_color = str(bet_color[0])

            if bet_range_char in bet and bet_color:  # Color and range
                result = roll_color()
                if bet_color == result:
                    bet = bet[len(bet_color):]
                    bet_range = convert_bet_range()
                    validate_bet_range(bet_range)
                    result = random.randint(1, 36)
                    if bet_range[0] <= result <= bet_range[1]:
                        win = True
                        result = f"{bet_color} and {str(result)}"
                        bet_amount = int(((72 / (max(bet_range) - min(bet_range) + 1)) - 1) * (bet_amount))

            elif bet_range_char in bet and bet_color is None:  # Range
                bet_range = convert_bet_range()
                validate_bet_range(bet_range)
                result = random.randint(1, 36)

                if bet_range[0] <= result <= bet_range[1]:
                    win = True
                    bet_amount = int(((36 / (max(bet_range) - min(bet_range) + 1)) - 1) * bet_amount)
            else:  # Color
                if bet.lower() in colors:
                    result = roll_color()
                    if result == bet.lower():
                        win = True
                else:
                    raise AttributeError(f"You can only place a bet for {[color for color in colors]}. Try again!")

        elif type(bet) == int:  # One number

            if 1 <= bet <= 36:
                result = random.randint(1, 36)
                if result == bet:
                    bet_amount = int(bet_amount * 36) - bet_amount
                    win = True
            else:
                raise AttributeError(f"You can only play a number from 1 to 36. Try again!")

        if win:
            return await ctx.send(self.result_string(result="win", who=ctx.message.author, amount=bet_amount, game="rlt", wheel_spin=result))
        else:
            return await ctx.send(self.result_string(result="lose", who=ctx.message.author, amount=-bet_amount, game="rlt", wheel_spin=result))

    @commands.command(aliases=["rps", ])
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def rockpaperscissors(self, ctx, choice: str):
        """ Play Rock Paper Scissors for 5 server currency. Choices are 'rock', 'paper', or 'scissors' """
        self.check_balance(ctx.message.author, 5)

        options = ["rock", "paper", "scissors"]

        def validate_choice():
            return choice.lower().strip() in options

        if not validate_choice():
            raise AttributeError(f"You can only pick Rock, Paper, or Scissors. Your option was: {choice}.")

        throw = random.choice(options)

        if choice.lower() == throw:
            return await ctx.send(f"Draw! Computer also threw {throw}. No {CURRENCY_NAME} change.")
        else:
            win = False

            if choice.lower() == options[0]:
                if throw == options[2]:
                    win = True
            elif choice.lower() == options[1]:
                if throw == options[0]:
                    win = True
            elif choice.lower() == options[2]:
                if throw == options[1]:
                    win = True

            if win:
                return await ctx.send(self.result_string(result="win", who=ctx.message.author, amount=5, game="rps", mbr_throw=choice, cpu_throw=throw))
            else:
                return await ctx.send(self.result_string(result="lose", who=ctx.message.author, amount=-5, game="rps", mbr_throw=choice, cpu_throw=throw))

    @commands.group(aliases=["m", ])
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
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
        if not self.check_author_initialized(ctx.message.author):
            starter_money = 100
            self.initiate_user(ctx, starter_money)
            await ctx.send(f"Congratulations {ctx.message.author.mention}! You now have {starter_money} {CURRENCY_NAME}. Use it wisely!")
        else:
            return await ctx.send(f"{ctx.message.author.mention}: 🔔🔔🔔 SHAME, SHAME! You can only initialize your account once! 🔔🔔🔔")

    @money.command(hidden=True)
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def grant(self, ctx, user: discord.Member, value: int):
        """ Admin command. Give user server currency """
        if not user:
            raise AttributeError("You must specify who this is going to!")

        if not value:
            raise AttributeError("You must specific how much to give!")

        self.check_author_initialized(user)
        self.adjust_currency(user, value)

        await ctx.send(f"{ctx.message.author.mention} has granted {user.mention} {value} {CURRENCY_NAME}!")

    @money.command()
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def pity(self, ctx):
        if not self.check_author_initialized(ctx.message.author):
            return

        balance = self.get_balance(ctx.message.author)

        if balance == 0:
            pitty_value = 100
            self.adjust_currency(ctx.message.author, pitty_value)
            return await ctx.send(content=f"Pity on you. You have been awarded [ {pitty_value} ] {CURRENCY_NAME}. Try not to suck so much next time!")
        else:
            return await ctx.send(f"You cannot use this command when your {CURRENCY_NAME} balance is greater than 0.")

    @money.command(aliases=["bal", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def balance(self, ctx, user: discord.Member = None):
        """ Show current balance of server currency for self or another member """
        if user:
            balance = self.get_balance(user)
            await ctx.send(f"{user.mention}'s balance is {balance:,} {CURRENCY_NAME}.")
        else:
            balance = self.get_balance(ctx.message.author)
            await ctx.send(f"{ctx.message.author.mention}'s balance is {balance:,} {CURRENCY_NAME}.")

    @money.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def give(self, ctx, user: discord.Member, value: int):
        """ Give some of your server currency to another member """
        if not user:
            raise AttributeError("You must specific who this is going to!")

        if not value:
            raise AttributeError("You must specific how much to give!")

        self.check_author_initialized(ctx.message.author)
        self.check_author_initialized(user)
        balance = self.get_balance(user=ctx.message.author)

        if value < 0:
            return await ctx.send("You can't give negative money you dummy.")
        elif value == 0:
            return await ctx.send("It makes no sense to give someone 0 of something, smh.")

        if balance >= value:
            self.adjust_currency(ctx.message.author, -value)
            self.adjust_currency(user, value)
            return await ctx.send(f"You have sent {value} {CURRENCY_NAME} to {user.mention}!")
        else:
            raise AttributeError(f"You do not have {value} {CURRENCY_NAME} to send! Please review `$money balance` and try again.")

    @money.command(aliases=["lb", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def leaderboard(self, ctx):
        leaderboard = process_MySQL(
            query=sqlRetrieveCurrencyLeaderboard,
            fetch="all"
        )

        from utils.client import client
        lb = ""
        for index, person in enumerate(leaderboard):
            member = client.get_user(id=int(person["user_id"]))
            if member is not None:
                lb += f"#{index + 1} {member.display_name} - {person['balance']:,} {CURRENCY_NAME}\n"

        await ctx.send(
            embed=build_embed(
                title=f"Husker Discord Currency Leaderboard",
                fields=[
                    ["Leaderboard", lb]
                ]
            )
        )


def setup(bot):
    bot.add_cog(BetCommands(bot))

import random
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
        
        output += f"You have been {'awarded' if result == 'win' else 'deducted'} {abs(amount)} {CURRENCY_NAME}. Your current balance is [ {self.get_balance(who):,} ]."

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

    def validate_bet_amount(self, bet_amount):
        if bet_amount > 0:
            return True
        else:
            return False

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
    async def roulette(self, ctx, bet_amount: int, bet: typing.Union[int, str]):
        """ Win or lose some server currency playing roulette
        $roulette 10 red -- Bet a color
        $roulette 10 25 -- Bet a specific number (225% bonus)
        $roulette 10 1:17 -- Bet a specific number range (scaling bonus)
        """
        if bet_amount is None or bet is None:
            raise AttributeError(f"You must select a bet!")

        if not self.validate_bet_amount(bet_amount):
            raise AttributeError(f"You must place a proper bet. Try again.")

        self.check_balance(ctx.message.author, bet_amount) # Checks if initialized and has the proper balance

        def validate_color_bet():
            return bet.lower() in colors

        def validate_number_bet():
            return 1 <= bet <= 36

        def validate_number_range_bet(range):
            check_one = 1 <= range[0] <= 36
            check_two = 1 <= range[1] <= 36
            if check_one and check_two and range[0] < range[1]:
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

        if type(bet) == str:
            if bet_range_char in bet:
                try:
                    range = convert_bet_range()
                    validate_number_range_bet(range)

                    result = random.randint(1, 36)
                    if range[0] <= result <= range[1]:
                        win = True
                        bet_amount = int(((36 / (max(range) - min(range) + 1)) - 1) * bet_amount)
                except:
                    raise AttributeError(f"Error in your bet format. Please review `$help roulette` for more information.")
            else:
                colors = ["red", "black"]

                if validate_color_bet():
                    result = random.choice(colors)
                    if result == bet.lower():
                        win = True
                else:
                    raise AttributeError(f"You can only place a bet for Red or Black. Try again!")

        elif type(bet) == int:

            if validate_number_bet():
                result = random.randint(1, 36)
                if result == bet:
                    bet_amount = int(bet_amount * 36) - bet_amount
                    win = True
            else:
                raise AttributeError(f"You can only play a number from 1 to 36. Try again!")

        if win:
            # self.adjust_currency(ctx.message.author, bet_amount)
            return await ctx.send(self.result_string(result="win", who=ctx.message.author, amount=bet_amount, game="rlt", wheel_spin=result))
        else:
            # self.adjust_currency(ctx.message.author, -bet_amount)
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
            pitty_value = 25
            self.adjust_currency(ctx.message.author, pitty_value)
            return await ctx.send(content=f"Pity on you. You have been awarded {pitty_value} {CURRENCY_NAME}. Try not to suck so much next time!")
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

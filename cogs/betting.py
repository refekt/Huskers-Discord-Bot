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
from utils.mysql import sqlInsertCustomLinesBets, sqlRetrieveOneCustomLinesKeywords, sqlRetrieveAllCustomLinesKeywords
from utils.mysql import sqlRetrieveAllOpenCustomLines, sqlRetrieveOneOpenCustomLine, sqlInsertCustomLines, sqlUpdateCustomLinesBets, sqlUpdateCustomLinesResult

PITY_CAP = 10
RLT_FLOOR = 1
RLT_CEILING = 36
BET_RANGE_CHAR = ":"


class BetCommands(commands.Cog, name="Betting Commands"):

    def pity_value(self):
        return 15000

    def result_string(self, result, who: discord.Member, amount, **kwargs):
        output = ""

        if result == "win":
            output = "Win! "
        elif result == "lose":
            output = "Loser! "

        self.adjust_currency(who, amount)

        if kwargs["game"] == "rps":
            output += f"You threw [ {kwargs['mbr_throw']} ] and the computer threw [ {kwargs['cpu_throw']} ]. "
        elif kwargs["game"] == "rlt":
            output += f"The computer spun the wheel and it landed on [ {kwargs['wheel_spin']} ]. You chose [ {kwargs['bet']} ]."
        elif kwargs["game"] == "arlt":
            output += f"The computer ran [ {kwargs['cycles']} ] cycles. You chose [ {kwargs['bet']} ] and you won [ {kwargs['wins']} ] of those cycles. Your winnings are [ {amount:,} ]."

        output += f" You have been {'awarded' if result == 'win' else 'deducted'} [ {abs(amount):,} ] {CURRENCY_NAME}. Your current balance is [ {self.get_balance(who):,} ]."

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
            return False
            # raise AttributeError(f"You do not have enough {CURRENCY_NAME} to play the game.")

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
        # No zero or negative numbers.
        if type(bet_amount) == int and bet_amount > 0:
            return True
        elif type(bet_amount) == str:
            # Maximum server currency
            if bet_amount == "max":
                return True
            # Percent of users current server currency balance
            elif "%" in bet_amount:
                return True
            else:
                raise False
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

    def find_color_string(self, bet):
        color_re = r"(red|black)"
        bet_color = re.findall(color_re, bet.lower())

        if len(bet_color) == 1:
            return str(bet_color[0])
        elif len(bet_color) > 1:
            raise AttributeError('You can put at most one color in your bet!')
        else:
            return None

    def convert_bet_range(self, bet):
        raw_range = bet.split(BET_RANGE_CHAR)
        return list(map(int, raw_range))

    def validate_bet_range(self, bet_range):
        check_one = RLT_FLOOR <= bet_range[0] <= RLT_CEILING
        check_two = RLT_FLOOR <= bet_range[1] <= RLT_CEILING
        if check_one and check_two and bet_range[0] < bet_range[1]:
            return True
        else:
            raise False

    def roll_single_int(self):
        return random.randint(RLT_FLOOR, RLT_CEILING)

    def roll_range_int(self):
        pass

    def roll_red_or_black(self):
        colors = ["red", "black"]
        return random.choice(colors)

    def roll_red_or_black_and_range_int(self):
        pass

    # def correct_bet(self, bet):
    #     try:
    #         iter(bet)
    #         bet_joined = "".join(bet)
    #         return bet_joined
    #     except:
    #         pass

    def adjust_bet_amount(self, bet_amount, current_balance):
        if type(bet_amount) == str and bet_amount == "max":
            return current_balance
        elif type(bet_amount) == str and "%" in bet_amount:
            perc = float(bet_amount.strip("%")) / 100
            return int(current_balance * perc)
        elif type(bet_amount) == int:
            return int(bet_amount)

    def generate_win_amount(self, bet_amount: int, bet_range=None, **kwargs):
        if kwargs["method"] == "color_and_range":
            return int((((RLT_CEILING * 2) / (max(bet_range) - min(bet_range) + 1)) - 1) * bet_amount)
        elif kwargs["method"] == "range":
            return int(((RLT_CEILING / (max(bet_range) - min(bet_range) + 1)) - 1) * bet_amount)
        elif kwargs["method"] == "number":
            return int(bet_amount * RLT_CEILING) - bet_amount

    @commands.command(aliases=["rlt", ])
    async def roulette(self, ctx, bet_amount: typing.Union[int, str], *, bet: typing.Union[int, str]):
        """ Win or lose some server currency playing roulette
        $roulette 10 red -- Bet a color
        $roulette 10 25 -- Bet a specific number (225% bonus)
        $roulette 10 1:17 -- Bet a specific number range (scaling bonus)
        $roulette 10 red1:36 -- Bet a color and number range (scaling bonus)
        """
        if bet_amount is None or bet is None:
            raise AttributeError(f"You must select a bet!")

        current_balance = self.get_balance(ctx.message.author)

        if not self.validate_bet_amount_syntax(bet_amount):
            raise AttributeError(f"You submitted an incorrect amount to bet.")

        bet_amount = self.adjust_bet_amount(bet_amount, current_balance)

        if not self.check_balance(ctx.message.author, bet_amount):
            raise AttributeError(f"You do not have enough {CURRENCY_NAME} to play the game.")

        if bet_amount <= 0:
            raise AttributeError(f"You cannot make bets for amounts that are 0 or lower {CURRENCY_NAME}.")

        edit_msg = await ctx.send("Loading...")

        bet_amount = self.adjust_bet_amount(bet_amount, current_balance)
        win = False
        result = None
        colors = ["red", "black"]
        bet_color = None

        if type(bet) == str:
            bet_color = self.find_color_string(bet)

            if BET_RANGE_CHAR in bet and bet_color:  # Color and range
                result = self.roll_red_or_black()

                if bet_color == result:
                    bet = bet[len(bet_color):]
                    bet_range = self.convert_bet_range(bet)

                    if not self.validate_bet_range(bet_range):
                        raise AttributeError(f"Error in your bet format. Please review `$help roulette` for more information.")

                    result = self.roll_single_int()

                    if bet_range[0] <= result <= bet_range[1]:
                        bet_amount = self.generate_win_amount(bet_amount, bet_range, method="color_and_range")
                        win = True
                        result = f"{bet_color} and {str(result)}"

            elif BET_RANGE_CHAR in bet and bet_color is None:  # Range only
                bet_range = self.convert_bet_range(bet)

                if not self.validate_bet_range(bet_range):
                    raise AttributeError(f"Error in your bet format. Please review `$help roulette` for more information.")

                result = self.roll_single_int()

                if bet_range[0] <= result <= bet_range[1]:
                    bet_amount = self.generate_win_amount(bet_amount, bet_range, method="range")
                    win = True

            else:  # Color only
                if bet.lower() in colors:
                    result = self.roll_red_or_black()

                    if result == bet.lower():
                        win = True
                else:
                    raise AttributeError(f"You can only place a bet for {[color for color in colors]}. Try again!")

        elif type(bet) == int:  # One number only

            if RLT_FLOOR <= bet <= RLT_CEILING:
                result = self.roll_single_int()

                if result == bet:
                    bet_amount = self.generate_win_amount(bet_amount, method="number")
                    win = True
            else:
                raise AttributeError(f"You can only play a number from {RLT_FLOOR} to {RLT_CEILING}. Try again!")

        if win:
            await edit_msg.edit(content=self.result_string(result="win", who=ctx.message.author, amount=bet_amount, game="rlt", wheel_spin=result,
                                                           bet=bet if not BET_RANGE_CHAR in bet and bet_color else f"{bet_color} {bet}"))
        else:
            await edit_msg.edit(content=self.result_string(result="lose", who=ctx.message.author, amount=-bet_amount, game="rlt", wheel_spin=result, bet=bet))

    @commands.command(aliases=["arlt", ])
    # @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    @commands.cooldown(rate=2, per=86400, type=discord.ext.commands.BucketType.user)
    async def autoroulette(self, ctx, goal: int, bet_multiplier: float, cycles: int = 10000, strat: str = '2*x+z'):
        """
        Spin the roulette wheel automatically up to 10,000 times!

        LIMIT 2 PER 24 HOURS!

        :param goal: Your target ending balance.
        :param bet_multiplier: The percentage of your current balance you'd like to bet on each spin.
        :param cycles: How many spins?
        :param strat: Voodoo magic. I don't understand it.
        """
        balance = self.get_balance(ctx.message.author)

        if balance > goal:
            raise AttributeError(f"You must be more than your current balance of [ {balance:,} ].")

        pities = 0
        pity_cap = 10

        edit_msg = await ctx.send(f"Spinning the wheel [ {cycles:,} ] times in an attempt to get to [ {goal:,} ] {CURRENCY_NAME} from [ {balance:,} ]! You have [ {pity_cap} ] pities available. Here "
                                  f"we go!")

        max_cycles = 10000
        cycles = min(cycles, max_cycles)
        i = -1
        pity_money = self.pity_value()
        ran = .9
        bet2 = 0
        losses_current = 0
        losses_max = 0
        wins_current = -1
        wins_max = 0
        balance_max = balance

        strat = strat.replace('x', 'bet2')
        strat = strat.replace('z', 'bet1')

        self.adjust_currency(ctx.message.author, -balance)

        while i < cycles and balance < goal:
            # await edit_msg.edit(content=edit_msg.content + " New wheel spin! ")
            if ran >= 0.5:
                wins_current += 1
                wins_max = max(wins_current, wins_max)
                losses_current = 0
                balance = balance + bet2
                bet1 = max(int(bet_multiplier * balance), 1)
                bet2 = min(bet1, balance)
                balance_max = max(balance, balance_max)
            else:
                losses_current += 1
                losses_max = max(losses_current, losses_max)
                wins_current = 0
                balance = balance - bet2

                if balance <= 0:
                    if pities >= pity_cap:
                        raise AttributeError("Pity is on cooldown! Auto Roulette has stopped.")
                    else:
                        await edit_msg.edit(content=edit_msg.content + f" Pity #{pities + 1}! ")

                        pities += 1
                        balance = pity_money
                        await self.pity_no_text(ctx)
                        self.adjust_currency(ctx.message.author, -balance)
                        bet1 = max(int(bet_multiplier * balance), 1)
                        bet2 = 0
                bet2 = int(min(max(eval(strat), 1), balance))
            ran = random.random()
            i += 1

        self.adjust_currency(ctx.message.author, balance)

        await edit_msg.edit(content=edit_msg.content + f" Done! New balance is [ {self.get_balance(ctx.message.author):,} ] {CURRENCY_NAME}. The wheel spun [ {i:,} ] times to get there!")

    # return the fun data/message after the loop is completed

    # if num_cycles > 10:
    #     raise AttributeError(f"You can only run 10 cycles!")
    #
    # if bet_amount is None or bet is None:
    #     raise AttributeError(f"You must select a bet!")
    #
    # current_balance = self.get_balance(ctx.message.author)
    #
    # if not self.validate_bet_amount_syntax(bet_amount):
    #     raise AttributeError(f"You submitted an incorrect amount to bet.")
    #
    # bet_amount = self.adjust_bet_amount(bet_amount, current_balance)
    #
    # if not self.check_balance(ctx.message.author, bet_amount):
    #     raise AttributeError(f"You do not have enough {CURRENCY_NAME} to play the game.")
    #
    # if bet_amount <= 0:
    #     raise AttributeError(f"You cannot make bets for amounts that are 0 or lower {CURRENCY_NAME}.")
    #
    # iterations = 0
    # while iterations < num_cycles:
    #     await self.roulette(ctx, bet_amount=bet_amount, bet=bet)
    #     iterations += 1

    @commands.command(aliases=["rps", ])
    async def rockpaperscissors(self, ctx, bet_amount: typing.Union[int, str], choice: str):
        """ Play Rock Paper Scissors for server currency. Choices are 'rock', 'paper', or 'scissors' """
        self.validate_bet_amount_syntax(bet_amount)

        if bet_amount == "max":
            bet_amount = self.get_balance(ctx.message.author)
        elif type(bet_amount) == str and "%" in bet_amount:
            perc = float(bet_amount.strip("%")) / 100
            bet_amount = int(self.get_balance(ctx.message.author) * perc)

        if bet_amount <= 0:
            raise AttributeError(f"You cannot make bets for amounts that are 0 or lower {CURRENCY_NAME}.")

        if not self.check_balance(ctx.author, bet_amount):
            raise AttributeError(f"You do not have enough {CURRENCY_NAME} to play the game.")

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
                return await ctx.send(self.result_string(result="win", who=ctx.message.author, amount=bet_amount, game="rps", mbr_throw=choice, cpu_throw=throw))
            else:
                return await ctx.send(self.result_string(result="lose", who=ctx.message.author, amount=-bet_amount, game="rps", mbr_throw=choice, cpu_throw=throw))

    @commands.group(aliases=["m", ])
    async def money(self, ctx):
        """ Husker server currency """
        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A sub command must be used. Review $help.")

    @money.command()
    async def new(self, ctx):
        """ Establish a wallet for server currency """
        if not self.check_author_initialized(ctx.message.author):
            starter_money = 100
            self.initiate_user(ctx, starter_money)
            await ctx.send(f"Congratulations {ctx.message.author.mention}! You now have [ {starter_money:,} ] {CURRENCY_NAME}. Use it wisely!")
        else:
            return await ctx.send(f"{ctx.message.author.mention}: 🔔🔔🔔 SHAME, SHAME! You can only initialize your account once! 🔔🔔🔔")

    @money.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def grant(self, ctx, user: discord.Member, value: int):
        """ Admin command. Give user server currency """
        if not user:
            raise AttributeError("You must specify who this is going to!")

        if not value:
            raise AttributeError("You must specific how much to give!")

        self.check_author_initialized(user)
        self.adjust_currency(user, value)

        await ctx.send(f"{ctx.message.author.mention} has granted {user.mention} [ {value:,} ] {CURRENCY_NAME}!")

    @money.command()
    @commands.cooldown(rate=PITY_CAP, per=86400, type=discord.ext.commands.BucketType.user)
    async def pity(self, ctx):
        if not self.check_author_initialized(ctx.message.author):
            return

        balance = self.get_balance(ctx.message.author)

        if balance == 0:
            self.adjust_currency(ctx.message.author, self.pity_value())
            return await ctx.send(content=f"Pity on you. You have been awarded [ {self.pity_value():,} ] {CURRENCY_NAME}. Try not to suck so much next time!")
        else:
            return await ctx.send(f"You cannot use this command when your {CURRENCY_NAME} balance is greater than 0.")

    @money.command()
    async def pity_no_text(self, ctx):
        if not self.check_author_initialized(ctx.message.author):
            return

        balance = self.get_balance(ctx.message.author)

        if balance == 0:
            self.adjust_currency(ctx.message.author, self.pity_value())
            return
            # return await ctx.send(content=f"Pity on you. You have been awarded [ {self.pity_value():,} ] {CURRENCY_NAME}. Try not to suck so much next time!")
        else:
            # return await ctx.send(f"You cannot use this command when your {CURRENCY_NAME} balance is greater than 0.")
            return

    @money.command(aliases=["bal", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def balance(self, ctx, user: discord.Member = None):
        """ Show current balance of server currency for self or another member """
        if user:
            balance = self.get_balance(user)
            await ctx.send(f"{user.mention}'s balance is [ {balance:,} ] {CURRENCY_NAME}.")
        else:
            balance = self.get_balance(ctx.message.author)
            await ctx.send(f"{ctx.message.author.mention}'s balance is [ {balance:,} ] {CURRENCY_NAME}.")

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
            return await ctx.send(f"You have sent [ {value:,} ] {CURRENCY_NAME} to {user.mention}!")
        else:
            raise AttributeError(f"You do not have [ {value:,} ] {CURRENCY_NAME} to send! Please review `$money balance` and try again.")

    @money.command()
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def grantall(self, ctx, value: int):
        users = process_MySQL(
            query=sqlRetrieveCurrencyLeaderboard,
            fetch="all"
        )

        for user in users:
            usr = ctx.guild.get_member(user["user_id"])
            if usr:
                self.adjust_currency(usr, value)

        return await ctx.send(f"Everyone with a server currency wallet has received [ {value:,} ] {CURRENCY_NAME}!")

    @money.command(aliases=["lb", ])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def leaderboard(self, ctx):

        leaderboard = process_MySQL(
            query=sqlRetrieveCurrencyLeaderboard,
            fetch="all"
        )

        lb = ""
        for index, person in enumerate(leaderboard):
            if index > 9:
                break

            member = person["username"][:13]
            spacer = "." * (35 - len(f"`🥇: {member}{person['balance']:,}`"))

            if member is not None:
                if index == 0:
                    lb += f"`🥇: {member}{spacer}{person['balance']:,}`\n"
                elif index == 1:
                    lb += f"`🥈: {member}{spacer}{person['balance']:,}`\n"
                elif index == 2:
                    lb += f"`🥉: {member}{spacer}{person['balance']:,}`\n"
                else:
                    lb += f"`🏅: {member}{spacer}{person['balance']:,}`\n"

        await ctx.send(
            embed=build_embed(
                title=f"Husker Discord Currency Leaderboard",
                fields=[
                    [f"Top 10 {CURRENCY_NAME} Leaderboard", lb]
                ]
            )
        )

    def retrieve_one_bet_keyword_custom_line(self, ctx: discord.ext.commands.Context, keyword):
        try:
            return process_MySQL(
                query=sqlRetrieveOneCustomLinesKeywords,
                values=(keyword, ctx.message.author.id),
                fetch="one"
            )
        except:
            return None

    def retrieve_all_bet_keyword_custom_line(self, ctx: discord.ext.commands.Context, keyword):
        try:
            return process_MySQL(
                query=sqlRetrieveAllCustomLinesKeywords,
                values=keyword,
                fetch="all"
            )
        except:
            return None

    def validate_keyword_bet(self, keyword: str):
        """
        Retrieves all bets from `custom_lines` database. Returns True if `keyword` exists else returns False

        :param keyword:
        :return:
        """
        try:
            check = process_MySQL(
                query=sqlRetrieveOneOpenCustomLine,
                values=keyword,
                fetch="all"
            )
        except ConnectionError:
            return False
        else:
            if check is None:
                return False

            for ch in check:
                if keyword in ch.values():
                    return True

    async def set_bet(self, ctx: discord.ext.commands.Context, which: str, keyword: str, value):
        """
        Create or update a bet `custom_lines_bets` database entry "for" or "against" and server currency value.

        :param ctx:
        :param which: Either "for" or "against".
        :param keyword: The `keyword` bet (line).
        :param value: The amount of server currency the user is betting.
        :return:
        """
        try:
            # Prevent spamming bets by betting max balance, and then using pity.
            if value <= self.pity_value():
                raise AttributeError(f"Bets must be more than [ {self.pity_value():,} ] {CURRENCY_NAME}. Try again.")

            #
            keyword_bet = self.retrieve_one_bet_keyword_custom_line(ctx, keyword)

            # Validate the `keyword` bet (line) exists or has not already resolved.
            if not self.validate_keyword_bet(keyword):
                raise AttributeError(f"The bet [ {keyword} ] was not found in the bet register. Try again.")

            # Validate the betting syntax.
            if not self.validate_bet_amount_syntax(value):
                raise AttributeError(f"The bet amount of [ {value:,} ] was not correct. Try again.")

            # Validate the user has enough server currency to place this bet.
            if not self.check_balance(ctx.message.author, value):
                raise AttributeError(f"You do not have the [ {value:,} ] [ {CURRENCY_NAME} ] to place this bet. Try again.")

            # Bets are additive.
            if keyword_bet is None:
                total_bet_value = value

                if which == "for":
                    process_MySQL(
                        query=sqlInsertCustomLinesBets,
                        values=(ctx.message.author.id, keyword, 1, 0, total_bet_value)
                    )
                elif which == "against":
                    process_MySQL(
                        query=sqlInsertCustomLinesBets,
                        values=(ctx.message.author.id, keyword, 0, 1, total_bet_value)
                    )
            else:
                total_bet_value = keyword_bet["value"] + value

                if which == "for":
                    process_MySQL(
                        query=sqlUpdateCustomLinesBets,
                        values=(1, 0, total_bet_value, ctx.message.author.id, keyword)
                    )
                elif which == "against":
                    process_MySQL(
                        query=sqlUpdateCustomLinesBets,
                        values=(0, 1, total_bet_value, ctx.message.author.id, keyword)
                    )

            keyword_bet = self.retrieve_one_bet_keyword_custom_line(ctx, keyword)

            self.adjust_currency(ctx.message.author, -value)

        except ConnectionError:
            raise AttributeError(f"A MySQL query error occurred!")
        else:
            author = ctx.guild.get_member(keyword_bet["orig_author"])

            await ctx.send(embed=build_embed(
                title="Custom Bet",
                description=f"{ctx.message.author.mention}'s bet [ {which} ] the [ {keyword} ] bet!",
                fields=[
                    ["Author", author],
                    ["Keyword", keyword],
                    ["Description", str(keyword_bet['description']).capitalize()],
                    ["Total Bet Amount", f"{keyword_bet['value']:,}"],
                    ["Most Recent Bet Amount", f"{value:,}"]
                ]
            )
            )

    def retrieve_open_custom_lines(self, keyword=None):
        """
        Returns all or one bet (line).

        :param keyword:
        :return:
        """
        if keyword is None:
            return process_MySQL(
                query=sqlRetrieveAllOpenCustomLines,
                fetch="all"
            )
        else:
            return process_MySQL(
                query=sqlRetrieveOneOpenCustomLine,
                values=keyword,
                fetch="one"
            )

    def convert_author(self, ctx: discord.ext.commands.Context, author):
        # Attempt to created a `discord.Member` object.
        author = ctx.guild.get_member(author)
        # Create a `str` if attempt fails.
        if author is None:
            return "Unknown Author"
        else:
            return author

    @commands.group()
    @commands.guild_only()
    async def bet(self, ctx):
        """Create custom bets for server currency"""
        # if ctx.channel.type == discord.channel.ChannelType.private:
        #     raise AttributeError("You cannot use bet commands in DMs.")

        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A sub command must be used. Review $help.")

    @bet.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def create(self, ctx, keyword: str, *, description: str):
        """
        Create a custom bet (line) for the Discord to place bets against.

        :param ctx:
        :param keyword: A single-word identifier for the bet (line).
        :param description: A detailed description of the bet (line). This should include conditions on "for" and "against" results.
        :return:
        """

        # Prevent errors
        keyword = keyword.replace(" ", "").lower()

        try:
            # Insert into `custom_lines` database.
            process_MySQL(
                query=sqlInsertCustomLines,
                values=(ctx.message.author.id, keyword, description)
            )
        except ConnectionError:
            # Was not able to insert into `custom_lines` database.
            raise AttributeError(f"A MySQL query error occurred!")
        else:
            # Alert the user that the bet (line) was created.
            await ctx.send(embed=build_embed(
                title="Custom Bet",
                description=f"{ctx.message.author.mention}'s bet was successfully created!",
                fields=[
                    ["Author", ctx.message.author.mention],
                    ["Keyword", keyword],
                    ["Description", description]
                ]
            ))

    @bet.command()
    async def show(self, ctx, keyword=None):
        """
        Show the list of open bets (lines) or a specified bet (line).

        :param ctx:
        :param keyword: Optional. Retrieves a bet (line) if provided.
        :return:
        """

        await ctx.message.delete()

        # Show the list of open bets (lines).
        if not keyword:
            # Retrieve all open bets (lines).
            bets = self.retrieve_open_custom_lines()
            bet_fields = []

            # Iterate through all bets (lines).
            for bet in bets:
                # Attempt to created a `discord.Member` object.
                author = self.convert_author(ctx, bet["author"])

                # Append list of members.
                bet_fields.append([
                    f"Keyword: {bet['keyword']}",
                    f"Author: {author.mention if type(author) == discord.Member else author}\n"
                    f"Description: {str(bet['description']).capitalize()}\n"
                ])

            return await ctx.send(embed=build_embed(
                title="All Open Bets",
                fields=bet_fields,
                inline=False
            ))
        else:
            # Retrieve single bet (line).
            bets = self.retrieve_one_bet_keyword_custom_line(ctx, keyword)

            # Raise error if no bet (line) was found.
            if bets is None:
                raise AttributeError(f"No bet found with the keyword [ {keyword} ]. Please try again!")

            # Attempt to created a `discord.Member` object.
            author = self.convert_author(ctx, bets["author"])

            return await ctx.send(embed=build_embed(
                title="All Open Bets",
                fields=[
                    [
                        f"Keyword: {bets['keyword']}",
                        f"Author: {author.mention if type(author) == discord.Member else author}\n"
                        f"Description: {str(bets['description']).capitalize()}\n"
                    ]
                ],
                inline=False
            ))

    @bet.command(aliases=["for", ])
    async def _for(self, ctx, keyword: str, value: int):
        """
        Please a bet for a specified `keyword` bet (line).

        :param ctx:
        :param keyword: The `keyword` of the bet (line) you want to bet against.
        :param value: The amount of server currency you want to place against the `keyword` bet.
        :return:
        """
        await self.set_bet(ctx, "for", keyword.lower(), value)

    @bet.command()
    async def against(self, ctx, keyword: str, value: int):
        """
        Please a bet against a specified `keyword` bet (line).

        :param ctx:
        :param keyword: The `keyword` of the bet (line) you want to bet against.
        :param value: The amount of server currency you want to place against the `keyword` bet.
        :return:
        """
        await self.set_bet(ctx, "against", keyword.lower(), value)

    @bet.command()
    async def resolve(self, ctx, keyword: str, result: str):
        """
        Resolve a bet (line).

        :param ctx:
        :param keyword: The `keyword` for a bet (line).
        :param result: Either "for" or "against".
        :return:
        """
        keyword = keyword.lower()

        original_bet = self.retrieve_open_custom_lines(keyword)

        if original_bet is None:
            raise AttributeError(f"Unable to find any [ {keyword} ] bet or it has already been resolved! Try again.")

        result = result.lower()

        if not (result == "for" or result == "against"):
            raise AttributeError(f"The result must be `for` or `against`. Not [ {result} ]. Try again!")

        author = ctx.guild.get_member(original_bet["author"])

        if not original_bet["author"] == ctx.message.author.id:
            raise AttributeError(f"You cannot update a bet you did not create! The original author for [ {keyword} ] is [ {author.mention} ]. ")

        try:

            process_MySQL(
                query=sqlUpdateCustomLinesResult,
                values=(result, keyword)
            )

            keyword_bet_uers = self.retrieve_all_bet_keyword_custom_line(ctx, keyword)

            winners = []
            losers = []

            for user in keyword_bet_uers:
                member = ctx.guild.get_member(user["author"])

                if user["_for"] == 1 and result == "for" or user["against"] == 1 and result == "against":
                    try:
                        self.adjust_currency(member, user["value"] * 2)
                        winners.append(member.mention)
                    except:
                        winners.append(user["author"])
                else:
                    try:
                        # self.adjust_currency(member, -(user["value"] * 2))
                        losers.append(member.mention)
                    except:
                        losers.append(user["author"])

        except ConnectionError:
            raise AttributeError(f"A MySQL query error occurred!")
        else:
            return await ctx.send(embed=build_embed(
                title=f"[ {author}'s ] [ {keyword} ] bet has been resolved!",
                description=keyword_bet_uers[0]["description"],
                fields=[
                    ["Result", result],
                    ["Winners", winners],
                    ["Losers", losers]
                ],
                inline=True
            ))


def setup(bot):
    bot.add_cog(BetCommands(bot))

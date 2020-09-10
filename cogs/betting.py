import random
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
from utils.mysql import sqlRetreiveCustomLinesForAgainst, sqlInsertCustomLinesBets, sqlRetrieveCustomLinesKeywords
from utils.mysql import sqlRetrieveCustomLines, sqlRetrieveCustomLinesKeyword, sqlInsertCustomLines, sqlUpdateCustomLinesBets, sqlUpdateCustomLinesResult


class BetCommands(commands.Cog, name="Betting Commands"):

    def pity_value(self):
        return 15000

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
    async def roulette(self, ctx, bet_amount: typing.Union[int, str], *, bet: typing.Union[int, str]):
        """ Win or lose some server currency playing roulette
        $roulette 10 red -- Bet a color
        $roulette 10 25 -- Bet a specific number (225% bonus)
        $roulette 10 1:17 -- Bet a specific number range (scaling bonus)
        $roulette 10 red1:36 -- Bet a color and number range (scaling bonus)
        """
        if bet_amount is None or bet is None:
            raise AttributeError(f"You must select a bet!")

        # checks to see if the bet is iterable, if so, it joins it into a string
        try:
            iter(bet)
            bet = ''.join(bet)
        except:
            pass

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
            bet_color = re.findall(color_re, bet.lower())

            if len(bet_color) == 1:
                bet_color = str(bet_color[0])
            elif len(bet_color) > 1:
                return await ctx.send('You can put at most one color in your bet!')
            else:
                bet_color = None

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
                        bet_amount = int(((72 / (max(bet_range) - min(bet_range) + 1)) - 1) * bet_amount)

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
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def money(self, ctx):
        """ Husker server currency """
        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A sub command must be used. Review $help.")

    @money.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def new(self, ctx):
        """ Establish a wallet for server currency """
        if not self.check_author_initialized(ctx.message.author):
            starter_money = 100
            self.initiate_user(ctx, starter_money)
            await ctx.send(f"Congratulations {ctx.message.author.mention}! You now have [ {starter_money:,} ] {CURRENCY_NAME}. Use it wisely!")
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

        await ctx.send(f"{ctx.message.author.mention} has granted {user.mention} [ {value:,} ] {CURRENCY_NAME}!")

    @money.command()
    # @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def pity(self, ctx):
        if not self.check_author_initialized(ctx.message.author):
            return

        balance = self.get_balance(ctx.message.author)

        if balance == 0:
            self.adjust_currency(ctx.message.author, self.pity_value())
            return await ctx.send(content=f"Pity on you. You have been awarded [ {self.pity_value():,} ] {CURRENCY_NAME}. Try not to suck so much next time!")
        else:
            return await ctx.send(f"You cannot use this command when your {CURRENCY_NAME} balance is greater than 0.")

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
    async def giveall(self, ctx, value: int):
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

            member = ctx.guild.get_member(person["user_id"])

            if member is not None:
                name_balance = f"{person['balance']:,}" + "@" + str(member.name)
                # spacer = "." * (
                #         50 - len(name_balance)
                # )
                spacer = " --- "
                lb += f"#{index + 1}: {member.mention if type(member) == discord.Member else member}{spacer}{person['balance']:,}\n"

        await ctx.send(
            embed=build_embed(
                title=f"Husker Discord Currency Leaderboard",
                fields=[
                    [f"Top 10 {CURRENCY_NAME} Leaderboard", lb]
                ]
            )
        )

    @money.command(hidden=True)
    async def buy(self, ctx):
        roles = ctx.guild.roles
        buyable_roles = [747241238692102155]

        if roles is None:
            return

        vals = []
        for index, role in enumerate(roles):
            if role.id in buyable_roles:
                vals.append(f"{index + 1}: {role}")

        embed = build_embed(
            title=f"Spend your {CURRENCY_NAME}!",
            fields=[
                ["Roles", vals]
            ]
        )

        buy_msg = await ctx.send(embed=embed)
        role_cost = 10000
        emojis = "1️⃣"

        try:
            await buy_msg.add_reaction(emojis)
        except discord.Forbidden:
            raise AttributeError(f"You do not have permission to add reactions.")
        except discord.NotFound:
            raise AttributeError(f"The emoji is not found.")
        except discord.InvalidArgument:
            raise AttributeError(f"The emoji parameter is invalid.")
        except discord.HTTPException:
            raise AttributeError(f"Reaction failed to add.")

        from utils.client import client

        def can_buy(r: discord.Reaction, u: discord.Member):
            if not u.bot:
                if self.get_balance(u) < role_cost:
                    raise AttributeError(f"You do not have {role_cost} to buy the role!")
                else:
                    return r.emoji == emojis

        try:
            reaction, user = await client.wait_for("reaction_add", check=can_buy)
            print(reaction, user)
            await user.add_roles(buyable_roles[0], reason=f"Bought with {role_cost} {CURRENCY_NAME}")
        except TimeoutError:
            return
        else:
            pass

    def check_bet_exists(self, ctx: discord.ext.commands.Context, keyword: str):
        try:
            previous_bets = process_MySQL(
                query=sqlRetreiveCustomLinesForAgainst,
                values=keyword,
                fetch="all"
            )
        except ConnectionError:
            raise AttributeError(f"A MySQL query error occurred!")
        else:
            if previous_bets is None:
                return False

            for bet in previous_bets:
                if bet["author"] == ctx.message.author.id:
                    if bet["_for"] == 1 or bet["against"] == 1:
                        return True

            return False

    def check_bet_resolved(self, keyword: str):
        try:
            previous_bets = process_MySQL(
                query=sqlRetrieveCustomLinesKeyword,
                values=keyword,
                fetch="one"
            )
        except ConnectionError:
            raise AttributeError(f"A MySQL query error occurred!")
        else:
            if previous_bets["result"] == "tbd":
                return False
            else:
                return True

    async def set_bet(self, ctx: discord.ext.commands.Context, which: str, keyword: str, value):
        try:
            if value <= self.pity_value():
                raise AttributeError(f"Bets must be more than [ {self.pity_value()} ] {CURRENCY_NAME}. Try again.")

            keyword_bet = self.keyword_bet(keyword)

            if not self.validate_keyword_bet(keyword):
                raise AttributeError(f"The bet [ {keyword} ] was not found. Try again.")

            if not self.validate_bet_amount_syntax(value):
                raise AttributeError(f"The bet amount of [ {value:,} ] was not correct. Try again.")

            if not self.check_balance(ctx.message.author, value):
                raise AttributeError(f"You do not have the [ {value:,} ] [ {CURRENCY_NAME} ] to place this bet. Try again.")

            if keyword_bet is None:
                total_bet_value = value
            else:
                total_bet_value = keyword_bet["value"] + value

            previous_bet_exists = self.check_bet_exists(ctx, keyword)

            if previous_bet_exists:
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
            else:
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

            self.adjust_currency(ctx.message.author, -value)

            keyword_bet = self.keyword_bet(keyword)

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

    def keyword_bet(self, keyword):
        return process_MySQL(
            query=sqlRetrieveCustomLinesKeywords,
            values=keyword,
            fetch="one"
        )

    def validate_keyword_bet(self, keyword: str):
        try:
            check = process_MySQL(
                query=sqlRetrieveCustomLinesKeyword,
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

    @commands.group()
    async def bet(self, ctx):
        """Create custom bets for server currency"""
        if ctx.channel.type == discord.channel.ChannelType.private:
            raise AttributeError("You cannot use bet commands in DMs.")

        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A sub command must be used. Review $help.")

    @bet.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def create(self, ctx, keyword: str, *, description: str):
        """Creates a custom bet.
        Key = single word descriptor
        Description = full description of the bet"""

        keyword = keyword.replace(" ", "").lower()

        try:
            process_MySQL(
                query=sqlInsertCustomLines,
                values=(ctx.message.author.id, keyword, description)
            )
        except ConnectionError:
            raise AttributeError(f"A MySQL query error occurred!")
        else:
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
        """Show all bets or a specific bet
        $bet show
        $bet show <keyword>"""
        if not keyword:
            bets = process_MySQL(
                query=sqlRetrieveCustomLines,
                fetch="all"
            )
        else:
            bets = process_MySQL(
                query=sqlRetrieveCustomLinesKeyword,
                fetch="one",
                values=keyword
            )

        if type(bets) == list:
            bet_fields = []

            for bet in bets:
                author = ctx.guild.get_member(bet["author"])
                if author is None:
                    author = "Unknown Author"

                bet_fields.append([
                    bet["keyword"],
                    f"Author: {author.mention if type(author) == discord.Member else author}\n"
                    f"Description: {str(bet['description']).capitalize()}\n"
                ])

            await ctx.send(embed=build_embed(
                title="All Open Bets",
                fields=bet_fields,
                inline=False
            ))
        elif type(bets) == dict:
            author = ctx.guild.get_member(bets["author"])
            if author is None:
                author = "Unknown Author"

            await ctx.send(embed=build_embed(
                title="All Open Bets",
                fields=[
                    [
                        bets["keyword"],
                        f"Author: {author.mention if type(author) == discord.Member else author}\n"
                        f"Description: {str(bets['description']).capitalize()}\n"
                    ]
                ],
                inline=False
            ))
        elif bets is None:
            return await ctx.send(f"No bet found with the keyword [ {keyword} ]. Please try again!")

    @bet.command(aliases=["for", ])
    async def _for(self, ctx, keyword: str, value: int):
        """Place a bet in favor for bet
        $bet for <keyword> <bet amount>"""
        await self.set_bet(ctx, "for", keyword.lower(), value)

    @bet.command()
    async def against(self, ctx, keyword: str, value: int):
        """Place a bet against for bet
        $bet against <keyword> <bet amount>"""
        await self.set_bet(ctx, "against", keyword.lower(), value)

    @bet.command()
    async def resolve(self, ctx, keyword: str, result: str):
        """Resolve a bet
        $resolve <keyword> <for|against>"""
        keyword = keyword.lower()

        if not self.check_bet_exists(ctx, keyword):
            raise AttributeError(f"Unable to find [ {keyword} ] bet! Try again.")

        if self.check_bet_resolved(keyword):
            raise AttributeError(f"The [ {keyword} ] bet has already been resolved!")

        result = result.lower()

        if not (result == "for" or result == "against"):
            raise AttributeError(f"The result must be `for` or `against`. Not [ {result} ]. Try again!")

        try:
            keyword_bet = self.keyword_bet(keyword)

            author = ctx.guild.get_member(keyword_bet["orig_author"])

            if not keyword_bet["orig_author"] == ctx.message.author.id:
                raise AttributeError(f"You cannot update a bet you did not create! The original author for [ {keyword} ] is [ {author.mention} ]. ")

            process_MySQL(
                query=sqlUpdateCustomLinesResult,
                values=(result, keyword)
            )

            keyword_bet = self.keyword_bet(keyword)

            bet_users = process_MySQL(
                query=sqlRetreiveCustomLinesForAgainst,
                fetch="all",
                values=keyword
            )

            winners = []
            losers = []

            for user in bet_users:
                member = ctx.guild.get_member(user["author"])

                if user["_for"] == 1 and result == "for" or user["against"] == 1 and result == "against":
                    try:
                        self.adjust_currency(member, user["value"] * 2)
                        winners.append(member.mention)
                    except:
                        winners.append(user["author"])
                else:
                    try:
                        self.adjust_currency(member, -(user["value"] * 2))
                        losers.append(member.mention)
                    except:
                        losers.append(user["author"])

        except ConnectionError:
            raise AttributeError(f"A MySQL query error occurred!")
        else:
            await ctx.send(embed=build_embed(
                title=f"[ {author}'s ] [ {keyword_bet['keyword']} ] bet has been resolved!",
                description=keyword_bet["description"],
                fields=[
                    ["Result", keyword_bet["result"]],
                    ["Winners", winners],
                    ["Losers", losers]
                ],
                inline=True
            ))


def setup(bot):
    bot.add_cog(BetCommands(bot))

from discord.ext import commands
import discord
import random
from utils.embed import build_embed

card_val_lower = 1
card_val_upper = 11
hand_val_max = 21
deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"] * 4
ace_value = 11
face_card_value = 10
orig = deck.copy()
card_char = "🃏"


class NoGamePlayingError(Exception):
    pass


class HandBustedError(Exception):
    pass


class BlackjackHand:
    def __init__(self, user: discord.Member):
        self.user = user
        self.init = False
        self.count = 0
        self.hand = []
        self.total = 0
        self.busted = False

    def restart(self):
        self.user = None
        self.init = False
        self.count = 0
        self.hand = []
        self.total = 0
        self.busted = False

    def deal_hand(self, player):
        self.init = True
        if player == "cpu":
            self.hit_me(player)
            self.hand.append(card_char)
        else:
            [self.hit_me(player) for _ in range(2)]

    def hit_me(self, player):
        if player == "cpu" and card_char in self.hand:
            self.hand.remove(card_char)

        dealt = random.randint(0, len(deck) - 1)
        self.count += 1
        self.hand.append(deck[dealt])
        del deck[dealt]

    def sort_hand(self, x):
        if type(x) == int:
            return x
        elif type(x) == str:
            if x == "J":
                return 11
            elif x == "Q":
                return 12
            elif x == "K":
                return 13
            elif x == "A":
                return 14
            elif x == card_char:
                return 99

    def tally_hand(self):
        self.total = 0
        self.hand.sort(key=self.sort_hand)
        for card in self.hand:
            if type(card) == int:
                self.total += card
            elif type(str):
                if card == "A":
                    if self.total + ace_value > hand_val_max:
                        self.total += 1
                    else:
                        self.total += ace_value
                elif card == card_char:
                    continue
                else:
                    self.total += face_card_value


class BlackjackCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = None
        self.dealer = None
        self.message_string = ""
        self.move_history = ""
        self.current_message = None
        self.convert_hand = {
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟",
            "J": ":regional_indicator_j:",
            "Q": ":regional_indicator_q:",
            "K": ":regional_indicator_k:",
            "A": ":regional_indicator_a:",
            "🃏": "🃏"
        }

    def initiate_hand(self, user: discord.Member):
        self.player = BlackjackHand(user)
        self.dealer = BlackjackHand(self.bot.user)

    def check_if_playing(self):
        if self.player is None:
            raise NoGamePlayingError(f"No game is currently being played!")
        else:
            return True

    def restart_game(self):
        self.player = None
        self.dealer = None
        self.message_string = ""
        self.move_history = ""
        self.current_message = None

    def current_move_string(self, result=""):
        embed = build_embed(
            title="Bot Frost Blackjack",
            description=f"{self.player.user.mention}'s hand",
            fields=[
                ["Player Hand:", " ".join(self.convert_hand[elem] for elem in self.player.hand) + f"  ({self.player.total})"],
                ["Dealer Hand:", " ".join(self.convert_hand[elem] for elem in self.dealer.hand) + f"  ({self.dealer.total})"],
                ["History", self.move_history]
            ],
            inline=False
        )
        if result:
            embed.insert_field_at(0, name="Game Result", value=result, inline=False)
        return embed

    async def check_bust(self, ctx, hand):
        if hand.total > hand_val_max:
            await self.current_message.delete()
            hand.busted = True
            if hand.user.bot:
                self.current_message = await ctx.send(embed=self.current_move_string(result="Winner! Dealer bust."))
                self.restart_game()
            else:
                self.current_message = await ctx.send(embed=self.current_move_string(result="Loser! User bust."))
                self.restart_game()

    def set_current_message(self, msg: discord.Message):
        self.current_message = msg

    def add_history(self, who: str, what: str = "", result: str = ""):
        _nl = "\n"
        if result:
            self.move_history += f"{self.move_history.count(_nl) + 1}: {who}: {result}\n"
        else:
            self.move_history += f"{self.move_history.count(_nl) + 1}: {who} drew {what}. "
            self.move_history += _nl

    @commands.group(aliases=["bj", ])
    async def blackjack(self, ctx):
        pass

    async def cog_after_invoke(self, ctx):
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

        if ctx.subcommand_passed == "hit":
            await self.check_bust(ctx, self.player)

    async def cog_before_invoke(self, ctx):
        if ctx.subcommand_passed is None:
            return

        if ctx.subcommand_passed == "hit":
            self.check_if_playing()
        else:
            return

    @blackjack.command()
    async def deal(self, ctx):
        self.initiate_hand(ctx.message.author)

        self.player.deal_hand("player")
        self.player.tally_hand()

        self.add_history(self.player.user.mention, " ".join([str(elem) for elem in self.player.hand]))

        self.dealer.deal_hand("cpu")
        self.dealer.tally_hand()

        self.add_history(self.dealer.user.mention, " ".join([str(elem) for elem in self.dealer.hand]))

        self.current_message = await ctx.send(embed=self.current_move_string())

    @blackjack.command()
    async def hit(self, ctx):
        self.player.hit_me("player")
        self.player.tally_hand()

        self.add_history(self.player.user.mention, " ".join([str(elem) for elem in self.player.hand]))

        await self.current_message.delete()
        self.current_message = await ctx.send(embed=self.current_move_string())
        await self.check_bust(ctx, self.player)

    @blackjack.command(aliases=["sit", ])
    async def stand(self, ctx):
        while self.dealer.total < 17:
            self.dealer.hit_me("cpu")
            self.dealer.tally_hand()
            self.add_history(self.dealer.user.mention, " ".join([str(elem) for elem in self.dealer.hand]))

        if not self.player.busted:
            if self.dealer.total > hand_val_max:
                await self.current_message.delete()
                self.add_history(self.player.user.mention, result="Winner! Dealer bust.")
                self.current_message = await ctx.send(embed=self.current_move_string(result="Winner! Dealer bust."))
                self.restart_game()
            elif self.player.total > self.dealer.total:
                await self.current_message.delete()
                self.add_history(self.player.user.mention, result="Winner!")
                self.current_message = await ctx.send(embed=self.current_move_string(result="Winner!"))
                self.restart_game()
            elif self.player.total == self.dealer.total:
                await self.current_message.delete()
                self.add_history(self.player.user.mention, result="Draw.")
                self.current_message = await ctx.send(embed=self.current_move_string(result="Draw!"))
                self.restart_game()
            else:
                await self.current_message.delete()
                self.add_history(self.player.user.mention, result="Loser")
                self.current_message = await ctx.send(embed=self.current_move_string(result="Loser!"))
                self.restart_game()

    @blackjack.command()
    async def surrender(self, ctx):
        self.restart_game()
        await self.current_message.delete()
        self.current_message = await ctx.send("Restarted your game!")


def setup(bot):
    bot.add_cog(BlackjackCommands(bot))

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

    def restart(self):
        self.user = None
        self.init = False
        self.count = 0
        self.hand = []
        self.total = 0

    def deal_hand(self, player):
        self.init = True
        if player == "cpu":
            self.hit_me(player)
            self.hand.append(card_char)
        else:
            [self.hit_me(player) for _ in range(2)]
        self.check_bust()

    def hit_me(self, player):
        if player == "cpu" and card_char in self.hand:
            self.hand.remove(card_char)
        dealt = random.randint(0, len(deck) - 1)
        self.count += 1
        self.hand.append(deck[dealt])
        del deck[dealt]
        self.tally_hand()
        self.check_bust()

    def tally_hand(self):
        self.total = 0
        for card in self.hand:
            if type(card) == int:
                self.total += card
            elif type(str):
                if card == "A":
                    if self.total + ace_value > hand_val_max:
                        self.total += 1
                    else:
                        self.total += ace_value
                else:
                    self.total += face_card_value

        self.check_bust()

    def check_bust(self):
        if self.total > hand_val_max:
            raise_str = f"You have lost! Your hand totals {self.total} with the following cards: {self.hand}."
            self.restart()
            raise HandBustedError(raise_str)


class BlackjackCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = None
        self.dealer = None
        self.message_string = ""
        self.current_message = None

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
        self.current_message = None

    def current_move_string(self, result=""):
        convert_hand = {
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
        embed = build_embed(
            title="Bot Frost Blackjack",
            fields=[
                ["Player Hand:", " ".join(convert_hand[elem] for elem in self.player.hand) + f"  ({self.player.total})"],
                ["Dealer Hand:", " ".join(convert_hand[elem] for elem in self.dealer.hand) + f"  ({self.dealer.total})"],
            ],
            inline=False
        )
        if result:
            embed.insert_field_at(0, name="Game Result", value=result, inline=False)
        return embed

    def set_current_message(self, msg: discord.Message):
        self.current_message = msg

    @commands.command()
    async def deal(self, ctx):
        self.initiate_hand(ctx.message.author)

        self.player.deal_hand("player")
        self.player.tally_hand()

        self.dealer.deal_hand("cpu")
        self.dealer.tally_hand()

        self.current_message = await ctx.send(embed=self.current_move_string())

    @commands.command()
    async def hit(self, ctx):
        self.check_if_playing()

        self.player.hit_me("player")

        await self.current_message.delete()
        self.current_message = await ctx.send(embed=self.current_move_string())

    @commands.command(aliases=["sit", ])
    async def stand(self, ctx):
        self.check_if_playing()

        self.dealer.hit_me("cpu")

        if self.player.total > self.dealer.total:
            await self.current_message.delete()
            self.current_message = await ctx.send(embed=self.current_move_string(result="Winner!"))
            self.restart_game()
        elif self.player.total == self.dealer.total:
            await self.current_message.delete()
            self.current_message = await ctx.send(embed=self.current_move_string(result="Draw!"))
            self.restart_game()
        else:
            await self.current_message.delete()
            self.current_message = await ctx.send(embed=self.current_move_string(result="Lower!"))
            self.restart_game()

    @commands.command()
    async def surrender(self, ctx):
        self.check_if_playing()
        self.restart_game()
        await self.current_message.delete()
        self.current_message = await ctx.send("Restarted your game!")


def setup(bot):
    bot.add_cog(BlackjackCommands(bot))

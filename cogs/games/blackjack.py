from discord.ext import commands
import discord
import random

card_val_lower = 1
card_val_upper = 11
hand_val_max = 21

# deck = {
#     "s": [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"],
#     "h": [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"],
#     "d": [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"],
#     "c": [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]
# }

orig = deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"] * 4


class PlayerHand:
    def __init__(self, user: discord.Member):
        self.user = user
        self.count = 0
        self.hand = []
        self.total = 0

    def deal(self):
        i = 0
        while 0 <= i < 2:
            dealt = random.randint(0, len(deck) - 1)
            self.hit()
            self.hand.append(deck[dealt])
            del deck[dealt]
            i += 1

    def hit(self):
        self.count += 1
        for card in self.hand:
            if type(card) == int:
                self.total += card
            else:
                self.total += 11

    def bust(self):
        if self.total > hand_val_max:
            return True
        else:
            return False


class HandDealtError(Exception):
    pass


class BlackjackCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hand = None

    def check_initiated(self, user: discord.Member):
        if self.hand is None:
            self.hand = PlayerHand(user)
        else:
            raise HandDealtError(f"{user.mention} already has an dealt hand!")

    # Deal
    @commands.command()
    async def deal(self, ctx):
        self.check_initiated(ctx.message.author)
        self.hand.deal()

        await ctx.send(f"Hand count: {self.hand.count}\nTotal value: {self.hand.total}\nHand: {self.hand.hand}")

    # Hit

    # Stand

    # Surrender


def setup(bot):
    bot.add_cog(BlackjackCommands(bot))

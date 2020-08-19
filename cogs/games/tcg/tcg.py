from discord.ext import commands
import discord

from utils.mysql import process_MySQL

class Player:
    def __init__(self, user: discord.Member):
        self.name = user.display_name
        self.id = user.id
    
    def get_balance(self):
        get_balance_sql = '''SELECT balance FROM currency WHERE user_id = %s'''
        balance = process_MySQL(query = get_balance_sql, values = (self.id,), fetch = 'one')
        return balance
        
        

class Card:
    pass
    
class TCGCommands(commands.Cog):
    @commands.group()
    async def tcg(self, ctx):
        '''Husker Discord TCG commands'''
        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A subcommand must be used. Review $help.")
            
    @tcg.group()       
    async def shop(self, ctx):
        from utils.client import client
        embed_title = f"Buy a Booster Pack with the command `{client.command_prefix}buy [id]`"
        embed_description = "The available booster packs are below:"
        embed = discord.Embed(title = embed_title, description = embed_description)
        embed.add_field(name = "Shop", value = "Pack ID - Pack Name\ni69420 - 90's Huskers")
        await ctx.send(embed = embed)
                
    @tcg.command()
    async def buy(self, ctx, pack_id: str = None):
        from utils.client import client
        player = Player(ctx.author)
        if pack_id is None:
            await ctx.send(f"You need to include the ID of the pack you'd like to buy, **{ctx.author.display_name}**. You can call `{client.command_prefix}tcg shop` to get the "
                            "list of available packs and their IDs.")
        else:
            await ctx.send(f"1 `standing name` bought for 69 Verduzcoins")
            
    @tcg.command()
    async def sell(self, ctx, card_id: str = None):
        player = Player(ctx.author)
        await ctx.send("You called the sell card command")
    

def setup(bot):
    bot.add_cog(TCGCommands(bot))
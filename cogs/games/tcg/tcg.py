from discord import commands
import discord

from utils.mysql import process_MySQL

class Player:
    def __init__(self, user: discord.Member):
        self.name = user.display_name
        self.id = user.id
    
    def get_balance(self):
        get_balance_sql = '''SELECT balance FROM currency WHERE user_id = %s'''
        balance = process_MySQL(query = get_balance_sql, values = (user.id,), fetch = 'one')
        return balance
        
        

class Card:

class TCGCommands(commands.Cog):
    @commands.group()
    async def tcg(self, ctx):
        '''Husker Discord TCG commands'''
        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A subcommand must be used. Review $help.")
            
    

def setup(bot):
    bot.add_cog(TCGCommands(bot))
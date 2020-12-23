from discord.ext import commands
import discord
import pandas as pd

from utils.mysql import process_MySQL

CREATE_USER_TABLE_SQL = '''CREATE TABLE IF NOT EXISTS tcg_users
                           (
                           id INT NOT NULL AUTO_INCREMENT,
                           discord_id BIGINT NOT NULL,
                           opted_in DATETIME,
                           tokens INT,
                           PRIMARY KEY ( id )
                           )
                        '''
CHECK_PLAYER_EXISTS_SQL = ''' SELECT * FROM tcg_users
                              WHERE discord_id=%s
                          '''
OPT_IN_SQL = '''INSERT INTO tcg_users (discord_id, opted_in, tokens)
                VALUES (%s, NOW(), 0)
             '''
CHECK_DAILY_MESSAGE_SQL = '''SELECT * FROM stats
                             WHERE author = %s
                             AND created_at >= TIMESTAMP(CURDATE())
                          '''
USER_INFO_SQL = '''SELECT * FROM tcg_users
                   WHERE discord_id = %s
                '''
REDUCE_USER_TOKEN_SQL = '''UPDATE tcg_users
                           SET tokens = tokens - 1
                           WHERE discord_id = %s
                        '''
PACK_CARDS_SQL = '''SELECT c.* FROM tcg_card as c
                    JOIN tcg_card_to_pack ctp on c.id=ctp.card_id
                    JOIN tcg_pack p on ctp.pack_id=p.id
                    WHERE p.name=%s
                 '''

class Player:
    def __init__(self, user: discord.Member):
        self.name = user.display_name
        self.id = user.id

    def get_balance(self):
        get_balance_sql = '''SELECT balance FROM currency WHERE user_id = %s'''
        balance = process_MySQL(query=get_balance_sql, values=(self.id,), fetch='one')
        return balance


class Card:
    pass


class TCGCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def tcg(self, ctx):
        '''Husker Discord TCG commands'''
        if ctx.subcommand_passed:
            return
        else:
            raise AttributeError(f"A subcommand must be used. Review $help.")
    
    @tcg.command()
    async def opt_in(self, ctx):
        user_id = ctx.author.id
        create_table_sql = process_MySQL(query=CREATE_USER_TABLE_SQL)
        check_exists_response = process_MySQL(query=CHECK_PLAYER_EXISTS_SQL, values=(user_id,), fetch='all')
        if check_exists_response is not None:
            await ctx.send("You've already opted in!")
        else:
            process_MySQL(query=OPT_IN_SQL, values=(user_id,))
            
    @tcg.group()
    async def shop(self, ctx):
        embed_title = f"Buy a Booster Pack with the command `{self.bot.command_prefix}buy [id]`"
        embed_description = "The available booster packs are below:"
        embed = discord.Embed(title=embed_title, description=embed_description)
        embed.add_field(name="Shop", value="Pack ID - Pack Name\ni69420 - 90's Huskers")
        await ctx.send(embed=embed)

    @tcg.command()
    async def buy(self, ctx, pack_name: str = None):
        player = Player(ctx.author)
        if pack_name is None:
            await ctx.send(f"You need to include the name of the pack you'd like to buy, **{ctx.author.display_name}**. You can call `{self.bot.command_prefix}tcg shop` to get the "
                           "list of available packs and their IDs.")
        else:
            #await ctx.send(f"1 `standing name` bought for 69 Verduzcoins")
            user_info = process_MySQL(query=USER_INFO_SQL, values=(ctx.author.id,), fetch='one')
            print(user_info)
            if user_info['tokens']==0:
                await ctx.send("Sorry, you don't have any tokens to spend on a pack at the moment")
            elif user_info['tokens']>0:
                await ctx.send(f"Purchasing a {pack_name} pack... (Not really, just a test)")
                process_MySQL(query=REDUCE_USER_TOKEN_SQL, values=(ctx.author.id,))
                pack_cards = process_MySQL(query=PACK_CARDS_SQL,values=(pack_name,),fetch='all')
                pack_cards = pd.DataFrame(pack_cards)
                choices = pack_cards['id'].sample(n=2, weights=pack_cards['weight'])
                print(choices)
                
                

    @tcg.command()
    async def sell(self, ctx, card_id: str = None):
        player = Player(ctx.author)
        await ctx.send("You called the sell card command")

    @commands.Cog.listener()
    async def on_message(self, message):
        check_daily_message_response = process_MySQL(query=CHECK_DAILY_MESSAGE_SQL, values=(message.author.name+'#'+message.author.discriminator,), fetch='one')
        if check_daily_message_response is None:
            pass
        else:
            pass
    
def setup(bot):
    bot.add_cog(TCGCommands(bot))

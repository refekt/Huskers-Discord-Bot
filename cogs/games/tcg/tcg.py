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
                    AND p.enabled = 1
                 '''
AVAILABLE_PACKS_SQL = '''SELECT * from tcg_pack
                         WHERE enabled=1
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
        available_packs = process_MySQL(query=AVAILABLE_PACKS_SQL, fetch='all')
        if available_packs is None:
            await ctx.send("There are currently no packs available!")
            return
        embed_title = f"Buy a Booster Pack with the command `{self.bot.command_prefix}buy [name]`"
        embed_description = "The available booster packs are below:\n\n**name: description**\n"
        shop_string = ''
        for i, p in enumerate(available_packs):
            if i+1<=len(available_packs):
                shop_string += f"{p['name']}: {p['description']}\n"
            elif i+1==len(available_packs):
                shop_string += f"{p['name']}: {p['description']}"
        embed_description += shop_string
        embed = discord.Embed(title=embed_title, description=embed_description)
        await ctx.send(embed=embed)

    @tcg.command()
    async def buy(self, ctx, pack_name: str = None):
        player = Player(ctx.author)
        if pack_name is None:
            await ctx.send(f"You need to include the name of the pack you'd like to buy, **{ctx.author.display_name}**. You can call `{self.bot.command_prefix}tcg shop` to get the "
                           "list of available packs and their IDs.")
        else:
            user_info = process_MySQL(query=USER_INFO_SQL, values=(ctx.author.id,), fetch='one')
            print(user_info)
            if user_info['tokens']==0:
                await ctx.send("Sorry, you don't have any tokens to spend on a pack at the moment")
            elif user_info['tokens']>0:
                pack_cards = process_MySQL(query=PACK_CARDS_SQL,values=(pack_name,),fetch='all')
                if pack_cards is None:
                    await ctx.send(f"There is no pack named {pack_name}, pick something real")
                else:
                    sent_message = await ctx.send(f"Purchasing a {pack_name} pack...")
                    process_MySQL(query=REDUCE_USER_TOKEN_SQL, values=(ctx.author.id,))                
                    pack_cards = pd.DataFrame(pack_cards)
                    choices = (pack_cards['id'].sample(n=2, weights=pack_cards['weight'])).tolist()
                    ADD_CARD_ADDON = '('
                    cards_received_message = 'You received the following cards:\n'
                    for i, c in enumerate(choices):
                        card_name = pack_cards.loc[pack_cards['id']==c,'name'].iloc[0]
                        card_position = pack_cards.loc[pack_cards['id']==c,'position'].iloc[0]
                        if i+1 < len(choices):
                            ADD_CARD_ADDON += f'{c}, '
                            cards_received_message += f"{card_position} {card_name}\n"
                        elif i+1 == len(choices):
                            ADD_CARD_ADDON += f'{c}) '
                            cards_received_message += f"{card_position} {card_name}"
                        
                    ADD_CARDS_INVENTORY_SQL= f'''INSERT INTO tcg_inventory (card_id, user_id, count)
                                                SELECT * 
                                                FROM (
                                                        SELECT id as 'card_id', (SELECT id FROM tcg_users WHERE discord_id={ctx.author.id}) as 'user_id', 0 
                                                        FROM tcg_card
                                                        WHERE id IN {ADD_CARD_ADDON}
                                                        ) AS tmp
                                                WHERE tmp.card_id NOT IN (
                                                    SELECT card_id FROM tcg_inventory 
                                                    WHERE user_id=(SELECT id FROM tcg_users WHERE discord_id={ctx.author.id})
                                                    AND card_id IN {ADD_CARD_ADDON}
                                                );'''.replace('\n','')
                    UPDATE_CARD_COUNT_SQL = f'''UPDATE tcg_inventory
                                                SET count = count + 1
                                                WHERE user_id=(SELECT id FROM tcg_users WHERE discord_id={ctx.author.id})
                                                AND card_id IN {ADD_CARD_ADDON};'''.replace('\n','')
                    process_MySQL(ADD_CARDS_INVENTORY_SQL)
                    process_MySQL(UPDATE_CARD_COUNT_SQL)
                    #await ctx.send(cards_received_message)
                    await sent_message.edit(content=cards_received_message)

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

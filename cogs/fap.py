import asyncio
import discord
import datetime
from utils.recruit import FootballRecruit
from discord.ext import commands
from utils.mysql import process_MySQL

async def get_teams():
    get_teams_query = '''SELECT name FROM team_ids;'''
    sql_teams = process_MySQL(query = get_teams_query, fetch = 'all')
    teams_list = [t['name'] for t in sql_teams]
    return teams_list

async def get_prediction(user, recruit):
    get_prediction_query = '''SELECT * FROM fap_predictions
                              WHERE user_id = %s AND recruit_profile = %s;'''
    sql_response = process_MySQL(query = get_prediction_query, values = (user.id, recruit.x247_profile), fetch = 'one')
    return sql_response
        
async def insert_prediction(user, recruit, team_prediction, prediction_confidence, previous_prediction):
    if previous_prediction is None:
        insert_prediction_query = '''INSERT INTO fap_predictions (user, user_id, recruit_name, recruit_profile, recruit_class, team, confidence, prediction_date)
                                     VALUES (%s, %s, %s, %s, %s, %s, %s, NOW());'''
        process_MySQL(query = insert_prediction_query, values = (user.name, user.id, recruit.name, recruit.x247_profile, recruit.year, team_prediction, prediction_confidence))
    else:
        update_prediction_query = '''UPDATE fap_predictions
                                     SET team = %s, confidence = %s, prediction_date = NOW()
                                     WHERE user_id = %s and recruit_profile = %s;'''
        process_MySQL(query = update_prediction_query, values = (team_prediction, prediction_confidence, user.id, recruit.x247_profile))
        
def get_croot_predictions(recruit):
    get_croot_preds_query = '''SELECT f.recruit_name, f.team, avg(f.confidence) as 'confidence', (count(f.team) / t.sumr) * 100 as 'percent', t.sumr as 'total'
                               FROM fap_predictions as f
                               JOIN (SELECT recruit_profile, COUNT(recruit_profile) as sumr FROM fap_predictions GROUP BY recruit_profile) as t on t.recruit_profile = f.recruit_profile
                               WHERE f.recruit_profile = %s
                               GROUP BY f.recruit_profile, f.recruit_name, f.team
                               ORDER BY percent DESC;
                            '''
    get_croot_preds_response = process_MySQL(query = get_croot_preds_query, values = (recruit.x247_profile), fetch = 'all')
    return get_croot_preds_response
    
async def initiate_fap(user, recruit, client):
    valid_teams = await get_teams()
    team_prediction = None
    prediction_confidence = None
    channel = user.dm_channel
    if user.dm_channel is None:
        channel = await user.create_dm()
        
    previous_prediction = await get_prediction(user, recruit)
    if previous_prediction is not None:
        await channel.send(f"It appears that you've previously predicted {recruit.name} to {previous_prediction['team']} with confidence {previous_prediction['confidence']}. You can answer the prompts to update your prediction.")       
    await channel.send(f'Please predict which team you think {recruit.name} will commit to. (247 Profile: {recruit.x247_profile})')
    while(team_prediction is None):
        try:
            prediction_response = await client.wait_for('message', 
                                                        check=lambda message:message.author == user and message.channel == channel,
                                                        timeout = 30)
        except asyncio.TimeoutError:
            await channel.send("Sorry, you ran out of time. You'll have to initiate the FAP process again by clicking the crystal ball emoji on the crootbot message or using the $predict command.")
            return
        else:
            if prediction_response.content.lower() in [t.lower() for t in valid_teams]:
                team_index = [t.lower() for t in valid_teams].index(prediction_response.content.lower())
                team_prediction = valid_teams[team_index]
                await channel.send(f"You've selected {team_prediction} as your prediction, what is your confidence in that pick from 1 to 10?")                   
            else:
                await channel.send("That isn't a valid team. Please try again or ask my creators to add that as a valid team.")
    
    while(prediction_confidence is None):
        try:
            confidence_response = await client.wait_for('message', 
                                                        check=lambda message:message.author == user and message.channel == channel,
                                                        timeout = 30)
        except asyncio.TimeoutError:
            await channel.send("Sorry, you ran out of time. You'll have to initiate the FAP process again by clicking the crystal ball emoji on the crootbot message or using the $predict command.")
            return
        else:
            try:
                confidence = int(confidence_response.content)
            except:
                await channel.send("That input was not accepted, please enter a number between 1 and 10.")
            else:
                if confidence >= 1 and confidence <= 10:
                    await channel.send(f"You've selected {confidence} as your confidence level.")
                    prediction_confidence = int(confidence_response.content)
                else:
                    await channel.send(f"{confidence} is not between 1 and 10. Try again.")
              
    await insert_prediction(user, recruit, team_prediction, prediction_confidence, previous_prediction)
    await channel.send(f"Your prediction of {recruit.name} to {team_prediction} has been logged!")
    
def get_faps(recruit):
    croot_preds = get_croot_predictions(recruit)
    return croot_preds

class fapCommands(commands.Cog):
        
    @commands.command(aliases=["predict", ])  
    async def fap(self, ctx, year: int, *name):
        """ Put in a FAP prediction for a recruit """
        from utils.client import client
        from utils.embed import build_embed
        
        if len(name) == 0:
            raise discord.ext.commands.UserInputError("A player's first and/or last name is required.")

        if len(str(year)) == 2:
            year += 2000

        if year > datetime.datetime.now().year + 5:
            raise discord.ext.commands.UserInputError("The search year must be within five years of the current class.")

        if year < 1869:
            raise discord.ext.commands.UserInputError("The search year must be after the first season of college football--1869.")

        edit_msg = await ctx.send("Loading...")
        search = FootballRecruit(year, name)

        if type(search) == commands.UserInputError:
            await edit_msg.edit(content=search)
            return
        
        async def send_fap_convo(target_recruit):
            await initiate_fap(ctx.message.author, target_recruit, client)
                    
        
        if len(search) == 1:
            await edit_msg.delete()
            await send_fap_convo(search[0])
            return

        result_info = ""
        search_reactions = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4, "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8, "🔟": 9}

        index = 0

        for index, result in enumerate(search):
            if index < 10:
                result_info += f"{list(search_reactions.keys())[index]}: {result.year} - {'⭐' * result.rating_stars}{' - ' + result.position if result.rating_stars > 0 else result.position} - {result.name}\n"

        embed = build_embed(
            title=f"Search Results for [{year} {[n for n in name]}]",
            fields=[["Search Results", result_info]]
        )

        await edit_msg.edit(content="", embed=embed)

        for reaction in list(search_reactions.keys())[0:index + 1]:
            await edit_msg.add_reaction(reaction)

        def checking_reaction(reaction, user):
            if not user.bot:
                return (reaction.emoji in search_reactions) and (user == ctx.message.author)

        search_result_player = None

        try:
            reaction, user = await client.wait_for("reaction_add", check=checking_reaction)
        except asyncio.TimeoutError:
            pass
        else:
            search_result_player = search[search_reactions[reaction.emoji]]
        
        try:
            await edit_msg.delete()
        except discord.HTTPException:
            print("Deleting the message failed.")
        except discord.ClientException:
            print("Unable to delete message due to lack of permissions.")
            
        await send_fap_convo(search_result_player)
        
def setup(bot):
    bot.add_cog(fapCommands(bot))      
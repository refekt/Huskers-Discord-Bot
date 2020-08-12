import asyncio
import discord
from discord.ext import commands

from utils.client import client

class fapConversation:
    def __init__(self, player, profile_url):
        self.player = player
        self.profile_url = profile_url
        self.school = None
        self.confidence = None
        
    def setSchool(self, school):
        self.school = school
        
    def setConfidence(self, confidence):
        self.confidence = confidence

class fapCommands(commands.Cog):
    async def initiate_fap(user, recruit):
        channel = user.dm_channel
        if user.dm_channel is None:
            channel = await user.create_dm()
        msg = await channel.send(f'Please make a prediction for {recruit.name} ({recruit.x247_profile})')
        no_prediction = True
        while(no_prediction):
            try:
                prediction_response = await client.wait_for('message', 
                                                            check=lambda message:message.author == user and message.channel == channel,
                                                            timeout = 120)
            except asyncio.TimeoutError:
                channel.send("Sorry, you ran out of time. You'll have to initiate the FAP process again by clicking the crystal ball emoji on the crootbot message.")
                return
            else:
                if prediction_response.content == 'Nebraska':
                    await channel.send("You've selected Nebraska as your prediction, what is your confidence in that pick from 1 to 10?")
                    no_prediction = False
                else:
                    await channel.send("That isn't a valid team. Please try again or ask my creators to add that as a valid team.")
        
        no_confidence = True
        while(no_confidence):
            try:
                confidence_response = await client.wait_for('message', 
                                                            check=lambda message:message.author == user and message.channel == channel,
                                                            timeout = 120)
            except asyncio.TimeoutError:
                await channel.send("Sorry, you ran out of time. You'll have to initiate the FAP process again by clicking the crystal ball emoji on the crootbot message.")
                return
            else:
                try:
                    confidence = int(confidence_response.content)
                except:
                    await channel.send("That input was not accepted, please enter a number between 1 and 10.")
                else:
                    if confidence >= 1 and confidence <= 10:
                        await channel.send(f"You've selected {confidence} as your confidence level.")
                        no_confidence = False
                    else:
                        await channel.send(f"{confidence} is not between 1 and 10. Try again.")
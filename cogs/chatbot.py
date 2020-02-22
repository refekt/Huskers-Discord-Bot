from chatterbot.chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from discord.ext import commands

chatbot = ChatBot("Bot Frost Bot")


def convert_messages_to_list(messages):
    output_list = []

    for message in messages:
        output_list.append(message.clean_content)

    return output_list


def create_chatbot(message_list: list):
    trainer = ListTrainer(chatbot)
    trainer.train(message_list)


class ChatBot(commands.Cog):
    @commands.command()
    async def cb_start(self, ctx):
        messages = await ctx.channel.history().flatten()
        list = convert_messages_to_list(messages)
        create_chatbot(list)

        await ctx.send("Chat bot started!")

    @commands.command()
    async def cb_say(self, ctx, *, question):
        await ctx.send(chatbot.get_response(question))


def setup(bot):
    bot.add_cog(ChatBot(bot))
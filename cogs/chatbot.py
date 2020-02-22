from chatterbot.chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer
from discord.ext import commands

chatbot = ChatBot("Bot Frost Bot")


def convert_messages_to_list(messages):
    output_list = []

    def cleanup_message(msg: str):
        msg = msg.replace("`","")
        msg = msg.replace("\n", "")

    for message in messages:
        if message.clean_content and not message.clean_content == "\n":
            output_list.append(cleanup_message(message.clean_content))

    from pprint import pprint
    pprint(output_list)

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

    @commands.command()
    async def cb_train(self, ctx):
        trainer = ListTrainer(chatbot)
        messages = await ctx.channel.history().flatten()
        list = convert_messages_to_list(messages)
        trainer.train(list)


def setup(bot):
    bot.add_cog(ChatBot(bot))
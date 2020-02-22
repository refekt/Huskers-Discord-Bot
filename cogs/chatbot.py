from chatterbot.chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from discord.ext import commands
from utils.client import client

chatbot = ChatBot("Bot Frost")
trainer = ListTrainer(chatbot)


class ChatBot(commands.Cog):
    @commands.command()
    async def cb_train(self, ctx):
        message_list = await ctx.channel.history().flatten()
        training_list = []

        def cleanup_message(msg: str):
            msg = msg.replace("`", "")
            msg = msg.replace("\n", "")

            return msg

        for msg in message_list:
            if msg.clean_content and not msg.clean_content.startswith(client.command_prefix):
                training_list.append(cleanup_message(msg.clean_content))

        trainer.train(training_list)


def setup(bot):
    bot.add_cog(ChatBot(bot))
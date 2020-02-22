from chatterbot.chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from discord.ext import commands


chatbot = ChatBot("Bot Frost", logic_adapters=["chatterbot.logic.BestMatch", "chatterbot.logic.MathematicalEvaluation"])
trainer = ListTrainer(chatbot)


class ChatBot(commands.Cog):
    @commands.command()
    async def cb_train(self, ctx):
        edit_msg = await ctx.send("Training myself...")
        message_list = await ctx.channel.history().flatten()
        training_list = []

        def cleanup_message(msg: str):
            msg = msg.replace("`", "")
            msg = msg.replace("\n", "")

            return msg

        for msg in message_list:
            if msg.clean_content and not msg.clean_content.startswith("$"):
                training_list.append(cleanup_message(msg.clean_content))

        trainer.train(training_list)

        await edit_msg.edit(content="Chat bot trained!")

    @commands.command()
    async def cb_export(self, ctx):
        trainer.export_for_training("export.json")


def setup(bot):
    bot.add_cog(ChatBot(bot))
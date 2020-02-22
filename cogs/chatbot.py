from chatterbot.chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from discord.ext import commands
from utils.consts import ROLE_ADMIN_TEST, ROLE_ADMIN_PROD, ROLE_MOD_PROD
from chatterbot import filters

chatbot = ChatBot("Bot Frost",
                  logic_adapters=["chatterbot.logic.BestMatch", "chatterbot.logic.MathematicalEvaluation"],
                  filters=[filters.get_recent_repeated_responses])
trainer = ChatterBotCorpusTrainer(chatbot)


class ChatBot(commands.Cog):
    @commands.command(hidden=True)
    # @commands.has_any_role(ROLE_MOD_PROD, ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def cb_train(self, ctx):
        edit_msg = await ctx.send("Training myself...")
        trainer = ChatterBotCorpusTrainer(chatbot)
        trainer.train("chatterbot.corpus.english")

        await edit_msg.edit(content="Chat bot trained!")

    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_MOD_PROD, ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def cb_export(self, ctx):
        trainer.export_for_training("export.json")


def setup(bot):
    bot.add_cog(ChatBot(bot))

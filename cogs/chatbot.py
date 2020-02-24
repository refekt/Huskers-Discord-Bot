import logging

from chatterbot import filters
from chatterbot.chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from discord.ext import commands

from utils.consts import ROLE_ADMIN_TEST, ROLE_ADMIN_PROD, ROLE_MOD_PROD

chatbot = ChatBot("Bot Frost",
                  logic_adapters=[{
                      'import_path': 'chatterbot.logic.BestMatch',
                      'default_response': 'Who knows what you\'re trying to say. You\'re probably a Gumby alt',
                      'maximum_similarity_threshold': 0.90
                  }],
                  preprocessors=[
                      "chatterbot.preprocessors.clean_whitespace",
                      "chatterbot.preprocessors.convert_to_ascii"]
                  ,
                  filters=[filters.get_recent_repeated_responses],
                  storage_adapter="chatterbot.storage.SQLStorageAdapter",
                  read_only=False,
                  database_uri=None
                  )
trainer = ChatterBotCorpusTrainer(chatbot)

logging.basicConfig(level=logging.INFO)


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

import re

import discord
from chatterbot import filters
from chatterbot.chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
from discord.ext import commands

from utils.consts import ROLE_ADMIN_TEST, ROLE_ADMIN_PROD, ROLE_MOD_PROD

chatbot = ChatBot("Bot Frost",
                  logic_adapters=[{
                      'import_path': 'chatterbot.logic.BestMatch',
                      'default_response': 'Who knows what you\'re trying to say...not me',
                      'maximum_similarity_threshold': 0.90
                  }],
                  preprocessors=[
                      "chatterbot.preprocessors.clean_whitespace",
                      "chatterbot.preprocessors.convert_to_ascii"]
                  ,
                  filters=[filters.get_recent_repeated_responses],
                  storage_adapter="chatterbot.storage.SQLStorageAdapter",
                  read_only=False
                  )
trainer = ChatterBotCorpusTrainer(chatbot)


class ChatBot(commands.Cog):
    @commands.command(hidden=True)
    async def chatbot_train(self, ctx):
        edit_msg = await ctx.send("Training myself...")
        trainer = ChatterBotCorpusTrainer(chatbot)
        trainer.train("chatterbot.corpus.english")

        await edit_msg.edit(content="Chat bot trained!")

    @commands.command(hidden=True)
    async def chatbot_grab_history_and_train(self, ctx):
        edit_msg = await ctx.send("Loading...")

        def clean_message(msg: str):
            mentions = r"<@!{0,1}\d{18}>"
            urls = r"^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"
            commands = r"(\$|\%)(\w{0,}|\s(\w{0,}(\#\w{0,})|\d{0,}))"

            output = re.sub(mentions, "", msg)
            output = re.sub(urls, "", output)
            output = re.sub(commands, "", output)
            output = output.strip()
            output.encode()

            return output

        history = await ctx.channel.history(limit=5000).flatten()
        conversation = []

        await edit_msg.edit(content=edit_msg.content + "History grabbed...")

        await edit_msg.edit(content=edit_msg.content + "Cleaning messages...")

        for message in history:
            if not message.author.bot:
                cleaned = clean_message(message.content)
                if cleaned:
                    conversation.append(cleaned)

        await edit_msg.edit(content=edit_msg.content + "Messages cleaned...")

        trainer = ListTrainer(chatbot)
        trainer.train(conversation)

        await edit_msg.edit(content=edit_msg.content + "Chatbot trained!")

    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_MOD_PROD, ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def chatbot_export(self, ctx):
        trainer.export_for_training("export.json")


def setup(bot):
    bot.add_cog(ChatBot(bot))

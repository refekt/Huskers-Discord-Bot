from discord.ext import commands
import mysql, config
# import random


def load_questions():
    with mysql.sqlConnection.cursor() as cursor:
        cursor.execute(config.sqlRetrieveTriviaQuestions)
        trivia_questions = cursor.fetchall()
    mysql.sqlConnection.commit()


class Trivia(commands.Cog, name="Husker Trivia"):
    """Husker trivia"""
    load_questions()

    @commands.group()
    async def trivia(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Trivia(bot))

import asyncio
import enum
import hashlib
import logging
import random
from html import unescape
from typing import ClassVar, Optional, Any, Union

import discord
import requests
from requests import Response

from helpers.constants import HEADERS, GLOBAL_TIMEOUT
from helpers.embed import buildEmbed
from objects.Exceptions import TriviaException
from objects.Logger import discordLogger, is_debugging

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

__all__ = [
    "TriviaBot",
    "TriviaCategories",
    "TriviaDifficulty",
    "TriviaQuestionType",
]

trivia_players: dict[str, int] = {}


# https://opentdb.com/api_config.php


class SessionToken(str):
    def __init__(self) -> None:
        self.response_code: int = 0
        self.response_message: str = ""
        self.token: str = ""
        self.token_request_url: str = (
            "https://opentdb.com/api_token.php?command=request"
        )
        self.token_reset_url: str = (
            f"https://opentdb.com/api_token.php?command=reset&token={self.token}"
        )

    def set_token(self) -> str:
        logger.debug("Getting a new session token")

        resp: Response = requests.get(url=self.token_request_url, headers=HEADERS)

        if resp.status_code == 200:
            j = resp.json()
            self.response_code = j["response_code"]
            self.response_message = j["response_message"]
            self.token = j["token"]
        else:
            raise TriviaException("Unable to set token.")

        return self.token

    def reset_token(
        self,
    ) -> str:  # May not be needed since all questions are queried up front
        logger.debug("Resetting session token")

        resp: Response = requests.get(url=self.token_reset_url, headers=HEADERS)

        if resp.status_code == 200:
            j = resp.json()
            self.response_code = j["response_code"]
            self.response_message = j["response_message"]
            self.token = j["token"]
        else:
            raise TriviaException("Unable to reset token.")

        return self.token

    def __str__(self) -> str:
        return self.token


class TriviaStartButtons(discord.ui.View):
    def __init__(self, game_master: discord.Member) -> None:
        super().__init__(timeout=GLOBAL_TIMEOUT)
        self.running: Optional[bool] = None
        self.game_master: discord.Member = game_master

    def on_timeout(self) -> None:
        logger.debug("Clearing all buttons")
        self.clear_items()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if interaction.user == self.game_master:
            logger.debug(
                f"Confirm pressed with match. {interaction.user} == {self.game_master}"
            )

            self.running = True
            self.stop()
        else:
            logger.debug(
                f"Confirm pressed with no match. {interaction.user} == {self.game_master}"
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if interaction.user == self.game_master:
            logger.debug(
                f"Cancel pressed with match. {interaction.user} == {self.game_master}"
            )

            self.running = False
            self.stop()
        else:
            logger.debug(
                f"Cancel pressed with no match. {interaction.user} == {self.game_master}"
            )


class TriviaCategories(int, enum.Enum):
    # https://opentdb.com/api_count.php?category=CATEGORY_ID_HERE
    # https://opentdb.com/api_count_global.php

    any = 0
    general = 9
    entertainment_books = 10
    entertainment_film = 11
    entertainment_music = 12
    entertainment_musicals_theaters = 13
    entertainment_television = 14
    entertainment_video_games = 15
    entertainment_board_games = 16
    science_nature = 17
    science_computers = 18
    science_math = 19
    science_mythology = 20
    science_sports = 21
    science_geography = 22
    science_history = 23
    science_politics = 24
    science_art = 25
    celebrities = 26
    animals = 27
    vehicles = 28
    entertainment_comics = 29
    entertainment_gadgets = 30
    entertainment_anime = 31
    entertainment_cartoons = 32

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)


class TriviaDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

    def __str__(self) -> str:
        return str(self.value)


class TriviaQuestionType(str, enum.Enum):
    any = ""
    multiple = "multiple"
    true_false = "boolean"

    def __str__(self) -> str:
        return str(self.value)


class TriviaQuestions:
    def __init__(
        self,
        category: TriviaCategories,
        question_type: TriviaQuestionType,
        difficulty: TriviaDifficulty,
        question: str,
        correct_answer: str,
        incorrect_answers: list[str],
    ) -> None:
        self.category: TriviaCategories = category
        self.type: TriviaQuestionType = question_type
        self.difficulty: TriviaDifficulty = difficulty
        self.question: str = question
        self.correct_answer: str = correct_answer
        self.incorrect_answers: list[str] = incorrect_answers
        self.answers: list[str] = self.incorrect_answers + [self.correct_answer]
        random.shuffle(self.answers)

    def __str__(self) -> str:
        return f"<{self.question}>:" + "|".join([answer for answer in self.answers])


class InteractionData(str):
    __slots__ = [
        "component_type",
        "custom_id",
    ]

    def __init__(self, data_dict: dict) -> None:
        for key, value in data_dict.items():
            setattr(self, key, value)


class TriviaQuestionButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str) -> None:
        super().__init__(
            label=label, custom_id=custom_id, style=discord.ButtonStyle.green
        )


class TriviaQuestionCancelButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Cancel", custom_id="cancel", style=discord.ButtonStyle.grey
        )


def tally_score(player: discord.Member, point: int) -> dict[str, int]:
    player_name: str = f"{player.name}#{player.discriminator}"

    logger.debug(f"Adding [{point} point] to [player_name]")

    global trivia_players

    if player_name not in trivia_players.keys():
        trivia_players[player_name] = 0

    if point == 1:
        trivia_players[player_name] = trivia_players[player_name] + point
    elif point == -1:
        trivia_players[player_name] = trivia_players[player_name] - abs(point)

    logger.debug(f"Current scores are: {trivia_players}")

    return {f"{player_name}": trivia_players[player_name]}


class TriviaQuestionView(discord.ui.View):
    LABEL_LIMIT: ClassVar[int] = 80
    CUSTOM_ID_LIMIT: ClassVar[int] = 100

    def __init__(self, question: TriviaQuestions, game_master: discord.Member) -> None:
        super().__init__(timeout=GLOBAL_TIMEOUT)
        logger.debug(f"Adding question: {str(question).encode('utf-8', 'replace')}")

        for index, answer in enumerate(question.answers):
            self.add_item(
                TriviaQuestionButton(
                    label=unescape(answer[: self.LABEL_LIMIT]),
                    custom_id=f"correct_{index}"[: self.CUSTOM_ID_LIMIT]
                    if answer == question.correct_answer
                    else f"incorrect_{index}",
                )
            )
        self.add_item(TriviaQuestionCancelButton())
        self.cancel: bool = False
        self.is_correct: bool = False
        self.players: dict[str, float] = {}
        self.game_master: discord.Member = game_master
        self.check_already_pressed: list[str] = []

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        data: InteractionData = InteractionData(interaction.data)

        if str(data.custom_id) == "cancel" and interaction.user == self.game_master:
            self.cancel = True
            self.stop()
            return True

        def get_hashed_user(user: discord.Member) -> str:
            return hashlib.sha1(str(user.id).encode("UTF-8")).hexdigest()[:10]

        if get_hashed_user(user=interaction.user) in self.check_already_pressed:
            logger.debug("User already pressed a button.")
            await interaction.response.send_message(
                f"You have already answered! This message can be dismissed.",
                ephemeral=True,
            )

            return True
        else:
            self.check_already_pressed.append(get_hashed_user(user=interaction.user))

        buttons: list[discord.Button] = interaction.message.components[0].children
        pressed_button = [
            item.label for item in buttons if item.custom_id == data.custom_id
        ]

        logger.debug(f"Question button {pressed_button} pressed.")

        if str(data.custom_id).startswith("correct"):
            self.is_correct = True
            self.players.update(tally_score(player=interaction.user, point=1))
        elif str(data.custom_id).startswith("incorrect"):
            self.is_correct = False
            self.players.update(tally_score(player=interaction.user, point=-1))

        await interaction.response.send_message(
            f"You selected {pressed_button}. Your score is [{trivia_players[f'{interaction.user.name}#{interaction.user.discriminator}']}]. This message can be dismissed.",
            ephemeral=True,
        )

        return True

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[Any],
    ) -> None:
        logger.exception(error, exc_info=True)


class TriviaBot:
    MAX_QUESTIONS: ClassVar[int] = 20

    def __init__(
        self,
        game_master: discord.Member,
        channel: Union[discord.TextChannel, Any],
        category: TriviaCategories,
        difficulty: TriviaDifficulty,
        question_type: TriviaQuestionType,
        question_amount: int,
        question_duration: int = 5 if is_debugging() else 15,
    ) -> None:
        self.session_token: SessionToken = SessionToken()
        self.session_token.set_token()
        self.api_url: str = (
            f"https://opentdb.com/api.php?amount={min(question_amount, self.MAX_QUESTIONS)}&"
            f"category={'' if category == TriviaCategories.any else category}&"
            f"difficulty={difficulty}&"
            f"type={question_type}&"
            f"token={self.session_token}"
        )
        self.category: str = category.name
        self.channel: discord.TextChannel = channel
        self.current_embed: Optional[int] = None
        self.current_question: Optional[int] = None
        self.difficulty: str = difficulty.name
        self.game_master: discord.Member = game_master
        self.question_duration: int = question_duration
        self.question_type: str = question_type.name
        self.question_view: Optional[TriviaQuestionView] = None
        self.questions: list[TriviaQuestions] = []
        self.running: bool = False
        self.trivia_message: Optional[discord.Message] = None
        self.embeds: list[discord.Embed] = [
            buildEmbed(
                title="Trivia Bot",
                description="Welcome to Trivia Bot! Read the rules below and confirm whether or not to start a game.",
                fields=[
                    dict(name="Game Master", value=f"👑 {self.game_master.mention}"),
                    dict(
                        name="Rules",
                        value="The game master will choose the category and number of questions. "
                        "Everyone in the server can join. "
                        f"There are maximum number of {self.MAX_QUESTIONS} questions. "
                        "The winner is determined by the number of correct questions at the end of the game.",
                    ),
                    dict(
                        name="Game Info",
                        value=f"Category: {self.category.title()}\n"
                        f"Difficulty: {self.difficulty.title()}\n"
                        f"Question Types: {self.question_type.title()}\n"
                        f"Number of Questions: {question_amount}\n"
                        f"Question Timer: {question_duration} seconds",
                    ),
                    dict(
                        name="Ready?",
                        value="Click 'Confirm' below to start the game or 'Cancel' to quit.",
                    ),
                ],
            ),
        ]
        self.initial_embed: discord.Embed = self.embeds[0]
        self.load_questions()

    def load_questions(self) -> None:
        resp: Response = requests.get(url=self.api_url, headers=HEADERS)

        if resp.status_code == 200:
            j = resp.json()

            if j["response_code"] == 0:
                for index, result in enumerate(j["results"]):
                    self.questions.append(
                        TriviaQuestions(
                            category=unescape(result["category"]),
                            question_type=unescape(result["type"]),
                            difficulty=unescape(result["difficulty"]),
                            question=unescape(result["question"]),
                            correct_answer=unescape(result["correct_answer"]),
                            incorrect_answers=unescape(result["incorrect_answers"]),
                        )
                    )
                    new_line: str = "\n"
                    self.embeds.append(
                        buildEmbed(
                            title=f"Trivia Bot Game Master: 👑 {self.game_master.name}#{self.game_master.discriminator}",
                            description=f"Q {index + 1}/{len(j['results'])} | {unescape(result['category'])} | "
                            f"{unescape(str(result['type']).title())} | "
                            f"{unescape(str(result['difficulty']).title())}",
                            fields=[
                                dict(
                                    name="Question",
                                    value=unescape(result["question"]),
                                    inline=False,
                                ),
                            ],
                        )
                    )
            else:
                raise TriviaException("Unable to load questions")

    def leaderboard(self) -> str:
        if self.question_view.cancel:
            return "The game was cancelled."

        sorted_players = sorted(
            trivia_players.items(), key=lambda kv: kv[1], reverse=True
        )
        lb = "\n".join(
            [
                f"#{index + 1}: {value} -- {key}"
                for index, (key, value) in enumerate(sorted_players)
            ]
        )

        if not lb:
            return "No one played this session."

        return lb

    async def start_game(self) -> None:
        logger.info("Starting a trivia game")

        global trivia_players

        start_view = TriviaStartButtons(game_master=self.game_master)

        self.trivia_message = await self.channel.send(
            embed=self.initial_embed,
            view=start_view,
        )
        await start_view.wait()

        if start_view.running is None:
            logger.exception("Trivia bot timed out")
            return
        elif start_view.running:
            await self.trivia_message.delete()

            self.running = True
            self.current_question = -1
            self.current_embed = self.current_question + 1

            while self.running:
                if self.question_view:
                    if self.question_view.cancel:
                        logger.debug("Cancelling the game")
                        self.running = False
                        break

                self.current_question += 1
                self.current_embed += 1

                if self.current_question >= len(self.questions):
                    logger.debug("Stopping game because there are no more questions")
                    self.running = False
                    break

                self.question_view = TriviaQuestionView(
                    question=self.questions[self.current_question],
                    game_master=self.game_master,
                )

                self.trivia_message = await self.channel.send(
                    embed=self.embeds[self.current_embed],
                    view=self.question_view,
                )

                await asyncio.sleep(self.question_duration)

                logger.info("Moving to next question")

                await self.trivia_message.edit(
                    view=None,
                    embed=self.trivia_message.embeds[0]
                    .add_field(
                        name="Correct Answer",
                        value=unescape(
                            self.questions[self.current_question].correct_answer
                        ),
                    )
                    .add_field(
                        name="Players",
                        value=[player for player in self.question_view.players.keys()]
                        if self.question_view.players
                        else "N/A",
                    ),
                )

                logger.debug("Updating trivia scores")

            logger.debug("Trivia game is over. Sending leaderboard")

            embed = buildEmbed(
                title="Trivia Bot Results",
                description="Game over!",
                fields=[
                    dict(
                        name="Game Info",
                        value=f"Category: {self.category.title()}\n"
                        f"Difficulty: {self.difficulty.title()}\n"
                        f"Question Types: {self.question_type.title()}\n",
                    ),
                    dict(name="Leaderboard", value=self.leaderboard()),
                ],
            )
            await self.channel.send(embed=embed)

            trivia_players = {}

        else:
            logger.info("Cancelling trivia game")
            await self.trivia_message.delete()

            trivia_players = {}

            await self.channel.send(content="The trivia game was cancelled.")


logger.info(f"{str(__name__).title()} module loaded!")

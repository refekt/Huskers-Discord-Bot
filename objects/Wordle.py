import logging
import re
from typing import ClassVar, Union, Optional

import discord

from helpers.constants import DEBUGGING_CODE
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__ = ["Wordle", "WordleFinder"]


class Wordle:
    __slots__ = [
        "__b",
        "__g",
        "__y",
        "message",
    ]

    __REGEX_DAY: ClassVar[str] = r"\s\d{3,4}\s"
    __REGEX_SCORE: ClassVar[str] = r"(\d{1}|X)\/\d{1}"

    def __init__(
        self,
        message: str,
    ) -> None:
        self.message: str = message.replace("\n\n", "\n")
        self.__y: ClassVar[tuple[str, str]] = (":yellow_square:", "🟨")
        self.__g: ClassVar[tuple[str, str]] = (":green_square:", "🟩")
        self.__b: ClassVar[tuple[str, str]] = (":black_large_square:", "⬛")

    @property
    def day(self) -> int:
        search = re.search(self.__REGEX_DAY, self.message)
        try:
            pos: tuple[int, int] = search.regs[0]
        except IndexError:
            return 0

        day: int = int(self.message[pos[0] : pos[1]])

        assert day > 0 and type(day) == int, ValueError("Invalid day.")

        return day

    @property
    def score(self) -> Union[int, str]:
        search = re.search(self.__REGEX_SCORE, self.message)
        try:
            pos: tuple[Union[int, str], int] = search.regs[0]
        except IndexError:
            return "N/A"

        score: Union[int, str] = self.message[pos[0] : pos[0] + 1]

        if score.isnumeric():
            assert 1 <= int(score) <= 6, ValueError("Score is not between 1 and 6")
            return score
        elif score.upper() == "X":
            return score.upper()
        else:
            raise ValueError("Invalid score.")

    @property
    def green_squares(self) -> int:
        total_color_count: int = 0
        for color in self.__g:
            total_color_count += self.message.count(color)
        return total_color_count

    @property
    def yellow_squares(self) -> int:
        total_color_count: int = 0
        for color in self.__y:
            total_color_count += self.message.count(color)
        return total_color_count

    @property
    def black_squares(self) -> int:
        total_color_count: int = 0
        for color in self.__b:
            total_color_count += self.message.count(color)
        return total_color_count

    @property
    def total_squares(self) -> int:
        return self.green_squares + self.yellow_squares + self.black_squares


class WordleFinder:
    __slots__ = ["wordle_finder"]

    def __init__(self, search_channel: discord.TextChannel) -> None:
        self.wordle_finder: ClassVar[str] = r"^Wordle\s\d{3,4}\s\d{1}\/\d{1}"

    def get_wordle_message(self, message: discord.Message) -> Optional[Wordle]:
        msg: str = message.content

        if re.search(self.wordle_finder, str(message.clean_content)):
            try:
                return Wordle(message=msg)
            except UnicodeError:
                return None
        else:
            return None


logger.info(f"{str(__name__).title()} module loaded!")

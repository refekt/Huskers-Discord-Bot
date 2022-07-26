import logging
import re
from typing import ClassVar, Union, Optional

import discord

from helpers.constants import DEBUGGING_CODE
from objects.Exceptions import WordleException
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__ = ["Wordle", "WordleFinder"]


class WordleConfirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.value: Optional[bool] = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = False
        self.stop()


class Wordle:
    __slots__ = [
        "__b",
        "__boxes",
        "__err_mg",
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
        self.__boxes: list[str] = self.message.strip().split("\n")
        self.__b: ClassVar[str] = "⬛"  # ":black_large_square:"
        self.__g: ClassVar[str] = "🟩"  # ":green_square:"
        self.__y: ClassVar[str] = "🟨"  # ":yellow_square:"
        self.__err_mg: str = "Denied! User submitted an invalid Wordle score."

        # Check each line is accurate
        for line in self.__boxes:

            # Skip first line
            if "Wordle" in line:
                continue

            logger.debug("Checking if line is 5 chars long")

            # Check if each line is 5 characters long
            assert len(line) == 5, WordleException(self.__err_mg)

            _line_count: int = 0
            _box_count: int = 0

            # Check to make sure no illegal characters are present
            for box in (self.__b, self.__g, self.__y):

                _box_count = line.count(box)
                logger.debug(f"Box count is {_box_count}")

                if _box_count:
                    _line_count += _box_count
                    logger.debug(f"Line count is {_line_count}")

            logger.debug("Checking if line count totals 5")
            assert _line_count == 5, WordleException(self.__err_mg)

            # Check last line is all green if a score is present
            logger.debug("Checking if last line in box and if score is not X")
            if line == self.__boxes[-1]:
                if self.score != "X":
                    assert line == self.__g * 5, WordleException(self.__err_mg)
                    logger.debug(
                        f"Line ({line.encode('utf-8', 'replace')}) is 5 green squares"
                    )
                else:
                    assert line != self.__g * 5, WordleException(self.__err_mg)
                    logger.debug("Score is X and last line is not 5 green squares")

    @property
    def day(self) -> int:
        search = re.search(self.__REGEX_DAY, self.message)
        try:
            pos: tuple[int, int] = search.regs[0]
        except IndexError:
            return 0

        day: int = int(self.message[pos[0] : pos[1]])

        assert day > 0 and type(day) == int, WordleException(self.__err_mg)

        return day

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

    @property
    def score(self) -> Union[int, str]:
        search = re.search(self.__REGEX_SCORE, self.message)
        try:
            pos: tuple[Union[int, str], int] = search.regs[0]
        except IndexError:
            return "N/A"

        score: Union[int, str] = self.message[pos[0] : pos[0] + 1]

        if score.isnumeric():
            assert 1 <= int(score) <= 6, WordleException(self.__err_mg)

            if score == 1:
                assert (
                    self.green_squares == 5
                    and self.yellow_squares == 0
                    and self.black_squares == 0
                ), WordleException(self.__err_mg)

                return score

            return score
        elif score.upper() == "X":
            return score.upper()
        else:
            raise WordleException(self.__err_mg)


class WordleFinder:
    __slots__ = ["wordle_finder"]

    def __init__(self, search_channel: discord.TextChannel) -> None:
        self.wordle_finder: ClassVar[str] = r"^Wordle\s\d{3,4}\s(\d{1}|X)\/\d{1}"

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
import datetime
import logging
import re
import statistics
from typing import ClassVar, Optional

import discord

from helpers.constants import TZ
from objects.Exceptions import WordleException
from objects.Logger import discordLogger, is_debugging

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
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
        "__backup_finder",
        "__boxes",
        "__err_mg",
        "__g",
        "__w",
        "__y",
        "_failed_score",
        "message",
    ]

    __REGEX_DAY: ClassVar[str] = r"\s\d{3,4}\s"
    __REGEX_SCORE: ClassVar[str] = r"(\d{1}|X)\/\d{1}"

    def __init__(self, message: str, backup_finder: bool = False) -> None:
        self.message: str = message.replace("\n\n", "\n")
        self.__boxes: list[str] = self.message.strip().split("\n")
        self.__b: ClassVar[str] = "⬛"  # ":black_large_square:"
        self.__w: ClassVar[str] = "⬜"  # :white_large_square:
        self.__g: ClassVar[str] = "🟩"  # ":green_square:"
        self.__y: ClassVar[str] = "🟨"  # ":yellow_square:"
        self._failed_score: ClassVar[float] = 6 + statistics.stdev([1, 2, 3, 4, 5, 6])
        self.__err_mg: str = "Denied! User submitted an invalid Wordle score."
        self.__backup_finder: bool = backup_finder

        assert len(self.__boxes) - 1 != self.score, WordleException(
            "Score and number of boxes do not match."
        )

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
            for box in (self.__b, self.__w, self.__g, self.__y):

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
                if self.score != self._failed_score:
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

        wordle_founded: datetime.date = datetime.date(year=2021, month=6, day=19)
        check_days: datetime.timedelta = (
            datetime.datetime.now(tz=TZ).date() - wordle_founded
        )

        if not self.__backup_finder:
            assert day == check_days.days, WordleException(
                "Date provided is not the correct date."
            )

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
        for color in (
            self.__b,
            self.__w,
        ):  # Not creating a separate property for white squares
            total_color_count += self.message.count(color)
        return total_color_count

    @property
    def total_squares(self) -> int:
        return self.green_squares + self.yellow_squares + self.black_squares

    @property
    def score(self) -> float | str:
        search = re.search(self.__REGEX_SCORE, self.message)
        try:
            pos: tuple[int | str, int] = search.regs[0]
        except IndexError:
            return "N/A"

        score: int | str = self.message[pos[0] : pos[0] + 1]

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
        elif score == "X":
            return self._failed_score
        else:
            raise WordleException(self.__err_mg)

    @property
    def failed_score(self) -> float:
        return self._failed_score


class WordleFinder:
    __slots__ = ["wordle_finder"]

    def __init__(self) -> None:
        self.wordle_finder: ClassVar[str] = r"Wordle\s\d{3,4}\s(\d{1}|X)\/\d{1}"

    def get_wordle_message(
        self, message: discord.Message | str, backup_finder: bool = False
    ) -> Optional[Wordle]:
        if isinstance(message, str):
            msg: str = message.strip()
        else:
            msg = message.content.strip()

        if "wordle" in msg.lower():
            logger.debug("WORDLE WORDLE WORDLE WORDLE WORDLE WORDLE WORDLE ")

        if re.search(self.wordle_finder, msg):
            try:
                return Wordle(message=msg, backup_finder=backup_finder)
            except UnicodeError:
                return None
        else:
            return None


logger.info(f"{str(__name__).title()} module loaded!")

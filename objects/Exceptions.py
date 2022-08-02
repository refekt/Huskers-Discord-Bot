# Global Errors
import logging
import platform
from dataclasses import dataclass  # https://www.youtube.com/watch?v=vBH6GRJ1REM
from typing import Optional, Any

from discord.app_commands import CommandInvokeError

from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if "Windows" in platform.platform() else logging.INFO,
)

__all__: list[str] = [
    "BettingException",
    "ChangelogException",
    "CommandException",
    "DiscordError",
    "ExtensionException",
    "ImageException",
    "MySQLException",
    "RecruitException",
    "ReminderException",
    "SSHException",
    "ScheduleException",
    "StatsException",
    "SurveyException",
    "TextException",
    "TriviaException",
    "TwitterStreamException",
    "UserInputException",
    "WeatherException",
    "WordleException",
]


class DiscordError:
    def __init__(
        self,
        original: CommandInvokeError,
        options: list[dict[str:int, str : list[dict[Any, ...]], str:str]],
        tb_msg: str,
    ) -> None:
        self.original: CommandInvokeError = original
        self.options: list[dict[str:int, str : list[dict[Any, ...]], str:str]] = (
            [
                f"{opt['name']} : {opt.get('value', 'N/A')}"
                for opt in options[0]["options"]
            ]
            if options is not None
            else None
        )
        self.traceback: str = tb_msg

    @property
    def type(self) -> str:
        return self.original.__class__.__name__

    @property
    def parent(self) -> Optional[str]:
        return self.original.command.parent

    @property
    def module(self) -> Optional[str]:
        return self.original.command.module

    @property
    def message(self) -> str:
        try:
            return self.original.original.message
        except AttributeError:
            return self.original.original.args[0]

    @property
    def command(self) -> Optional[str]:
        # TODO Monitor for Python Exceptions
        return self.original.command.qualified_name

    def __str__(self) -> str:
        return (
            f"{self.type}: /{self.command} {' '.join(self.options)}: {self.message}\n"
            f"```\n"
            f"{self.traceback}\n"
            f"```"
        )


@dataclass()
class CommandException(Exception):
    message: str


@dataclass()
class UserInputException(Exception):
    message: str


@dataclass()
class MySQLException(Exception):
    message: str


@dataclass()
class ExtensionException(Exception):
    message: str


@dataclass()
class TwitterStreamException(Exception):
    message: str


@dataclass()
class ChangelogException(Exception):
    message: str


@dataclass()
class SurveyException(Exception):
    message: str


@dataclass()
class WeatherException(Exception):
    message: str


@dataclass()
class ImageException(Exception):
    message: str


@dataclass()
class ScheduleException(Exception):
    message: str


@dataclass()
class StatsException(Exception):
    message: str


@dataclass()
class RecruitException(Exception):
    message: str


@dataclass()
class SSHException(Exception):
    message: str


@dataclass()
class ReminderException(Exception):
    message: str


@dataclass()
class BettingException(Exception):
    message: str


@dataclass()
class TextException(Exception):
    message: str


@dataclass()
class TriviaException(Exception):
    message: str


@dataclass()
class WordleException(Exception):
    message: str


ALL_EXCEPTIONS: list[object] = [
    globals()[_exc] for _exc in globals() if "Exception" in _exc
]

logger.info(f"{str(__name__).title()} module loaded!")

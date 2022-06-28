# Global Errors
import logging
import traceback
from dataclasses import dataclass  # https://www.youtube.com/watch?v=vBH6GRJ1REM
from typing import Optional

from discord.app_commands import CommandInvokeError

logger = logging.getLogger(__name__)

__all__ = [
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
    "TwitterStreamException",
    "UserInputException",
    "WeatherException",
]


class DiscordError:
    def __init__(self, original: CommandInvokeError, options: dict) -> None:
        self.command: Optional[str] = original.command.qualified_name
        self.error_type: str = type(original).__name__
        if hasattr(original, "message"):
            self.message: str = original.original.message
        elif hasattr(original, "args"):
            self.message = original.args[0]
        self.module: Optional[str] = original.command.module
        self.original: ALL_EXCEPTIONS = original.original
        self.options: list[str] = (
            [f"{opt['name']} : {opt.get('value', 'N/A')}" for opt in options]
            if options is not None
            else None
        )
        self.parent: Optional[str] = original.command.parent
        self.traceback: traceback = original.__traceback__

    def __str__(self) -> str:
        return f"{self.error_type}: {self.message}"


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


ALL_EXCEPTIONS = [globals()[_exc] for _exc in globals() if "Exception" in _exc]

logger.info(f"{str(__name__).title()} module loaded!")

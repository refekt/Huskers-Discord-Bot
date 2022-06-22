# Global Errors
import logging
from dataclasses import dataclass  # https://www.youtube.com/watch?v=vBH6GRJ1REM

logger = logging.getLogger(__name__)

__all__ = [
    "BettingException",
    "ChangelogException",
    "CommandException",
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

logger.info(f"{str(__name__).title()} module loaded!")


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

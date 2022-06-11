# Global Errors
import logging
from dataclasses import dataclass  # https://www.youtube.com/watch?v=vBH6GRJ1REM

logger = logging.getLogger(__name__)

__all__ = [
    "ChangelogException",
    "CommandException",
    "ExtensionException",
    "ImageException",
    "MySQLException",
    "RecruitException",
    "SSHException",
    "ScheduleException",
    "StatsException",
    "SurveyException",
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


class RecruitException(Exception):
    message: str


class SSHException(Exception):
    message: str

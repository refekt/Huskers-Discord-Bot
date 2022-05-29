# Global Errors
import logging
from dataclasses import dataclass  # https://www.youtube.com/watch?v=vBH6GRJ1REM

logger = logging.getLogger(__name__)

__all__ = ["CommandException", "UserInputException", "MySQLException"]

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

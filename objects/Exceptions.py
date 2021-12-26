# Global Errors
import logging
from dataclasses import dataclass  # https://www.youtube.com/watch?v=vBH6GRJ1REM

logger = logging.getLogger(__name__)


@dataclass()
class CommandException(Exception):
    message: str


@dataclass()
class UserInputException(Exception):
    message: str

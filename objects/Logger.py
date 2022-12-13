import logging
import os
import pathlib
import platform
import sys

__all__: list[str] = [
    "discordLogger",
    "initializeLogging",
    "is_debugging",
]


def is_debugging() -> bool:
    if "bypass" in sys.argv:
        return False
    else:
        return "Windows" in platform.platform()


def discordLogger(name: str, level: int) -> logging.Logger:
    root_logger: logging.Logger = logging.getLogger("root")
    root_logger.setLevel(level=level)

    logger: logging.Logger = logging.getLogger(name=name)
    logger.setLevel(level=level)

    logging.debug(
        f"Created [{str(logger.name).upper()}] logger with [{logger.level}] level"
    )
    return logger


def initializeLogging():
    format_string: str = "[%(asctime)s] %(levelname)s :: %(name)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s"
    formatter: logging.Formatter = logging.Formatter(format_string)

    filename: pathlib.Path = pathlib.Path("log.log")
    full_path: str = os.path.join(filename.parent.resolve(), "logs", filename)

    _level: int = logging.DEBUG

    file_handler: logging.FileHandler = logging.FileHandler(
        filename=full_path, mode="a+"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level=_level)

    stream_handler: logging.StreamHandler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level=_level)

    logging.basicConfig(
        datefmt="%X %x",
        level=_level,
        encoding="utf-8",
        handlers=[file_handler, stream_handler],
    )

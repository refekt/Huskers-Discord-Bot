import logging
import os
import pathlib
import sys

__all__: list[str] = ["discordLogger"]


def discordLogger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logger: logging.Logger = logging.getLogger(name=name)
    logger.setLevel(level=level)

    format_string: str = "[%(asctime)s] %(levelname)s :: %(name)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s"
    formatter: logging.Formatter = logging.Formatter(format_string)

    filename: pathlib.Path = pathlib.Path("log.log")
    full_path: str = os.path.join(filename.parent.resolve(), "logs", filename)

    file_handler: logging.FileHandler = logging.FileHandler(
        filename=full_path, mode="a"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level=level)

    stream_handler: logging.StreamHandler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level=level)

    logging.basicConfig(
        datefmt="%X %x",
        level=level,
        encoding="utf-8",
        handlers=[file_handler, stream_handler],
    )

    logging.debug(
        f"Created [{str(logger.name).upper()}] logger with [{logger.level}] level"
    )
    return logger

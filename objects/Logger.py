import inspect
import logging
import os
import pathlib
import sys

__all__ = ["discordLogger"]

from logging.handlers import RotatingFileHandler

from helpers.misc import getModuleMethod


def discordLogger(name: str, level: int = logging.INFO) -> logging.Logger:
    module, method = getModuleMethod(inspect.stack())
    path = pathlib.Path(f"{module}.log")
    full_path = os.path.join(path.parent.resolve(), "logs", path)

    format_string = "[%(asctime)s] %(levelname)s :: %(name)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s"
    formatter = logging.Formatter(format_string)

    handler = RotatingFileHandler(filename=full_path, mode="a", maxBytes=2_621_440)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logging.basicConfig(
        format=format_string,
        datefmt="%X %x",
        level=level,
        encoding="utf-8",
        stream=sys.stdout,
    )

    for _ in logger.handlers[:]:
        pass

    return logger

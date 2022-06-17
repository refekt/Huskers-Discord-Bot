import logging
import pathlib
import platform
import sys

__all__ = ["discordLogger"]


def discordLogger(name: str, level: int = logging.INFO) -> logging.Logger:
    format_string = "[%(asctime)s] %(levelname)s :: %(name)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s"
    formatter = logging.Formatter(format_string)
    logging.basicConfig(
        format=format_string,
        datefmt="%X %x",
        level=level,
        encoding="utf-8",
        stream=sys.stdout,
    )
    logger = logging.getLogger(name)
    path = pathlib.Path("bot.log")
    if "Windows" in platform.platform():
        handler = logging.FileHandler(
            filename=f"{path.parent.absolute()}\\{path}",
            mode="a",
        )
    elif "Linux" in platform.platform():
        handler = logging.FileHandler(
            filename=f"{path.parent.absolute()}/{path}",
            mode="a",
        )
    else:
        handler = None
    if handler:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

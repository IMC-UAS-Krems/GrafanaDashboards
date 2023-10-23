import logging
import sys
from copy import copy
from typing import Literal, Optional

"""
Configs logging for the Dash app by creating a 'dash_app' logger

Notes
-----
Formatter was taken from uvicorn logging config
"""

grafana_logger = logging.getLogger("grafana_dashboards")
grafana_logger.setLevel(logging.INFO)

resolver_logger = logging.getLogger("grafana_dashboards.types_resolver")
resolver_logger.setLevel(logging.INFO)


def colorize(message: str, color: str) -> str:
    if color == "red":
        return "\033[91m" + message + "\033[0m"

    if color == "green":
        return "\033[92m" + message + "\033[0m"

    if color == "yellow":
        return "\033[93m" + message + "\033[0m"

    if color == "blue":
        return "\033[94m" + message + "\033[0m"

    if color == "cyan":
        return "\033[96m" + message + "\033[0m"

    if color == "bright_red":
        return "\033[31;1m" + message + "\033[0m"

    return message


class ColourizedFormatter(logging.Formatter):
    """
    A custom log formatter class that:

    * Outputs the LOG_LEVEL with an appropriate color.
    * If a log call includes an `extras={"color_message": ...}` it will be used
      for formatting the output, instead of the plain text message.
    """

    level_name_colors = {
        5: lambda level_name: colorize(str(level_name), "blue"),
        logging.DEBUG: lambda level_name: colorize(str(level_name), "cyan"),
        logging.INFO: lambda level_name: colorize(str(level_name), "green"),
        logging.WARNING: lambda level_name: colorize(str(level_name), "yellow"),
        logging.ERROR: lambda level_name: colorize(str(level_name), "red"),
        logging.CRITICAL: lambda level_name: colorize(str(level_name), "bright_red"),
    }

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: Literal["%", "{", "$"] = "%",
    ):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        def default(level_name: str) -> str:
            return str(level_name)

        func = self.level_name_colors.get(level_no, default)
        return func(level_name)

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        seperator = " " * (8 - len(recordcopy.levelname))
        levelname = self.color_level_name(levelname, recordcopy.levelno)
        if "color_message" in recordcopy.__dict__:
            recordcopy.msg = recordcopy.__dict__["color_message"]
            recordcopy.__dict__["message"] = recordcopy.getMessage()
        recordcopy.__dict__["levelprefix"] = levelname + ":" + seperator
        return super().formatMessage(recordcopy)


stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(
    ColourizedFormatter(
        "%(levelprefix)s [%(name)s] %(module)s:%(funcName)s:%(lineno)d - %(message)s"
    )
)
grafana_logger.addHandler(stream_handler)
resolver_logger.addHandler(stream_handler)

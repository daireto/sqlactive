"""Logger for testing."""

import logging

from colorlog import ColoredFormatter


LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s'


formatter = ColoredFormatter(LOG_FORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)


def get_logger(name: str | None = None):
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(stream)
    return logger


logger = get_logger('sqlactive.tests')

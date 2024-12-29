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


def show_preview(logger: logging.Logger):
    logger.debug('A quirky message only developers care about')
    logger.info('Curious users might want to know this')
    logger.warning('Something is wrong and any user should be informed')
    logger.error('Serious stuff, this is red for a reason')
    logger.critical('OH NO everything is on fire')


logger = get_logger('sqlactive.tests')

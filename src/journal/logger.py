import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# --------------------------- BEGIN LOGGER --------------------------- #

logger = logging.getLogger('journal')
logger.setLevel(logging.DEBUG)

log_file_Path = Path('logs', os.getlogin(), 'journal.log').resolve()
log_file_Path.parent.mkdir(parents=True, exist_ok=True)

# create file handler which logs even debug messages
fh = RotatingFileHandler(str(log_file_Path), mode='a', maxBytes=1024 * 1024)
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()  # create console handler
ch.setLevel(logging.WARNING)

# create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    '%Y-%m-%d %H:%M:%S',  # dont't want milliseconds
)
# add formatter to the handler(s)
ch.setFormatter(formatter)
fh.setFormatter(formatter)

logger.addHandler(ch)  # add the handler to the logger
logger.addHandler(fh)

# --------------------------- END LOGGER --------------------------- #

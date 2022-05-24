import logging
import os
from CodeDocs_backend.settings import BASE_DIR

LOGGER_FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def create_logger(logger_name, level=logging.INFO):
    # create path
    path = os.path.join(BASE_DIR, "logs", f"{logger_name}.log")
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    # file handler
    fh = logging.FileHandler(path, encoding='utf-8')
    formatter = logging.Formatter(LOGGER_FORMATTER)
    fh.setFormatter(formatter)

    # create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(fh)
    return logger

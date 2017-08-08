import logging
from colorlog import ColoredFormatter


log_level = logging.DEBUG
logger_format = "[%(log_color)s%(asctime)s %(levelname)s%(reset)s] %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(log_level)
formatter = ColoredFormatter(
    logger_format,
    datefmt="%H:%M:%S",
    log_colors={
      "DEBUG": "bold,cyan",
      "INFO": "green",
      "WARNING": "yellow",
      "ERROR": "red",
      "CRITICAL": "bold,red"
    }
)
stream = logging.StreamHandler()
stream.setLevel(log_level)
stream.setFormatter(formatter)
LOGGER = logging.getLogger('consolelog')
LOGGER.setLevel(log_level)
LOGGER.addHandler(stream)
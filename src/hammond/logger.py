import logging

import coloredlogs

other_level = logging.INFO
logging.basicConfig(level=logging.INFO)
logging.getLogger("discord").setLevel(logging.INFO)
coloredlogs.install(level=logging.INFO)

our_level = logging.DEBUG
logger = logging.getLogger("hammond")
coloredlogs.install(level=our_level, logger=logger)
logger.setLevel(our_level)

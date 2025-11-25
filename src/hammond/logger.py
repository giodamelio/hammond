import logging

import coloredlogs

# Create hammond logger at DEBUG level with coloredlogs
logger = logging.getLogger("hammond")
logger.setLevel(logging.DEBUG)
coloredlogs.install(level=logging.DEBUG, logger=logger)

# Create discord logger at INFO level with coloredlogs
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.INFO)
coloredlogs.install(level=logging.INFO, logger=discord_logger)

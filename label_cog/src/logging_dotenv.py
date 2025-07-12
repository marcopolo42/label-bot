import logging
import os
import dotenv
import sys
import colorlog

dotenv.load_dotenv()


def setup_logger(name, level=logging.INFO):
    """
    Set up a logger with a colored stream handler.

    Args:
        name (str): The name of the logger.
        level: The logging level (default is INFO).

    Returns:
        logging.Logger: Configured logger object.
    """
    # Define color scheme for different log levels
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }

    # Create a color formatter
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s():\n%(reset)s%(message)s',
        log_colors=log_colors,
        secondary_log_colors={
            'message': {
                'ERROR': 'bold_red',
                'CRITICAL': 'bold_red',
                'WARNING': 'bold_yellow'
            }
        }
    )

    # Set up a stream handler (logs to console)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # custom part
    environment = os.getenv('ENV')
    if environment == 'prod':
        print("Work environment is prod.")
        level = logging.INFO
    elif environment == 'dev':
        print("Work environment is dev.")
        level = logging.DEBUG
    else:
        print("Work environment is not set.")
        level = logging.DEBUG

    # Create the logger with the specified name and level
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(handler)

    return logger

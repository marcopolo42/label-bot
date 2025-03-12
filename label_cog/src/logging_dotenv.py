import logging
import os
import dotenv
import sys

dotenv.load_dotenv()


def setup_logger(name, level=logging.INFO):
    """
    Set up a logger with a stream handler.

    Args:
        name (str): The name of the logger.
        level: The logging level (default is INFO).

    Returns:
        logging.Logger: Configured logger object.
    """
    # Define a custom formatter including file, function, and line details
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s():\n    %(message)s'
    )

    # Set up a stream handler (logs to console)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # custom part
    environment = os.getenv('ENV')
    if environment == 'prod':
        level = logging.INFO
    elif environment == 'dev':
        print("Work environment set to dev in .env handler flush set to ensure logs are written instantly")
        level = logging.DEBUG
        handler.flush = lambda: handler.stream.flush()  # Ensure logs are written instantly
    else:
        print("Work environment not set in .env, Defaulting to debug logging level ")
        level = logging.DEBUG

    # Create the logger with the specified name and level
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

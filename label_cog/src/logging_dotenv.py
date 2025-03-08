import logging
import os
import dotenv
import sys

dotenv.load_dotenv()

environment = os.getenv('ENV')
if environment == 'prod':
    log_level = logging.INFO
elif environment == 'dev':
    log_level = logging.DEBUG
else:
    print("Work environment not set in .env, Defaulting to debug logging level ")
    log_level = logging.DEBUG

logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
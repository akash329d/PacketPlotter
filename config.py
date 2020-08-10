import os
from dotenv import load_dotenv
import distutils.util

load_dotenv(dotenv_path='config.ini')

class Config:
    PING_DESTINATION = os.getenv('PING_DESTINATION', '8.8.8.8')
    PING_SIZE = os.getenv('PING_SIZE', 32)
    PING_TIMEOUT = os.getenv('PING_TIMEOUT', 200)
    DEBUG = distutils.util.strtobool(os.getenv('DEBUG', 'False'))

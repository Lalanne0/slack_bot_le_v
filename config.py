# Config values

import os
from dotenv import load_dotenv

load_dotenv()


SECRET_KEY = os.urandom(24)
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")
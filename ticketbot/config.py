import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHECK_INTERVAL_MINUTES = int(os.environ.get("CHECK_INTERVAL_MINUTES", "12"))
PROXY_ENABLED = os.environ.get("PROXY_ENABLED", "true").lower() == "true"
DB_PATH = BASE_DIR / os.environ.get("DB_PATH", "data/subscriptions.db")

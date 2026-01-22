import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ALLOWED_CHAT_IDS = set(
    int(x.strip()) for x in (os.getenv("ALLOWED_CHAT_IDS", "")).split(",") if x.strip()
)

DADATA_TOKEN = os.getenv("DADATA_TOKEN", "")
DADATA_SECRET = os.getenv("DADATA_SECRET", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

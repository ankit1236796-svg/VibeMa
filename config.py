import os

# Tera Bot Token variables se aayega
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Scraper ka URL seedha hardcode kar diya, ab environment variable ki zaroorat hi nahi!
PLAYWRIGHT_SCRAPER_URL = "https://loving-liberation-production-52a3.up.railway.app"

# Checking Intervals
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", 180))
STAGGER_INTERVAL_SECONDS = int(os.getenv("STAGGER_INTERVAL_SECONDS", 3))

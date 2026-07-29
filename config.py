import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "TERA_BOT_TOKEN_YAHAN_DAAL")
PLAYWRIGHT_SCRAPER_URL = os.getenv("PLAYWRIGHT_SCRAPER_URL", "http://localhost:8000")

# Checking Intervals
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", 180)) 
STAGGER_INTERVAL_SECONDS = int(os.getenv("STAGGER_INTERVAL_SECONDS", 3)) # Delay between each combo

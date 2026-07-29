import os
from dataclasses import dataclass

@dataclass
class Config:
    # Telegram
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID")

    # Apple
    COUNTRY: str = "in"
    BASE_URL: str = "https://www.apple.com/{country}/shop/retail/pickup-message"

    # Concurrency
    MAX_CONCURRENT_CHECKS: int = 5
    TIER1_TIMEOUT: int = 10
    TIER2_TIMEOUT: int = 60

    # Rate limiting
    REQUEST_DELAY: float = 0.5  # Seconds between requests
    RETRY_ATTEMPTS: int = 2

config = Config()

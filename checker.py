import asyncio
import httpx
import random
import logging
from config import PLAYWRIGHT_SCRAPER_URL

logger = logging.getLogger(__name__)

# Concurrency Limits
_tier1_api_semaphore = asyncio.Semaphore(4)  # Max 4 concurrent fast API calls
_tier2_playwright_semaphore = asyncio.Semaphore(2)  # Matches Playwright MAX_CONCURRENT_CHECKS

async def check_tier1_direct(url: str, pincode: str) -> dict:
    """Mock implementation of the fast zero-auth Apple API."""
    # Note: Extract actual SKU from URL/Page first in real scenario
    target_url = f"https://www.apple.com/in/shop/retail/pickup-message?parts.0=MOCK_SKU&location={pincode}"
    
    async with _tier1_api_semaphore:
        # Micro-jitter to prevent Akamai burst detection
        await asyncio.sleep(random.uniform(0.1, 1.5))
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(target_url)
            resp.raise_for_status()
            return resp.json()

async def check_tier2_playwright(url: str, pincode: str) -> dict:
    """Fallback to Playwright container."""
    async with _tier2_playwright_semaphore:
        async with httpx.AsyncClient(timeout=240.0) as client:
            resp = await client.post(
                f"{PLAYWRIGHT_SCRAPER_URL}/check-pickup-availability",
                json={"url": url, "pincode": pincode},
            )
            resp.raise_for_status()
            return resp.json()

async def fetch_pickup_availability(url: str, pincode: str) -> bool:
    """The smart fallback chain."""
    try:
        # Try Fast API
        data = await check_tier1_direct(url, pincode)
        logger.info(f"[Tier 1] Success for {pincode}")
        # Parse data here... return True/False based on Apple JSON
        return True 
    except Exception as e:
        logger.warning(f"[Tier 1] Failed for {pincode} ({e}) -> Falling back to Tier 2")
        
        try:
            # Try Playwright
            data = await check_tier2_playwright(url, pincode)
            logger.info(f"[Tier 2] Success for {pincode}")
            # Parse data here... return True/False
            return True
        except Exception as e_pw:
            logger.error(f"[Tier 2] Failed for {pincode} ({e_pw})")
            return False


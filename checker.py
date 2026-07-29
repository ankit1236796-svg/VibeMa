import httpx
import asyncio
import re
import logging
from bs4 import BeautifulSoup
import config

logger = logging.getLogger(__name__)

# Akamai ko khush rakhne ke liye concurrency limits
_tier1_api_semaphore = asyncio.Semaphore(4)
_playwright_fallback_semaphore = asyncio.Semaphore(2)

async def _extract_sku(url):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        m = re.search(r'"partNumber"\s*:\s*"([A-Z0-9]{5,14}/A)"', resp.text)
        if m:
            return m.group(1)
    except Exception as e:
        logger.error(f"Error extracting SKU for {url}: {e}")
    return None

async def check_pickup_strictly(url, pincode):
    sku = await _extract_sku(url)
    if not sku:
        return {"status": "error", "message": "Product ka SKU nahi mila."}

    # --- TIER 1: FAST DIRECT HTTP API ---
    async with _tier1_api_semaphore:
        await asyncio.sleep(1.0) # Jitter delay bot manager bypass ke liye
        try:
            target = f"https://www.apple.com/in/shop/retail/pickup-message?parts.0={sku}&location={pincode}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(target)
            
            if resp.status_code == 200:
                data = resp.json()
                stores = data.get("body", {}).get("stores", [])
                if not stores:
                    return {"status": "oos"} # No stores near pincode
                
                available_stores = []
                for store in stores:
                    part_info = store.get("partsAvailability", {}).get(sku, {})
                    if part_info.get("pickupDisplay") in ("available", "eligible"):
                        available_stores.append(store.get("storeName"))
                
                if available_stores:
                    return {"status": "instock", "stores": available_stores}
                else:
                    return {"status": "oos"}
        except Exception as e:
            logger.warning(f"Tier 1 failed for pincode {pincode}: {e}. Fallback to Tier 2.")
    
    # --- TIER 2: PLAYWRIGHT FALLBACK ---
    if not config.PLAYWRIGHT_SCRAPER_URL:
         return {"status": "error", "message": "Tier 1 failed aur Playwright URL configured nahi hai."}
         
    async with _playwright_fallback_semaphore:
        try:
            async with httpx.AsyncClient(timeout=240.0) as client:
                resp = await client.post(
                    f"{config.PLAYWRIGHT_SCRAPER_URL}/check-pickup-availability",
                    json={"url": url, "pincode": pincode}
                )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("available"):
                    stores = [s.get("store_name") for s in data.get("matching_stores", [])]
                    return {"status": "instock", "stores": stores}
                else:
                    return {"status": "oos"}
            else:
                return {"status": "error", "message": f"Playwright returned {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Tier 2 (Playwright) failed: {e}"}

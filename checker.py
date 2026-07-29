import httpx
import asyncio
import re
import json
import logging
from bs4 import BeautifulSoup
import config

logger = logging.getLogger(__name__)

# Akamai ko khush rakhne ke liye concurrency limits
_tier1_api_semaphore = asyncio.Semaphore(4)
_playwright_fallback_semaphore = asyncio.Semaphore(2)

async def _extract_sku(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        sku = None
        
        # Method 1: JSON-LD Extraction
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                item = data[0] if isinstance(data, list) else data
                sku = item.get("sku")
                if not sku and "offers" in item:
                    offers = item["offers"]
                    if isinstance(offers, dict):
                        sku = offers.get("sku")
                    elif isinstance(offers, list) and len(offers) > 0:
                        sku = offers[0].get("sku")
                if sku: 
                    break
            except:
                pass
                
        # Method 2: Regex Fallback
        if not sku:
            match = re.search(r'"partNumber"\s*:\s*"([A-Z0-9]{5,14}/[A-Z])"', resp.text)
            if match:
                sku = match.group(1)
        
        return sku
    except Exception as e:
        logger.error(f"Error extracting SKU for {url}: {e}")
        return None

async def check_pickup_strictly(url, pincode):
    sku = await _extract_sku(url)
    
    # --- TIER 1: FAST DIRECT HTTP API ---
    # Sirf tab chalega agar SKU successfuly nikal gaya ho
    if sku:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        async with _tier1_api_semaphore:
            await asyncio.sleep(1.0) # Jitter delay
            try:
                target = f"https://www.apple.com/in/shop/retail/pickup-message?parts.0={sku}&location={pincode}"
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(target, headers=headers)
                
                if resp.status_code == 200:
                    data = resp.json()
                    stores = data.get("body", {}).get("stores", [])
                    if not stores:
                        return {"status": "oos"}
                    
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
    else:
        logger.warning(f"SKU nahi mila for {url}. Direct Playwright (Tier 2) par jaa raha hu.")

    # --- TIER 2: PLAYWRIGHT FALLBACK ---
    # Agar SKU nahi mila (Akamai block) YA Tier 1 api fail ho gayi, toh ye chalega!
    if not config.PLAYWRIGHT_SCRAPER_URL:
         return {"status": "error", "message": "Tier 1 blocked, and Playwright Scraper URL is not configured."}
         
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
                return {"status": "error", "message": f"Playwright returned HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Tier 2 (Playwright) failed: {e}"}

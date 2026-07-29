import httpx
import re
import json
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

async def check_pickup_strictly(url: str, pincode: str) -> dict:
    """
    Sirf in-store pickup check karega. Delivery status ko ignore karega.
    Return shape: {"status": "instock" | "oos" | "error", "stores": [...], "message": "..."}
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # ---------------------------------------------------------
        # STEP 1: URL se SKU extract karna (e.g., MG6N4HN/A)
        # ---------------------------------------------------------
        sku = None
        try:
            resp = await client.get(url, headers=headers)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # JSON-LD method
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
            
            # Regex Fallback method
            if not sku:
                match = re.search(r'"partNumber"\s*:\s*"([A-Z0-9]{5,14}/[A-Z])"', resp.text)
                if match:
                    sku = match.group(1)

        except Exception as e:
            logging.error(f"SKU fetch fail hua: {e}")
            return {"status": "error", "message": "Product page fetch nahi ho paya."}

        if not sku:
            return {"status": "error", "message": "Is URL se SKU extract nahi ho paya."}

        logging.info(f"Target SKU for {pincode}: {sku}")

        # ---------------------------------------------------------
        # STEP 2: Strict Apple Pickup API Check (No Delivery Fallback)
        # ---------------------------------------------------------
        api_url = "https://www.apple.com/in/shop/retail/pickup-message"
        params = {
            "parts.0": sku,
            "location": pincode
        }
        
        try:
            api_resp = await client.get(api_url, params=params, headers=headers)
            if api_resp.status_code != 200:
                return {"status": "error", "message": f"Apple API ne {api_resp.status_code} diya."}
            
            data = api_resp.json()
            stores = data.get("body", {}).get("stores", [])
            
            if not stores:
                # Agar us pincode ke paas koi Apple store nahi hai
                return {"status": "oos", "stores": []}
            
            available_stores = []
            for store in stores:
                part_info = store.get("partsAvailability", {}).get(sku, {})
                pickup_display = part_info.get("pickupDisplay", "")
                
                # Yahan hum STRICTLY check kar rahe hain
                if pickup_display in ("available", "eligible"):
                    available_stores.append(store.get("storeName", "Apple Store"))
            
            if available_stores:
                return {"status": "instock", "stores": available_stores}
            else:
                return {"status": "oos", "stores": []}
                
        except Exception as e:
            logging.error(f"API Check crash: {e}")
            return {"status": "error", "message": str(e)}

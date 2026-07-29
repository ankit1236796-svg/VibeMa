import aiohttp
import asyncio
import time
import logging
from typing import Optional, List
from .models import CheckResult, StoreAvailability
from config import config
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class AppleChecker:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_CHECKS)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.TIER1_TIMEOUT))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_pickup(self, sku: str, pincode: str) -> CheckResult:
        async with self.semaphore:
            return await self._check_with_retry(sku, pincode)

    async def _check_with_retry(self, sku: str, pincode: str, retry: int = 0) -> CheckResult:
        # Try Tier 1 first
        result = await self._tier1_check(sku, pincode)
        if result.success:
            return result

        # Retry Tier 1
        if retry < config.RETRY_ATTEMPTS:
            delay = (2 ** retry) + (time.time() % 1)  # Exponential backoff + jitter
            await asyncio.sleep(delay)
            return await self._check_with_retry(sku, pincode, retry + 1)

        # Fall back to Tier 2
        return await self._tier2_check(sku, pincode)

    async def _tier1_check(self, sku: str, pincode: str) -> CheckResult:
        start_time = time.time()
        url = config.BASE_URL.format(country=config.COUNTRY)
        params = {
            "parts.0": sku,
            "location": pincode
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return CheckResult(
                        sku=sku,
                        pincode=pincode,
                        tier="tier1",
                        success=False,
                        error=f"HTTP {response.status}",
                        response_time=time.time() - start_time
                    )

                data = await response.json()
                availability = self._parse_tier1_response(data, sku, pincode)

                return CheckResult(
                    sku=sku,
                    pincode=pincode,
                    tier="tier1",
                    success=True,
                    availability=availability,
                    response_time=time.time() - start_time
                )

        except Exception as e:
            return CheckResult(
                sku=sku,
                pincode=pincode,
                tier="tier1",
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )

    def _parse_tier1_response(self, data: dict, sku: str, pincode: str) -> List[StoreAvailability]:
        stores = data.get("body", {}).get("stores", [])
        results = []

        for store in stores:
            parts_availability = store.get("partsAvailability", {})
            sku_data = parts_availability.get(sku, {})

            results.append(StoreAvailability(
                store_id=store.get("storeId", "unknown"),
                store_name=store.get("storeName", "Unknown Store"),
                pincode=pincode,
                sku=sku,
                available=sku_data.get("pickupDisplay") == "available",
                pickup_display=sku_data.get("pickupDisplay", "unavailable")
            ))

        return results

    async def _tier2_check(self, sku: str, pincode: str) -> CheckResult:
        start_time = time.time()
        url = f"https://www.apple.com/{config.COUNTRY}/shop/buy-iphone/iphone-17/{sku}"

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # Critical for Akamai
                    args=["--disable-dev-shm-usage"]
                )
                context = await browser.new_context()
                page = await context.new_page()

                # Navigate to product page
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Type pincode with realistic keystrokes
                pincode_input = await page.query_selector('input[name="location"]')
                if pincode_input:
                    for char in pincode:
                        await pincode_input.type(char, delay=random.uniform(0.05, 0.2))
                    await page.wait_for_timeout(2000)  # Wait for XHR

                # Intercept the pickup-message XHR response
                response_data = await page.evaluate("""() => {
                    return new Promise((resolve) => {
                        const originalFetch = window.fetch;
                        window.fetch = async (...args) => {
                            const response = await originalFetch(...args);
                            if (args[0].includes('pickup-message')) {
                                response.clone().json().then(resolve);
                            }
                            return response;
                        };
                    });
                }""", timeout=10000)

                if response_data:
                    availability = self._parse_tier1_response(response_data, sku, pincode)
                    return CheckResult(
                        sku=sku,
                        pincode=pincode,
                        tier="tier2",
                        success=True,
                        availability=availability,
                        response_time=time.time() - start_time
                    )

                # Fallback: Parse DOM
                availability = await self._parse_tier2_dom(page, sku, pincode)
                return CheckResult(
                    sku=sku,
                    pincode=pincode,
                    tier="tier2",
                    success=True,
                    availability=availability,
                    response_time=time.time() - start_time
                )

        except Exception as e:
            return CheckResult(
                sku=sku,
                pincode=pincode,
                tier="tier2",
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )
        finally:
            if 'browser' in locals():
                await browser.close()

    async def _parse_tier2_dom(self, page, sku: str, pincode: str) -> List[StoreAvailability]:
        # Implement DOM parsing as fallback
        return []

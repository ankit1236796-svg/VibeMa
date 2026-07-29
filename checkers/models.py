from dataclasses import dataclass
from typing import Literal, Optional, List
from datetime import datetime

@dataclass
class StoreAvailability:
    store_id: str
    store_name: str
    pincode: str
    sku: str
    available: bool
    pickup_display: str  # "available", "unavailable", "ineligible"
    last_checked: datetime = datetime.now()

@dataclass
class CheckResult:
    sku: str
    pincode: str
    tier: Literal["tier1", "tier2"]
    success: bool
    availability: Optional[List[StoreAvailability]] = None
    error: Optional[str] = None
    response_time: Optional[float] = None

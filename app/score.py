from math import log1p
from typing import Optional

def deal_score(fb_price: Optional[float], avg_sold: Optional[float], count: int) -> Optional[float]:
    if fb_price is None or avg_sold is None:
        return None
    try:
        return round((avg_sold - fb_price) * log1p(max(0, count)), 2)
    except Exception:
        return None

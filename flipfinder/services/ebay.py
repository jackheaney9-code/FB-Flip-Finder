from typing import Optional, List
import httpx
import re

EBAY_SEARCH_URL = "https://www.ebay.ca/sch/i.html"


def clean_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9 ]+", " ", title)
    return " ".join(title.split())


async def sold_prices(keyword: str, limit: int = 20) -> List[float]:
    params = {
        "_nkw": keyword,
        "LH_Sold": "1",
        "LH_Complete": "1",
        "_ipg": str(limit),
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(EBAY_SEARCH_URL, params=params)
            r.raise_for_status()
        html = r.text
    except Exception:
        # Any HTTP / parsing error → no prices, caller will fall back to rules
        return []

    matches = re.findall(r'>(C\$|CA\$)?\s?([0-9,]+\.\d{2})<', html)

    prices: List[float] = []
    for _, p in matches:
        try:
            prices.append(float(p.replace(",", "")))
        except Exception:
            pass

    return prices


async def sold_median(keyword: str) -> Optional[float]:
    prices = await sold_prices(keyword, limit=50)
    if not prices:
        return None

    prices.sort()
    n = len(prices)
    mid = n // 2
    if n % 2 == 1:
        return prices[mid]
    return (prices[mid - 1] + prices[mid]) / 2

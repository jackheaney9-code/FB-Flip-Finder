import os, re, time, requests
from typing import List, Dict, Any, Optional
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()
EBAY_APP_ID = os.getenv("EBAY_APP_ID")
FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"
GLOBAL_ID = os.getenv("EBAY_GLOBAL_ID", "EBAY-ENCA")  # change to EBAY-US if you prefer

def _clean_query(text: str) -> str:
    t = text or ""
    t = re.sub(r"Pending\s*·\s*", "", t, flags=re.I)
    t = re.sub(r"[^\w\s\-\+\.]", " ", t)  # drop emojis/symbols
    t = re.sub(r"\s+", " ", t).strip()
    return t

def find_completed_items(title: str, max_results: int = 20) -> List[Dict[str, Any]]:
    if not EBAY_APP_ID:
        raise RuntimeError("Missing EBAY_APP_ID in environment")

    keywords = _clean_query(title)
    params = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "true",
        "GLOBAL-ID": GLOBAL_ID,
        "paginationInput.entriesPerPage": str(max_results),
        "keywords": keywords,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "sortOrder": "EndTimeSoonest",
    }

    last_err = None
    for attempt in range(3):
        try:
            r = requests.get(FINDING_URL, params=params, timeout=20)
            if 500 <= r.status_code < 600:
                last_err = Exception(f"eBay 5xx: {r.status_code}")
                time.sleep(0.8 * (attempt + 1))
                continue
            r.raise_for_status()
            data = r.json()
            items = (
                data.get("findCompletedItemsResponse", [{}])[0]
                    .get("searchResult", [{}])[0]
                    .get("item", [])
            )
            out: List[Dict[str, Any]] = []
            for it in items:
                selling = it.get("sellingStatus", [{}])[0]
                price = selling.get("currentPrice", [{}])[0].get("__value__", None)
                currency = selling.get("currentPrice", [{}])[0].get("@currencyId", "USD")
                title_i = it.get("title", [""])[0]
                view_url = it.get("viewItemURL", [""])[0]
                ended = it.get("listingInfo", [{}])[0].get("endTime", [""])[0]
                state = selling.get("sellingState", [""])[0]
                sold = state.lower() == "endedwithsales"
                try:
                    price_f = float(Decimal(str(price))) if price is not None else None
                except Exception:
                    price_f = None
                out.append({
                    "title": title_i,
                    "price": price_f,
                    "currency": currency,
                    "url": view_url,
                    "ended": ended,
                    "sold": sold,
                })
            return out
        except requests.RequestException as e:
            last_err = e
            time.sleep(0.8 * (attempt + 1))

    return []

def summarize_prices(items: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    prices = [i["price"] for i in items if i.get("price") is not None]
    if not prices:
        return {"low": None, "avg": None, "high": None, "count": 0}
    prices_sorted = sorted(prices)
    avg = sum(prices) / len(prices)
    return {"low": prices_sorted[0], "avg": avg, "high": prices_sorted[-1], "count": len(prices)}

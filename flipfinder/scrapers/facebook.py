# flipfinder/scrapers/facebook.py

import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

FACEBOOK_MARKETPLACE_BASE = "https://www.facebook.com/marketplace"

PRICE_RE = re.compile(r"^(?:CA\$|\$)?\s*([0-9][0-9.,]*)")


def _parse_card_text(text: str) -> Dict[str, Any]:
    """
    Parse inner_text() of a FB Marketplace card into price, title, location.

    Example:
        "CA$400\nMilwaukee m18 fuel 2 tool combo kit\nToronto, ON"
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    price = None
    title = ""
    location = None
    currency = "CA$"

    if lines:
        m = PRICE_RE.match(lines[0])
        if m:
            try:
                price = float(m.group(1).replace(",", ""))
            except ValueError:
                price = None

        if "CA$" in lines[0]:
            currency = "CA$"
        elif "$" in lines[0]:
            currency = "$"

        if len(lines) >= 2:
            title = lines[1]
        if len(lines) >= 3:
            location = lines[2]

    return {
        "price": price,
        "currency": currency,
        "title": title,
        "location": location,
    }


def _resolve_location_slug(location: Optional[str]) -> Optional[str]:
    """
    Map a human location string to a Marketplace URL slug.
    For now, we only care about Toronto.
    """
    if not location:
        return None

    loc = location.lower()
    # Very simple mapping: anything containing 'toronto' → 'toronto'
    if "toronto" in loc:
        return "toronto"

    # You can extend this later with other cities:
    # if "mississauga" in loc: return "mississauga_on"
    # if "oakville" in loc: return "oakville_on"

    return None


def search_marketplace(
    query: str,
    max_results: int = 30,
    radius_km: int = 50,
    location: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Scrape FB Marketplace search results.

    IMPORTANT CHANGE:
    - We no longer append 'Toronto, ON' to the query.
    - Instead, for Toronto, we hit /marketplace/toronto/search/?query=...
    """

    # Just the user query (no location text in the query itself)
    search_text = query.strip()
    url_query = quote_plus(search_text)

    location_slug = _resolve_location_slug(location)

    if location_slug:
        # Toronto-specific search path
        search_url = (
            f"{FACEBOOK_MARKETPLACE_BASE}/{location_slug}/search/?query={url_query}"
            f"&radiusKm={radius_km}"
        )
    else:
        # Fallback: generic search path
        search_url = (
            f"{FACEBOOK_MARKETPLACE_BASE}/search/?query={url_query}"
            f"&radiusKm={radius_km}"
        )

    print("[DEBUG] FB URL:", search_url)
    print("[DEBUG] Raw location input:", repr(location))
    print("[DEBUG] Resolved location slug:", repr(location_slug))

    items: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(search_url, timeout=60_000)
            page.wait_for_timeout(5_000)

            cards = page.locator('a[role="link"][href*="/marketplace/item/"]').all()
            print(f"[DEBUG] Found {len(cards)} raw FB cards")
        except PlaywrightTimeoutError:
            print("[ERROR] Timeout while loading FB search page")
            browser.close()
            return []

        for card in cards[:max_results]:
            href = card.get_attribute("href") or ""
            text = card.inner_text()

            parsed = _parse_card_text(text)
            card_location = parsed.get("location") or ""

            print(f"[DEBUG] Card location text: {card_location!r} (no post-filter)")

            # NO post-filter here: we rely on the /marketplace/toronto/... context
            # to bias results. We'll see if this actually yields GTA in practice.

            # Build full URL
            if href.startswith("/"):
                full_url = "https://www.facebook.com" + href
            else:
                full_url = href

            item = {
                "url": full_url,
                "title": parsed["title"],
                "price": parsed["price"],
                "currency": parsed["currency"],
                "location": parsed["location"],
                "description": None,
                "posted_at_text": None,
                "seller": None,
                "photos": None,
                "raw_html": None,
            }
            items.append(item)

        browser.close()

    print(f"[DEBUG] Kept {len(items)} items total")
    return items

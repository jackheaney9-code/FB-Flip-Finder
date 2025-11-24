import re
import sys
import subprocess
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)

FACEBOOK_MARKETPLACE_BASE = "https://www.facebook.com/marketplace"

PRICE_RE = re.compile(r"^(?:CA\$|\$)?\s*([0-9][0-9.,]*)")


def _parse_card_text(text: str) -> Dict[str, Any]:
    """
    Parse the inner_text() of a FB Marketplace card into
    price, title, location.

    Example pattern:
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


def _normalize_location_keywords(location: Optional[str]) -> List[str]:
    """
    Turn 'Toronto, ON' into ['toronto', 'on'] etc.
    """
    if not location:
        return []

    raw = location.lower()
    # Split on commas, slashes, dashes, pipes, and whitespace
    tokens = re.split(r"[,/|\-]\s*|\s+", raw)
    keywords = sorted({t for t in tokens if t})
    return keywords


def _location_matches(loc_text: Optional[str], keywords: List[str]) -> bool:
    """
    Check if the card's location text contains any of the keywords.
    If there are no keywords, we accept all locations.
    """
    if not keywords:
        return True  # no filtering

    if not loc_text:
        return False

    lt = loc_text.lower()
    for kw in keywords:
        if kw and kw in lt:
            return True
    return False


def _install_playwright_browsers_if_needed() -> None:
    """
    Try to install Chromium browsers at runtime if they are missing.
    This is mainly for Render, where the build step may not have
    installed them correctly.
    """
    try:
        print("[WARN] Playwright browsers missing. Installing chromium at runtime...")
        # Try with --with-deps first (works on many Linux environments)
        try:
            subprocess.check_call(
                [sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"]
            )
        except Exception:
            # Fallback without --with-deps
            subprocess.check_call(
                [sys.executable, "-m", "playwright", "install", "chromium"]
            )
        print("[DEBUG] Playwright chromium install completed.")
    except Exception as e:
        print("[ERROR] Failed to install Playwright browsers at runtime:", e)


def search_marketplace(
    query: str,
    max_results: int = 30,
    radius_km: int = 50,
    location: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Scrape Facebook Marketplace search results.

    If a location string is provided (e.g. 'Toronto, ON'), we bias the search
    query by appending it (e.g. 'macbook pro Toronto, ON') and then filter
    card locations by keywords derived from that string.

    Returns a list of dicts with at least:
      - url
      - title
      - price
      - currency
      - location
    """

    if location:
        search_text = f"{query} {location}"
    else:
        search_text = query

    url_query = quote_plus(search_text)

    search_url = (
        f"{FACEBOOK_MARKETPLACE_BASE}/search/?query={url_query}"
        f"&radiusKm={radius_km}"
    )

    print(f"[DEBUG] FB URL: {search_url}")
    print(f"[DEBUG] Raw location input: {location!r}")

    location_keywords = _normalize_location_keywords(location)
    print(f"[DEBUG] Location keywords used for filter: {location_keywords}")

    results: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        # --- Make sure the browser is installed / launch, with a runtime fallback ---
        try:
            browser = p.chromium.launch(headless=True)
        except PlaywrightError as e:
            if "Executable doesn't exist" in str(e):
                # Install browsers at runtime, then retry once
                _install_playwright_browsers_if_needed()
                browser = p.chromium.launch(headless=True)
            else:
                raise

        page = browser.new_page()

        try:
            page.goto(search_url, timeout=60_000)
            page.wait_for_timeout(5_000)

            cards = page.locator('a[role="link"][href*="/marketplace/item/"]').all()
        except PlaywrightTimeoutError:
            browser.close()
            return []

        print(f"[DEBUG] Found {len(cards)} raw FB cards")

        for card in cards[:max_results]:
            href = card.get_attribute("href") or ""
            text = card.inner_text()

            parsed = _parse_card_text(text)
            loc_text = parsed.get("location")

            print(f"[DEBUG] Card location text: {loc_text!r}")

            if not _location_matches(loc_text, location_keywords):
                print(f"[DEBUG] Skipping card with location {loc_text!r}")
                continue

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
            results.append(item)

        browser.close()

    print(f"[DEBUG] Kept {len(results)} items after location filter")
    return results

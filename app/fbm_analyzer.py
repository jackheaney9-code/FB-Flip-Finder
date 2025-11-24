import os, asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright
from sqlalchemy.exc import IntegrityError

from .db import SessionLocal
from .models import Listing
from .utils import parse_price

# Reuse a persistent browser profile so Facebook login is kept
USER_DATA_DIR = os.getenv("PLAYWRIGHT_USER_DATA_DIR", ".pw-fb-profile")
# Optional (not required now, but kept for future): storage_state.json
STORAGE_PATH = os.getenv("PLAYWRIGHT_STORAGE", "storage_state.json")

# Marketplace selectors (defensive, try a few)
SELECTORS: Dict[str, List[str]] = {
    "title": [
        'h1[dir="auto"]',
        'h1[data-ad-preview="message"]',
        'div[role="main"] h1',
        'h1'
    ],
    "price": [
        'div[role="heading"] span:has-text("$")',
        'span:has-text("$")'
    ],
    "location": [
        'div:has-text("Location") ~ div',
        'a[href*="maps.google"]',
        'div[role="main"] div[dir="auto"] a[href*="maps"]'
    ],
    "description": [
        'div[role="article"] div[dir="auto"]',
        'div[role="main"] div[dir="auto"]'
    ],
    "posted": [
        'span:has-text("Listed")',
        'div:has-text("Listed")'
    ],
    "image": [
        'img[src*="scontent"]',
        'img[referrerpolicy]',
        'img'
    ],
}

async def _first_text(page, selectors: List[str]) -> Optional[str]:
    for s in selectors:
        try:
            el = await page.query_selector(s)
            if el:
                txt = (await el.inner_text()).strip()
                if txt:
                    return txt
        except:
            pass
    return None

async def _first_image(page, selectors: List[str]) -> Optional[str]:
    for s in selectors:
        try:
            els = await page.query_selector_all(s)
            for el in els:
                src = await el.get_attribute("src")
                if src and not src.startswith("data:"):
                    return src
        except:
            pass
    return None

async def analyze_fbm_url(url: str, headless: bool = True) -> Dict[str, Any]:
    """Open a Marketplace item URL with Playwright and extract details."""
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        # Expand long descriptions if present
        try:
            see_more = await page.query_selector('div[role="button"]:has-text("See more")')
            if see_more:
                await see_more.click()
                await page.wait_for_timeout(400)
        except:
            pass

        title = await _first_text(page, SELECTORS["title"])
        price_text = await _first_text(page, SELECTORS["price"])
        location = await _first_text(page, SELECTORS["location"])
        description = await _first_text(page, SELECTORS["description"])
        posted = await _first_text(page, SELECTORS["posted"])
        image = await _first_image(page, SELECTORS["image"])
        price, currency = parse_price(price_text or "")

        raw_html = await page.content()
        await page.close()
        await ctx.close()

        return {
            "source": "facebook",
            "url": url,
            "title": title,
            "description": description,
            # IMPORTANT: cast to float so it’s JSON-serializable
            "price": float(price) if price is not None else None,
            "currency": (currency or "CAD"),
            "location": location,
            "posted_at_text": posted,
            "seller": None,
            "photos": [image] if image else None,
            "raw_html": raw_html,
        }

def save_listing(row: dict) -> int:
    """Persist a listing; return 1 if added, 0 if duplicate or failed."""
    db = SessionLocal()
    try:
        db.add(Listing(**row))
        db.commit()
        return 1
    except IntegrityError:
        db.rollback()
        return 0
    except Exception as e:
        db.rollback()
        print("Save error:", e)
        return 0
    finally:
        db.close()

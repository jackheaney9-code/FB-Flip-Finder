from typing import List, Optional
from sqlalchemy.orm import Session

from .. import models
from ..scrapers.facebook import search_marketplace


def run_facebook_search(
    db: Session,
    query: str,
    max_results: int,
    radius_km: int,
    location: Optional[str],
) -> List[int]:
    """
    Run a Facebook Marketplace search, upsert results into the DB,
    and return the list of listing IDs (new or updated).
    """

    # Default location: Toronto, ON
    effective_location = location or "Toronto, ON"

    print(
        f"[DEBUG] run_facebook_search: query={query!r}, "
        f"location={effective_location!r}, radius_km={radius_km}, max_results={max_results}"
    )

    items = search_marketplace(
        query=query,
        max_results=max_results,
        radius_km=radius_km,
        location=effective_location,
    )

    listing_ids: List[int] = []

    for item in items:
        url = item["url"]

        listing = (
            db.query(models.Listing)
            .filter(models.Listing.source == "facebook")
            .filter(models.Listing.url == url)
            .one_or_none()
        )

        if listing is None:
            # New listing
            listing = models.Listing(
                source="facebook",
                url=url,
                title=item.get("title") or "",
                price=item.get("price"),
                currency=item.get("currency") or "CAD",
                location=item.get("location"),
                description=item.get("description"),
            )
            db.add(listing)
            db.flush()  # get listing.id
            print(f"[DEBUG] Created new listing id={listing.id} url={url}")
        else:
            # Update existing listing fields
            listing.title = item.get("title") or listing.title
            listing.price = item.get("price") or listing.price
            listing.currency = item.get("currency") or listing.currency
            listing.location = item.get("location") or listing.location
            listing.description = item.get("description") or listing.description
            print(f"[DEBUG] Updated listing id={listing.id} url={url}")

        listing_ids.append(listing.id)

    db.commit()
    print(f"[DEBUG] Upserted {len(listing_ids)} Facebook listings")

    return listing_ids
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..services.comps import refresh_comps_for_listing_id
from ..scrapers.facebook import search_marketplace  # real Playwright scraper


router = APIRouter(prefix="/scrape", tags=["scrape"])


class FacebookScrapeRequest(BaseModel):
    query: str
    location: Optional[str] = None
    min_profit: float = 150.0
    min_roi: float = 0.35
    max_results: int = 30
    radius_km: int = 50  # default search radius


def run_facebook_search(
    db: Session,
    query: str,
    max_results: int,
    radius_km: int,
    location: Optional[str],
) -> List[int]:
    """
    Call the REAL Playwright scraper and upsert rows into `listings`.

    - Uses search_marketplace(query, max_results, radius_km, location).
    - If an item has no URL, we generate a synthetic one so the row can still
      be saved and won't break the UNIQUE(source, url) constraint.
    """

    items = search_marketplace(
        query=query,
        max_results=max_results,
        radius_km=radius_km,
        location=location,
    )
    listing_ids: List[int] = []

    now_ts = int(datetime.utcnow().timestamp())

    for idx, item in enumerate(items):
        raw_url = item.get("url")

        # If no URL provided by scraper, synthesize a unique one
        if raw_url:
            url = raw_url
        else:
            safe_query = query.replace(" ", "_")
            url = f"fb-debug://{safe_query}/{now_ts}/{idx}"

        # Check if listing already exists for this (source, url)
        existing = (
            db.query(models.Listing)
            .filter_by(source="facebook", url=url)
            .first()
        )

        if existing:
            listing = existing
            # Update some useful fields
            if item.get("title"):
                listing.title = item["title"]
            if item.get("price") is not None:
                listing.price = item["price"]
            if item.get("currency"):
                listing.currency = item["currency"]
            if item.get("location"):
                listing.location = item["location"]
            if item.get("posted_at_text"):
                listing.posted_at_text = item["posted_at_text"]
            if item.get("seller"):
                listing.seller = item["seller"]
            if item.get("raw_html"):
                listing.raw_html = item["raw_html"]
            if item.get("photos") is not None:
                listing.photos = item["photos"]
        else:
            listing = models.Listing(
                source="facebook",
                url=url,
                title=item.get("title") or "",
                description=item.get("description"),
                price=item.get("price"),
                currency=item.get("currency") or "CA$",
                location=item.get("location"),
                posted_at_text=item.get("posted_at_text"),
                seller=item.get("seller"),
                photos=item.get("photos"),
                raw_html=item.get("raw_html"),
                created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            )
            db.add(listing)

        # Ensure it has an ID before we run comps later
        db.flush()
        listing_ids.append(listing.id)

    db.commit()
    return listing_ids


@router.post("/facebook")
def scrape_facebook(
    req: FacebookScrapeRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Facebook scrape endpoint:

      1. Uses Playwright scraper to fetch items.
      2. Upserts them into `listings`.
      3. Runs comps on each listing.
      4. Filters by min_profit / min_roi for the `profits` dict.
    """

    listing_ids: List[int] = run_facebook_search(
        db=db,
        query=req.query,
        max_results=req.max_results,
        radius_km=req.radius_km,
        location=req.location,
    )

    profits: Dict[int, Any] = {}

    for lid in listing_ids:
        comp = refresh_comps_for_listing_id(db, lid) or {}
        if not comp.get("success"):
            continue

        est_profit = float(comp.get("estimated_profit", 0.0))
        roi = float(comp.get("roi", 0.0))

        if est_profit >= req.min_profit and roi >= req.min_roi:
            profits[lid] = comp

    return {
        "found": len(listing_ids),
        "inserted": len(listing_ids),
        "skipped_existing": 0,
        "created_ids": listing_ids,
        "emails_sent": 0,
        "profits": profits,
    }


__all__ = ["router"]

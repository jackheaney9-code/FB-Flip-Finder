from pathlib import Path
from typing import List

from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .db import get_db
from . import models
from .routers.facebook import router as facebook_router


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="FlipFinder")

# Mount the Facebook scraper API
app.include_router(facebook_router)

# Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/")
def root(
    request: Request,
    min_profit: float = 150.0,
    min_roi: float = 0.35,
    db: Session = Depends(get_db),
):
    """
    Deals dashboard.

    - Shows rows from listings where is_deal == 1
    - Filters by min_profit and min_roi
    - Passes them into dashboard.html as `deals`
    """

    # Query deals from DB
    rows: List[models.Listing] = (
        db.query(models.Listing)
        .filter(
            models.Listing.is_deal == True,  # only flagged deals
            models.Listing.profit >= min_profit,
            models.Listing.roi >= min_roi,
        )
        .order_by(models.Listing.id.desc())
        .limit(200)
        .all()
    )

    # Normalize rows to simple dicts for the template
    deals = []
    for row in rows:
        deals.append(
            {
                "id": row.id,
                "title": row.title,
                "url": row.url,
                "price": float(row.price or 0.0) if row.price is not None else 0.0,
                "estimated_resale": float(getattr(row, "estimated_resale", 0.0) or 0.0),
                "profit": float(getattr(row, "profit", 0.0) or 0.0),
                "roi": float(getattr(row, "roi", 0.0) or 0.0),
                "source": row.source,
                "created_at": row.created_at,
            }
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "deals": deals,
            "min_profit": min_profit,
            "min_roi": min_roi,
        },
    )

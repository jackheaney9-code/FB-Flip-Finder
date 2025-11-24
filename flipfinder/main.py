from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from .db import get_db, init_db
from . import models
from .routers import facebook as facebook_router

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI()
app.include_router(facebook_router.router)


@app.on_event("startup")
def on_startup():
    """
    Ensure the database schema exists when the app starts.
    On Render, this will create flipfinder.db and all tables
    if they are missing.
    """
    init_db()


@app.get("/", response_class=HTMLResponse)
def root(
    request: Request,
    min_profit: float = 150.0,
    min_roi: float = 0.35,
    radius_km: int = 50,
    db=Depends(get_db),
):
    # Extra safety: also ensure schema exists on first request.
    # This is cheap and idempotent for SQLite.
    init_db()

    deals = (
        db.query(models.Listing)
        .filter(models.Listing.is_deal == True)
        .filter(models.Listing.profit >= min_profit)
        .filter(models.Listing.roi >= min_roi)
        .order_by(models.Listing.created_at.desc())
        .limit(50)
        .all()
    )

    recent = (
        db.query(models.Listing)
        .order_by(models.Listing.created_at.desc())
        .limit(50)
        .all()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "deals": deals,
            "recent": recent,
            "min_profit": min_profit,
            "min_roi": min_roi,
            "radius_km": radius_km,
        },
    )

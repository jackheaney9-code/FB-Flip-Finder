from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Listing
from ..services.comps import refresh_comps_for_listing_id

router = APIRouter()

@router.post("/listing/{listing_id}/refresh_comps")
def refresh_comps(listing_id: int, db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return refresh_comps_for_listing_id(db, listing_id)

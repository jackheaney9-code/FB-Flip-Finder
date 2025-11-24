from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import Listing  # assumes you have a Listing model

def intake_listings(db: Session, items: list[dict]) -> tuple[list[int], int]:
    created_ids: list[int] = []
    skipped = 0
    for it in items:
        existing = db.execute(
            select(Listing.id).where(
                Listing.source == it["source"],
                Listing.external_id == it["external_id"]
            )
        ).scalar_one_or_none()
        if existing:
            skipped += 1
            continue
        stmt = insert(Listing).values(
            source=it["source"],
            external_id=it["external_id"],
            source_url=it["source_url"],
            url=it.get("source_url") or "",  # url is NOT NULL in DB
            title=it["title"],
            price=it["price"],
            currency=it["currency"],
            location=it["location"],
            posted_at=it["posted_at"],
        )
        try:
            res = db.execute(stmt)
            db.commit()
            new_id = res.lastrowid
            if not new_id:
                new_id = db.execute(select(Listing.id).order_by(Listing.id.desc())).scalar_one()
            created_ids.append(new_id)
        except IntegrityError:
            db.rollback()
            skipped += 1
    return created_ids, skipped

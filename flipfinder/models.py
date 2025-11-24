from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Float,
    DateTime,
)
from .db import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)
    url = Column(String(800), nullable=False)
    title = Column(String(400))
    description = Column(Text)
    price = Column(Numeric(12, 2))
    currency = Column(String(10))
    location = Column(String(200))
    posted_at_text = Column(String(120))
    seller = Column(String(200))
    photos = Column(Text)       # JSON stored as text
    raw_html = Column(Text)
    created_at = Column(String) # your DB uses TEXT for this
    label = Column(Text)
    note = Column(Text)
    distance_km = Column(Float)
    external_id = Column(String)
    source_url = Column(String)
    posted_at = Column(DateTime)

    # 💰 Analytics / comps fields (already exist in DB)
    estimated_resale = Column(Numeric)  # estimated_resale NUMERIC
    profit = Column(Numeric)           # profit NUMERIC
    roi = Column(Float)                # roi NUMERIC/REAL
    is_deal = Column(Integer)          # is_deal INTEGER (0/1)

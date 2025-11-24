from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, UniqueConstraint, JSON
from .db import Base

class Listing(Base):
    __tablename__ = "listings"
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)
    url = Column(String(800), nullable=False)
    created_at = Column(DateTime, nullable=True)
    label = Column(String(32), nullable=True)
    note = Column(Text, nullable=True)


    title = Column(String(400), nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12,2), nullable=True)
    currency = Column(String(10), nullable=True)
    location = Column(String(200), nullable=True)
    posted_at_text = Column(String(120), nullable=True)
    seller = Column(String(200), nullable=True)
    photos = Column(JSON, nullable=True)
    raw_html = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint('source', 'url', name='uq_source_url'),)

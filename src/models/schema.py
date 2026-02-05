"""
Pydantic models for Mordor Intelligence report data.
Schema TBD after mitmproxy analysis.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class MarketSize(BaseModel):
    value: Optional[Decimal] = None
    unit: Optional[str] = None  # "Billion", "Trillion"
    year: Optional[int] = None
    currency: str = "USD"

class MajorPlayer(BaseModel):
    name: str
    rank: Optional[int] = None

class Report(BaseModel):
    """Core report model - fields TBD after API analysis."""
    slug: str
    title: str
    url: str

    # Time periods
    study_period_start: Optional[int] = None
    study_period_end: Optional[int] = None

    # Market sizing
    market_size_current: Optional[MarketSize] = None
    market_size_forecast: Optional[MarketSize] = None
    cagr_percent: Optional[Decimal] = None

    # Geography
    region: Optional[str] = None
    countries: Optional[List[str]] = None

    # Players
    major_players: Optional[List[MajorPlayer]] = None

    # Metadata
    page_last_updated: Optional[date] = None
    scraped_at: datetime

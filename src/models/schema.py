"""
Pydantic models for Mordor Intelligence report data.
Full schema for 153 payment market reports with versioning and change tracking.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
import json
import hashlib


class MarketSize(BaseModel):
    """Market size with value, unit, year, and currency."""
    value: Optional[Decimal] = None
    unit: Optional[str] = None  # "Billion", "Trillion"
    year: Optional[int] = None
    currency: str = "USD"


class SegmentData(BaseModel):
    """Segment information with name, share, and growth."""
    name: str
    share_percent: Optional[Decimal] = None
    cagr_percent: Optional[Decimal] = None


class FAQPair(BaseModel):
    """FAQ question-answer pair."""
    question: str
    answer: str


class Report(BaseModel):
    """Complete report model with all 153 payment market report fields."""

    # Identity
    slug: str = Field(..., description="URL-friendly identifier")
    title: str = Field(..., description="Report title")
    url: str = Field(..., description="Report URL")
    description: Optional[str] = None

    # Market Sizing - Current
    market_size_current_value: Optional[Decimal] = None
    market_size_current_unit: Optional[str] = None  # "Billion", "Trillion"
    market_size_current_year: Optional[int] = None
    market_size_current_currency: str = "USD"

    # Market Sizing - Forecast
    market_size_forecast_value: Optional[Decimal] = None
    market_size_forecast_unit: Optional[str] = None
    market_size_forecast_year: Optional[int] = None
    market_size_forecast_currency: str = "USD"

    # Growth metrics
    cagr_percent: Optional[Decimal] = None

    # Time periods
    study_period_start: Optional[int] = None
    study_period_end: Optional[int] = None
    temporal_coverage: Optional[str] = None

    # Geography
    region: Optional[str] = None
    spatial_coverage: Optional[str] = None
    fastest_growing_country: Optional[str] = None
    fastest_growing_country_cagr: Optional[Decimal] = None

    # Leading segment
    leading_segment_name: Optional[str] = None
    leading_segment_share_percent: Optional[Decimal] = None
    leading_segment_cagr: Optional[Decimal] = None

    # Cloud/Deployment
    cloud_share_percent: Optional[Decimal] = None
    cloud_share_year: Optional[int] = None

    # Segments (stored as JSON strings)
    transaction_types: Optional[List[str]] = None
    components: Optional[List[str]] = None
    deployment_types: Optional[List[str]] = None
    enterprise_sizes: Optional[List[str]] = None
    end_user_industries: Optional[List[str]] = None
    geographies: Optional[List[str]] = None

    # Players
    major_players: Optional[List[str]] = None

    # Page metadata
    page_date_published: Optional[datetime] = None
    page_date_modified: Optional[datetime] = None

    # FAQ and images
    faq_questions_answers: Optional[List[FAQPair]] = None
    image_urls: Optional[List[str]] = None

    # Tracking
    content_hash: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    version_count: int = 1

    def compute_content_hash(self) -> str:
        """Compute SHA256 hash of report content (excluding scraped_at and tracking fields)."""
        content_dict = self.model_dump(exclude={
            'scraped_at', 'first_seen_at', 'last_updated_at',
            'content_hash', 'version_count'
        })
        # Convert to JSON with sorted keys for deterministic hashing
        content_json = json.dumps(content_dict, sort_keys=True, default=str)
        return hashlib.sha256(content_json.encode()).hexdigest()

    def get_changed_fields(self, other: 'Report') -> Optional[List[str]]:
        """Compare with another Report and return list of changed fields."""
        if other is None:
            return None

        changed = []
        exclude_fields = {'scraped_at', 'first_seen_at', 'last_updated_at', 'content_hash', 'version_count'}

        for field in self.model_fields.keys():
            if field in exclude_fields:
                continue

            self_value = getattr(self, field)
            other_value = getattr(other, field)

            if self_value != other_value:
                changed.append(field)

        return changed if changed else None


class ReportVersion(BaseModel):
    """Historical snapshot of a report at a specific version."""
    version_id: Optional[int] = None
    report_id: int
    version_number: int

    # Full snapshot of all report fields
    slug: str
    title: str
    url: str
    description: Optional[str] = None

    market_size_current_value: Optional[Decimal] = None
    market_size_current_unit: Optional[str] = None
    market_size_current_year: Optional[int] = None
    market_size_current_currency: str = "USD"

    market_size_forecast_value: Optional[Decimal] = None
    market_size_forecast_unit: Optional[str] = None
    market_size_forecast_year: Optional[int] = None
    market_size_forecast_currency: str = "USD"

    cagr_percent: Optional[Decimal] = None
    study_period_start: Optional[int] = None
    study_period_end: Optional[int] = None
    temporal_coverage: Optional[str] = None

    region: Optional[str] = None
    spatial_coverage: Optional[str] = None
    fastest_growing_country: Optional[str] = None
    fastest_growing_country_cagr: Optional[Decimal] = None

    leading_segment_name: Optional[str] = None
    leading_segment_share_percent: Optional[Decimal] = None
    leading_segment_cagr: Optional[Decimal] = None

    cloud_share_percent: Optional[Decimal] = None
    cloud_share_year: Optional[int] = None

    transaction_types: Optional[List[str]] = None
    components: Optional[List[str]] = None
    deployment_types: Optional[List[str]] = None
    enterprise_sizes: Optional[List[str]] = None
    end_user_industries: Optional[List[str]] = None
    geographies: Optional[List[str]] = None

    major_players: Optional[List[str]] = None

    page_date_published: Optional[datetime] = None
    page_date_modified: Optional[datetime] = None
    faq_questions_answers: Optional[List[FAQPair]] = None
    image_urls: Optional[List[str]] = None

    # Version metadata
    content_hash: str
    snapshot_reason: str  # "new_report", "field_change"
    changed_fields: Optional[List[str]] = None
    scraped_at: datetime


class ScrapeLogEntry(BaseModel):
    """Log entry for a single scrape attempt."""
    log_id: Optional[int] = None
    run_id: str  # UUID per run
    report_url: str
    report_slug: Optional[str] = None

    # Status
    status: str  # "success", "error", "skipped"
    status_message: Optional[str] = None
    error_type: Optional[str] = None

    # HTTP metrics
    http_status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    html_size_bytes: Optional[int] = None

    # Results
    fields_extracted: Optional[int] = None
    fields_changed: Optional[int] = None
    version_created: bool = False

    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[Decimal] = None

    # Metadata
    retry_count: int = 0

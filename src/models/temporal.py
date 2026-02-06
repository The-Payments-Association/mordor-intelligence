"""
Temporal data models for professional financial reporting.
Handles historical values, forecasts, CAGR calculations with confidence intervals.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime


class YearlyValue(BaseModel):
    """Market value for a specific year with data quality indicators."""
    year: int = Field(..., description="Calendar year")
    value: Decimal = Field(..., description="Market value")
    unit: str = Field(default="Trillion", description="Unit (Billion, Trillion)")
    currency: str = Field(default="USD", description="Currency code")
    data_type: str = Field(
        default="forecast",
        description="'actual' (observed), 'forecast' (predicted), 'provisional' (preliminary)"
    )
    confidence_level: Optional[str] = Field(
        default=None,
        description="'high', 'medium', 'low' - reliability of this data point"
    )

    @field_validator('data_type')
    @classmethod
    def validate_data_type(cls, v):
        if v not in ['actual', 'forecast', 'provisional']:
            raise ValueError('data_type must be actual, forecast, or provisional')
        return v


class CAGRCalculation(BaseModel):
    """CAGR calculation with temporal context and methodology."""
    start_year: int = Field(..., description="Start year of calculation")
    end_year: int = Field(..., description="End year of calculation")
    start_value: Decimal = Field(..., description="Value at start year")
    end_value: Decimal = Field(..., description="Value at end year")
    cagr_percent: Decimal = Field(..., description="Calculated CAGR percentage")

    calculation_type: str = Field(
        default="forecast",
        description="'historical' (observed), 'forecast' (projected), 'mixed' (both)"
    )
    confidence_level: str = Field(
        default="medium",
        description="'high' (all actual data), 'medium' (mostly actual), 'low' (mostly forecast)"
    )

    @field_validator('calculation_type')
    @classmethod
    def validate_calc_type(cls, v):
        if v not in ['historical', 'forecast', 'mixed']:
            raise ValueError('calculation_type must be historical, forecast, or mixed')
        return v

    def __str__(self) -> str:
        years = self.end_year - self.start_year
        return f"{self.cagr_percent:.2f}% ({self.start_year}-{self.end_year}, {years}yr, {self.calculation_type})"


class TemporalAssumptions(BaseModel):
    """Explicit documentation of temporal assumptions made in analysis."""

    report_publish_date: datetime = Field(
        ...,
        description="When was this report originally published?"
    )
    report_last_updated: datetime = Field(
        ...,
        description="When was this report last updated?"
    )
    forecast_base_year: int = Field(
        ...,
        description="What year was the original forecast based on?"
    )

    current_observation_year: int = Field(
        default=2026,
        description="Current year (when we're reading the data)"
    )

    forecast_horizon_year: int = Field(
        ...,
        description="What year is the forecast for?"
    )

    assumptions_text: str = Field(
        ...,
        description="Plain English explanation of key assumptions"
    )

    data_freshness_days: Optional[int] = Field(
        default=None,
        description="How many days old is the base data?"
    )

    def is_outdated(self, threshold_days: int = 365) -> bool:
        """Check if data is older than threshold."""
        if self.data_freshness_days is None:
            return False
        return self.data_freshness_days > threshold_days

    def freshness_description(self) -> str:
        """Human-readable freshness description."""
        if self.data_freshness_days is None:
            return "Unknown age"

        if self.data_freshness_days < 30:
            return "Very Fresh"
        elif self.data_freshness_days < 90:
            return "Fresh"
        elif self.data_freshness_days < 365:
            return "Moderately Dated"
        else:
            years = self.data_freshness_days // 365
            return f"{years} years old"


class TemporalReport(BaseModel):
    """Report with full temporal context, historical data, and assumption transparency."""

    # Identity
    slug: str = Field(..., description="URL-friendly identifier")
    title: str = Field(..., description="Report title")
    url: str = Field(..., description="Report URL")

    # Temporal assumptions (transparency)
    temporal_assumptions: TemporalAssumptions = Field(
        ...,
        description="Explicit assumptions about time periods and forecasts"
    )

    # Historical + Current + Forecast values
    yearly_values: List[YearlyValue] = Field(
        default_factory=list,
        description="Market values by year (historical actuals + forecasts)"
    )

    # CAGR calculations
    original_forecast_cagr: CAGRCalculation = Field(
        ...,
        description="CAGR from original forecast (when report was published)"
    )

    recalculated_actual_cagr: Optional[CAGRCalculation] = Field(
        default=None,
        description="CAGR recalculated from actual data we've observed so far"
    )

    remaining_forecast_cagr: Optional[CAGRCalculation] = Field(
        default=None,
        description="CAGR needed from now to 2031 to hit original forecast"
    )

    # Other core fields
    region: Optional[str] = None
    fastest_growing_country: Optional[str] = None
    fastest_growing_country_cagr: Optional[Decimal] = None
    leading_segment_name: Optional[str] = None
    leading_segment_share_percent: Optional[Decimal] = None
    leading_segment_cagr: Optional[Decimal] = None
    cloud_share_percent: Optional[Decimal] = None
    cloud_share_year: Optional[int] = None
    major_players: Optional[List[str]] = None

    # Tracking
    scraped_at: Optional[datetime] = None
    version_count: int = 1

    def get_confidence_indicator(self) -> str:
        """Get visual confidence indicator emoji."""
        cagr = self.recalculated_actual_cagr or self.original_forecast_cagr
        if cagr.confidence_level == 'high':
            return "🟢"  # Green - high confidence
        elif cagr.confidence_level == 'medium':
            return "🟡"  # Yellow - medium confidence
        else:
            return "🔴"  # Red - low confidence

    def get_forecast_age_days(self) -> int:
        """How old is the original forecast?"""
        if self.temporal_assumptions.data_freshness_days:
            return self.temporal_assumptions.data_freshness_days
        return 0

    def needs_update(self, threshold_years: int = 1) -> bool:
        """Check if forecast needs updating based on age."""
        years_since_update = (
            self.temporal_assumptions.current_observation_year -
            self.temporal_assumptions.forecast_base_year
        )
        return years_since_update >= threshold_years

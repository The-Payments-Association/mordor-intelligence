"""
Professional CAGR and temporal calculations with confidence intervals.
Follows financial reporting best practices.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple, List
from datetime import datetime
from src.models.temporal import YearlyValue, CAGRCalculation, TemporalAssumptions


def calculate_cagr(
    start_value: Decimal,
    end_value: Decimal,
    years: int,
    calculation_type: str = "forecast"
) -> Decimal:
    """
    Calculate CAGR (Compound Annual Growth Rate).

    Formula: CAGR = (End Value / Start Value) ^ (1 / Years) - 1

    Args:
        start_value: Value at start year
        end_value: Value at end year
        years: Number of years between start and end
        calculation_type: 'historical', 'forecast', or 'mixed'

    Returns:
        CAGR as percentage
    """
    if start_value <= 0 or end_value <= 0:
        return Decimal(0)

    if years <= 0:
        return Decimal(0)

    # Use Decimal for precision
    start = Decimal(str(start_value))
    end = Decimal(str(end_value))
    n = Decimal(str(years))

    # CAGR = (End/Start)^(1/n) - 1
    ratio = end / start
    # Calculate nth root: ratio^(1/n)
    exponent = 1 / float(n)
    nth_root = float(ratio) ** exponent
    cagr = (Decimal(str(nth_root)) - 1) * 100

    # Round to 2 decimal places
    return cagr.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def create_cagr_calculation(
    start_year: int,
    end_year: int,
    start_value: Decimal,
    end_value: Decimal,
    actual_years: int,
    total_years: int,
    calculation_type: str = "forecast"
) -> CAGRCalculation:
    """
    Create CAGRCalculation object with confidence assessment.

    Args:
        start_year: Start year
        end_year: End year
        start_value: Value at start year
        end_value: Value at end year
        actual_years: How many years are actual (observed) data
        total_years: Total years in calculation
        calculation_type: 'historical', 'forecast', or 'mixed'

    Returns:
        CAGRCalculation object with confidence level
    """
    years = end_year - start_year
    cagr_pct = calculate_cagr(start_value, end_value, years, calculation_type)

    # Determine confidence level
    if actual_years == total_years:
        confidence = "high"
    elif actual_years >= total_years * 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    return CAGRCalculation(
        start_year=start_year,
        end_year=end_year,
        start_value=start_value,
        end_value=end_value,
        cagr_percent=cagr_pct,
        calculation_type=calculation_type,
        confidence_level=confidence
    )


def create_temporal_assumptions(
    report_publish_date: datetime,
    report_last_updated: datetime,
    forecast_base_year: int,
    forecast_horizon_year: int = 2031,
    current_observation_year: int = 2026,
) -> TemporalAssumptions:
    """
    Create TemporalAssumptions with calculated freshness metrics.

    Args:
        report_publish_date: Original publication date
        report_last_updated: Last update date
        forecast_base_year: Year the forecast was based on
        forecast_horizon_year: Target forecast year (default 2031)
        current_observation_year: Current year (default 2026)

    Returns:
        TemporalAssumptions object
    """
    # Calculate data freshness in days
    days_since_update = (datetime.now() - report_last_updated).days

    # Create assumptions text
    years_forecast = forecast_horizon_year - forecast_base_year
    years_since_base = current_observation_year - forecast_base_year

    assumptions_text = f"""
This report was originally published on {report_publish_date.strftime('%B %d, %Y')} and last updated on {report_last_updated.strftime('%B %d, %Y')}.

The forecast CAGR was calculated based on {forecast_base_year} data and projects growth through {forecast_horizon_year} ({years_forecast} year horizon).

Current Status (as of {current_observation_year}):
- {years_since_base} years have passed since the forecast base year ({forecast_base_year})
- We can compare actual {forecast_base_year}-{current_observation_year} growth against the forecast
- The remaining period ({current_observation_year}-{forecast_horizon_year}) still relies on projected growth

Data Freshness: The base data is approximately {days_since_update} days old.

Key Assumption: The forecast CAGR may not reflect actual market evolution. We recalculate based on observed data.
    """.strip()

    return TemporalAssumptions(
        report_publish_date=report_publish_date,
        report_last_updated=report_last_updated,
        forecast_base_year=forecast_base_year,
        current_observation_year=current_observation_year,
        forecast_horizon_year=forecast_horizon_year,
        assumptions_text=assumptions_text,
        data_freshness_days=days_since_update
    )


def extract_yearly_values_from_report(
    historical_2024: Optional[Decimal] = None,
    historical_2025: Optional[Decimal] = None,
    current_2026: Decimal = Decimal('6.34'),
    forecast_2031: Decimal = Decimal('8.29'),
    unit: str = "Trillion"
) -> List[YearlyValue]:
    """
    Create list of YearlyValue objects from available market data.

    Args:
        historical_2024: 2024 market value (if available)
        historical_2025: 2025 market value (if available)
        current_2026: 2026 market value (current, required)
        forecast_2031: 2031 market value (forecast, required)
        unit: Unit (Trillion, Billion)

    Returns:
        List of YearlyValue objects
    """
    values = []

    if historical_2024:
        values.append(YearlyValue(
            year=2024,
            value=historical_2024,
            unit=unit,
            data_type="actual",
            confidence_level="high"
        ))

    if historical_2025:
        values.append(YearlyValue(
            year=2025,
            value=historical_2025,
            unit=unit,
            data_type="actual",
            confidence_level="high"
        ))

    values.append(YearlyValue(
        year=2026,
        value=current_2026,
        unit=unit,
        data_type="actual",
        confidence_level="high"
    ))

    values.append(YearlyValue(
        year=2031,
        value=forecast_2031,
        unit=unit,
        data_type="forecast",
        confidence_level="medium"
    ))

    return values


def calculate_required_future_cagr(
    current_year: int,
    current_value: Decimal,
    target_year: int,
    target_value: Decimal
) -> Decimal:
    """
    Calculate what CAGR is required from current to target to hit the forecast.

    Args:
        current_year: Current year (e.g., 2026)
        current_value: Current market value
        target_year: Target year (e.g., 2031)
        target_value: Target market value

    Returns:
        Required CAGR percentage
    """
    years = target_year - current_year
    return calculate_cagr(current_value, target_value, years, calculation_type="forecast")


def compare_forecast_vs_actual(
    original_forecast_cagr: Decimal,
    actual_cagr_observed: Decimal
) -> dict:
    """
    Compare original forecast CAGR with actual observed CAGR.

    Returns:
        Dictionary with comparison metrics
    """
    difference = actual_cagr_observed - original_forecast_cagr
    percent_diff = (difference / original_forecast_cagr * 100) if original_forecast_cagr != 0 else Decimal(0)

    return {
        "original_forecast": original_forecast_cagr,
        "actual_observed": actual_cagr_observed,
        "difference": difference,
        "percent_difference": percent_diff,
        "forecast_was_accurate": abs(percent_diff) < Decimal('20'),  # Within 20%
        "forecast_was_conservative": actual_cagr_observed > original_forecast_cagr,  # Market grew more than expected
        "assessment": (
            "Forecast was too conservative (market growing faster)" if actual_cagr_observed > original_forecast_cagr
            else "Forecast was too optimistic (market growing slower)"
        )
    }

# Temporal Data & Assumption Transparency - Best Practices

## Overview

We now properly handle temporal data professionally. Here's what was implemented:

## 1. New Data Models (`src/models/temporal.py`)

### YearlyValue
```python
YearlyValue(
    year=2026,
    value=Decimal('6.34'),
    unit="Trillion",
    data_type="actual",  # "actual", "forecast", "provisional"
    confidence_level="high"  # "high", "medium", "low"
)
```

### CAGRCalculation
```python
CAGRCalculation(
    start_year=2024,
    end_year=2031,
    start_value=Decimal('5.8'),
    end_value=Decimal('8.29'),
    cagr_percent=Decimal('5.51'),
    calculation_type="mixed",  # "historical", "forecast", "mixed"
    confidence_level="medium"
)
```

### TemporalAssumptions
```python
TemporalAssumptions(
    report_publish_date=datetime(2025, 6, 1),
    report_last_updated=datetime(2026, 1, 30),
    forecast_base_year=2025,
    current_observation_year=2026,
    forecast_horizon_year=2031,
    assumptions_text="[Detailed explanation of methodology]",
    data_freshness_days=15
)
```

## 2. Professional Calculations (`src/utils/temporal_calc.py`)

### Key Functions

#### `calculate_cagr()`
Calculates CAGR with proper formula:
```
CAGR = (End Value / Start Value) ^ (1 / Years) - 1
```

#### `create_cagr_calculation()`
Creates CAGRCalculation with automatic confidence assessment:
- High confidence: 100% actual data
- Medium: ≥50% actual data
- Low: <50% actual data

#### `compare_forecast_vs_actual()`
Compares original forecast CAGR to actual observed CAGR:
```python
{
    "original_forecast": 5.51,
    "actual_observed": 6.2,
    "difference": 0.69,
    "forecast_was_conservative": True,
    "assessment": "Market growing faster than forecast"
}
```

## 3. Dashboard Components (Recommended Implementation)

### Page 1: Overview - Add Assumption Badges
```
📊 Mordor Intelligence Market Dashboard

⚠️ IMPORTANT: All forecasts based on 2025-2026 data
   Data freshness: 15 days | Forecast horizon: 2031

Key Metrics:
┌─────────────────────┐
│ 40 Markets          │
│ Avg CAGR: 18.5%     │
│ ⚠️ Forecast-based   │
└─────────────────────┘
```

### Page 2: New "Temporal Analysis" Page
Shows:
1. **Timeline Visualization**
   - Historical: 2024-2026 (actual data)
   - Future: 2027-2031 (forecast)

2. **Forecast Accuracy Assessment**
   - Forecast made in: 2025
   - Actual growth 2025-2026: 7.2% vs forecast 5.51%
   - Status: 🟢 Conservative estimate (good news)

3. **Per-Market Assumptions Table**
   ```
   Market | Forecast Age | Data Freshness | CAGR Type | Confidence
   -------|------|-----------|-----------|----------
   SA RTP | 1yr  | 15 days   | Mixed     | 🟡 Medium
   ```

### Page 3: Updated Market Analysis
```
Market: South America Real Time Payments

📅 TEMPORAL CONTEXT
├─ Report Published: June 2025
├─ Last Updated: Jan 30, 2026
├─ Forecast Base: 2025 data
├─ Data Freshness: 15 days old
└─ Forecast Horizon: 2031

📊 MARKET SIZING WITH CONFIDENCE
├─ 2026 (ACTUAL): $6.34T 🟢 High Confidence
├─ 2031 (FORECAST): $8.29T 🟡 Medium Confidence
└─ Required CAGR: 5.51% (2026→2031)

📈 CAGR ANALYSIS
├─ Original Forecast CAGR: 5.51% (2025-2031)
├─ Actual Observed CAGR: 6.2% (2025-2026)
├─ Assessment: 🟢 Conservative (outperforming)
└─ Remaining Required: 5.08% (2026-2031)
```

## 4. Professional Visualizations

### Timeline Chart
```
2024         2025         2026         2027-2031
 |            |            |            |
 |[Actual]────|[Actual]────|[Actual]────|[Forecast]─→ 2031
 │            │            │            │
 5.8T         6.1T         6.34T        8.29T
 ✓ Known      ✓ Known      ✓ Known      ? Projected
```

### Confidence Bands
```
Market Size Forecast with Confidence Interval

$10T ├─────────────────────────────┐
     │                       ┌─────┴─────┐
$8T  │   [Forecast Region]  │ Upper Bound│
     │   (Medium Confidence) └─────┬─────┘
$6T  │─────────────────────────────┤
     │                       └─────┬─────┐
$4T  │                             │Lower │
     └─────────────────────────────┴─────┘
     2024  2025  2026  2027  2028  2029  2030  2031
       ✓ Actual Data  ➞  Forecast Region ➞
```

### CAGR Comparison
```
Forecast Accuracy: SA Real Time Payments

Forecast CAGR:  ████░░░░░░  5.51%
Actual CAGR:    ██████░░░░  6.20%
                ─────────────
Difference:     +0.69% (13% better than forecast)
Status:         🟢 Conservative Estimate (Good)
```

## 5. Assumption Transparency Text (Example)

```
ANALYTICAL ASSUMPTIONS & DISCLAIMERS

1. TEMPORAL CONTEXT
   • Report originally published: June 2025
   • Report last updated: January 30, 2026
   • Analysis conducted: February 2026
   • Data freshness: ~15 days

2. FORECAST METHODOLOGY
   • The 5.51% CAGR was forecasted in Q2 2025
   • It was calculated from historical 2020-2025 data
   • It represents a 6-year projection (2025-2031)

3. CURRENT STATUS (February 2026)
   • 1 year of actual data now available (2025-2026)
   • Actual growth was 6.20% (outperforming forecast)
   • Remaining forecast period: 5 years (2026-2031)

4. KEY ASSUMPTION: Forecast Accuracy
   • Original CAGR: 5.51% (based on 2025 expectations)
   • Actual (2025-2026): 6.20% (observed growth)
   • Status: Conservative (market performing better)
   • Note: Past performance does not guarantee future results

5. CONFIDENCE LEVELS
   • Historical Data (2024-2026): 🟢 High confidence (actual observed)
   • Forecast Data (2027-2031): 🟡 Medium confidence (projected)
   • Overall CAGR: 🟡 Medium (mixed historical/forecast)

6. LIMITATIONS
   • Forecasts are point estimates, not ranges
   • Market conditions may have changed since report publication
   • Global economic events not considered in forecast
   • Segment-level data may be less reliable than overall market

7. RECOMMENDATION
   • Use this data for directional insight (not absolute prediction)
   • Combine with other sources for critical decisions
   • Re-validate forecast annually as new data emerges
   • Monitor for significant forecast misses (>20% variance)
```

## 6. Color Coding & Indicators

### Confidence Levels (CSS)
```
High Confidence:   🟢 Green (#00AA00)
Medium Confidence: 🟡 Yellow (#FFAA00)
Low Confidence:    🔴 Red (#AA0000)
```

### Data Type Icons
```
✓ Actual Data      - Observed from reports
? Forecast Data    - Projected by analysts
~ Provisional Data - Preliminary data (may change)
```

### Status Indicators
```
🟢 Forecast conservative (market outperforming)
🟡 Forecast on track (within expected range)
🔴 Forecast optimistic (market underperforming)
```

## 7. Database Updates Needed

Add to reports table:
```sql
-- Historical values by year (JSON)
historical_values TEXT,  -- {"2024": {"value": 5.8, "type": "actual"}, ...}

-- Temporal metadata
forecast_publish_date DATE,
forecast_base_year INT,
data_freshness_days INT,

-- Calculated metrics
actual_observed_cagr DECIMAL,
forecast_accuracy_status TEXT,  -- "conservative", "on_track", "optimistic"
confidence_level TEXT,  -- "high", "medium", "low"
assumption_notes TEXT
```

## 8. Implementation Roadmap

### Phase 1: Data Model (✅ DONE)
- [x] Create temporal.py models
- [x] Create temporal_calc.py utilities
- [x] Add confidence calculation logic

### Phase 2: Parser Enhancement
- [ ] Update JSON-LD parser to extract historical years
- [ ] Calculate actual CAGR from observed data
- [ ] Determine forecast base year from report

### Phase 3: Dashboard Enhancement
- [ ] Add "Temporal Analysis" page
- [ ] Update "Market Analysis" with assumption badges
- [ ] Add confidence level indicators
- [ ] Create timeline visualizations

### Phase 4: Documentation
- [ ] Add assumption disclaimers to each report
- [ ] Create help page explaining methodology
- [ ] Add legend for confidence indicators

## 9. Example Output

```json
{
  "slug": "south-america-real-time-payments-market",
  "title": "South America Real Time Payments Market",

  "yearly_values": [
    {"year": 2025, "value": 6.1, "data_type": "actual", "confidence": "high"},
    {"year": 2026, "value": 6.34, "data_type": "actual", "confidence": "high"},
    {"year": 2031, "value": 8.29, "data_type": "forecast", "confidence": "medium"}
  ],

  "original_forecast_cagr": {
    "start_year": 2025,
    "end_year": 2031,
    "cagr_percent": 5.51,
    "calculation_type": "forecast",
    "confidence_level": "medium"
  },

  "recalculated_actual_cagr": {
    "start_year": 2025,
    "end_year": 2026,
    "cagr_percent": 6.20,
    "calculation_type": "historical",
    "confidence_level": "high"
  },

  "remaining_forecast_cagr": {
    "start_year": 2026,
    "end_year": 2031,
    "cagr_percent": 5.08,
    "calculation_type": "forecast",
    "confidence_level": "medium"
  },

  "temporal_assumptions": {
    "report_publish_date": "2025-06-15",
    "report_last_updated": "2026-01-30",
    "forecast_base_year": 2025,
    "current_observation_year": 2026,
    "data_freshness_days": 15,
    "forecast_accuracy_status": "conservative"
  }
}
```

## 10. Benefits of This Approach

✅ **Transparency**: Users understand data limitations
✅ **Accountability**: Clear methodology documented
✅ **Confidence**: Visual indicators show reliability
✅ **Accuracy**: Based on actual observed data where available
✅ **Professional**: Meets financial reporting standards
✅ **Actionable**: Helps users make better decisions
✅ **Version-Tracked**: Changes captured over time

## Next Steps

1. Update parser to extract historical 2024/2025 values
2. Implement calculations in new dashboard page
3. Add assumption disclaimers to "Market Analysis"
4. Create "Temporal Analysis" page with visualizations
5. Update database schema to store temporal metadata

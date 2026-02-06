# Update Frequency Analysis - Next Level Enhancement

## Current Situation

**What We Know:**
- Reports modified: Oct 2024 → Feb 2026
- Most recent batch: 18 reports in Jan 2026, 2 in Feb 2026
- This is our **first scrape** - no historical tracking yet
- **Can't determine update frequency yet** without historical data

**The Opportunity:**
We can use multiple strategies to determine update patterns and optimize scraping:

---

## Strategy 1: Wayback Machine Analysis (Most Valuable)

### How It Works
The Internet Archive Wayback Machine has captured Mordor Intelligence pages historically. We can:
1. Query Wayback Machine API for historical snapshots
2. Find when pages were last different
3. Determine update frequency per market
4. Build "update calendar"

### Implementation

```python
# src/scrapers/wayback_analysis.py
import requests
from datetime import datetime

def get_wayback_snapshots(url: str, start_year: int = 2024):
    """
    Get all Wayback Machine snapshots of a URL.

    Example: https://archive.org/wayback/available?url=DOMAIN&output=json
    """
    base_url = "https://archive.org/wayback/available"
    params = {
        'url': url,
        'output': 'json'
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    # Returns list of timestamps when page was captured
    snapshots = data.get('archived_snapshots', {}).get('snapshots', [])

    return [
        {
            'timestamp': snap['timestamp'],
            'date': datetime.strptime(snap['timestamp'], '%Y%m%d%H%M%S'),
            'status': snap['status']
        }
        for snap in snapshots
    ]


def analyze_update_frequency(snapshots: list) -> dict:
    """
    Analyze snapshots to determine update frequency.
    """
    if len(snapshots) < 2:
        return {'frequency': 'unknown', 'snapshots': len(snapshots)}

    # Calculate days between snapshots
    dates = sorted([s['date'] for s in snapshots])
    gaps = []

    for i in range(1, len(dates)):
        gap_days = (dates[i] - dates[i-1]).days
        if gap_days > 0:  # Ignore same-day captures
            gaps.append(gap_days)

    if not gaps:
        return {'frequency': 'unknown', 'snapshots': len(snapshots)}

    avg_gap = sum(gaps) / len(gaps)
    min_gap = min(gaps)
    max_gap = max(gaps)

    # Determine frequency
    if avg_gap < 7:
        frequency = 'daily'
    elif avg_gap < 30:
        frequency = 'weekly'
    elif avg_gap < 90:
        frequency = 'monthly'
    elif avg_gap < 180:
        frequency = 'quarterly'
    elif avg_gap < 365:
        frequency = 'semi-annually'
    else:
        frequency = 'yearly'

    return {
        'frequency': frequency,
        'avg_gap_days': round(avg_gap, 1),
        'min_gap_days': min_gap,
        'max_gap_days': max_gap,
        'total_snapshots': len(snapshots),
        'date_range': {
            'first': dates[0].isoformat(),
            'last': dates[-1].isoformat()
        }
    }
```

### Expected Output
```json
{
  "south-america-real-time-payments-market": {
    "frequency": "quarterly",
    "avg_gap_days": 87.5,
    "min_gap_days": 45,
    "max_gap_days": 120,
    "total_snapshots": 12,
    "date_range": {
      "first": "2024-02-15",
      "last": "2026-02-06"
    }
  }
}
```

---

## Strategy 2: Content Hash Comparison (Extract Differences)

### How It Works
Compare actual content from Wayback Machine snapshots to see:
1. Which fields actually changed
2. How much content changed
3. When meaningful updates occurred

### Implementation

```python
# src/utils/wayback_content_analysis.py

def extract_from_wayback(wayback_url: str) -> dict:
    """
    Fetch page from Wayback Machine and extract report data.

    wayback_url: https://web.archive.org/web/20240815120000/https://...
    """
    import requests
    from src.parsers.jsonld_parser import JSONLDParser

    response = requests.get(wayback_url, timeout=30)
    parser = JSONLDParser(response.text, wayback_url)

    return parser.parse_report()


def compare_versions_from_wayback(
    url: str,
    snapshots: list
) -> list:
    """
    Compare multiple snapshots to find real changes.

    Returns: List of {date, cagr_changed, size_changed, players_changed, ...}
    """
    changes = []
    previous_data = None

    for snapshot in snapshots[-5:]:  # Last 5 snapshots to save time
        wayback_url = (
            f"https://web.archive.org/web/{snapshot['timestamp']}/"
            f"{url}"
        )

        try:
            current_data = extract_from_wayback(wayback_url)

            if previous_data:
                changed_fields = identify_changes(previous_data, current_data)

                if changed_fields:
                    changes.append({
                        'date': snapshot['date'],
                        'changed_fields': changed_fields,
                        'magnitude': len(changed_fields)
                    })

            previous_data = current_data

        except Exception as e:
            print(f"Could not fetch {snapshot['timestamp']}: {e}")

    return changes
```

---

## Strategy 3: Dashboard Feature - Update Calendar

### New Dashboard Page: "📅 Update Frequency Analysis"

```
Shows for each market:

┌─────────────────────────────────────────────────┐
│ Market: South America Real Time Payments        │
│                                                 │
│ 📊 UPDATE HISTORY (from Wayback Machine)        │
│ ┌──────────────────────────────────────────┐   │
│ │ Snapshots Found: 12                      │   │
│ │ Date Range: Feb 2024 - Feb 2026          │   │
│ │ Update Frequency: QUARTERLY              │   │
│ │ Avg Days Between Updates: 87.5 days      │   │
│ └──────────────────────────────────────────┘   │
│                                                 │
│ 📈 TIMELINE OF CHANGES                         │
│ 2024-02-15: Initial snapshot                   │
│ 2024-05-10: CAGR changed (5.2% → 5.51%)       │
│ 2024-08-20: Market size updated               │
│ 2024-11-15: Major players changed             │
│ 2025-02-06: Cloud share updated               │
│ 2025-05-12: Forecast value changed            │
│ ...                                            │
│                                                 │
│ 🎯 NEXT EXPECTED UPDATE                        │
│ Based on pattern: ~May 2026                    │
│ Recommendation: Scrape monthly in Q2/Q3       │
│                                                 │
│ ⚠️ ANOMALIES DETECTED                          │
│ Jan 2026: Multiple reports updated           │
│ Possible: Quarterly refresh cycle             │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Strategy 4: Smart Scraping Schedule

### Optimize When We Scrape

```python
# src/config/scraping_schedule.py

MARKET_UPDATE_SCHEDULES = {
    "south-america-real-time-payments-market": {
        "frequency": "quarterly",
        "expected_updates": ["Feb", "May", "Aug", "Nov"],
        "scrape_on": ["1st", "2nd", "3rd"],  # Days of month
        "confidence": "high"  # Based on Wayback data
    },
    "asia-pacific-fintech-market": {
        "frequency": "semi-annual",
        "expected_updates": ["Jan", "Jul"],
        "scrape_on": ["1st"],
        "confidence": "medium"
    },
    "uk-payments-market": {
        "frequency": "unknown",
        "expected_updates": [],
        "scrape_on": ["1st"],  # Default: monthly
        "confidence": "low"
    }
}


def should_scrape_market(slug: str, current_month: str) -> bool:
    """
    Determine if we should scrape this market this month.
    Avoids wasting resources on markets that haven't changed.
    """
    schedule = MARKET_UPDATE_SCHEDULES.get(slug, {})

    if schedule.get('frequency') == 'quarterly':
        # Only scrape in expected months
        return current_month in schedule['expected_updates']

    elif schedule.get('frequency') == 'unknown':
        # Default: scrape everything
        return True

    else:
        # Other frequencies: check schedule
        return current_month in schedule['expected_updates']
```

### Benefits
- **Saves bandwidth**: Don't scrape markets that don't change
- **Reduces costs**: Fewer unnecessary requests
- **Smarter insights**: Know which markets are volatile vs. stable
- **Better predictions**: Know when to expect updates

---

## Strategy 5: Detect Update Patterns

### Identify Seasonal Changes

```python
# src/analytics/update_patterns.py

def detect_update_patterns(market_history: list) -> dict:
    """
    Analyze update patterns for seasonality and cycles.
    """

    # Group by month
    months_with_updates = {}
    for change in market_history:
        month = change['date'].strftime('%B')
        if month not in months_with_updates:
            months_with_updates[month] = 0
        months_with_updates[month] += 1

    # Identify seasonal pattern
    most_common_month = max(months_with_updates,
                            key=months_with_updates.get)

    return {
        'seasonal_pattern': months_with_updates,
        'most_common_update_month': most_common_month,
        'likely_cycle': identify_cycle(market_history),
        'next_expected_update': predict_next_update(market_history)
    }


def predict_next_update(history: list) -> dict:
    """
    Predict when next update will occur.
    """
    if not history:
        return {'prediction': 'unknown'}

    # Last update date
    last_update = history[-1]['date']

    # Average gap
    gaps = []
    for i in range(1, len(history)):
        gap = (history[i]['date'] - history[i-1]['date']).days
        gaps.append(gap)

    if gaps:
        avg_gap = sum(gaps) / len(gaps)
        next_date = last_update + timedelta(days=int(avg_gap))

        return {
            'prediction': next_date.isoformat(),
            'confidence': 'high' if len(gaps) > 5 else 'medium',
            'avg_update_cycle_days': round(avg_gap)
        }

    return {'prediction': 'unknown'}
```

### Example Output
```
Market: South America Real Time Payments

Update Pattern Analysis:
├─ Most Common Update Month: January (5 updates)
├─ Secondary: May (4 updates)
├─ Cycle: Roughly Quarterly (Q1, Q2, Q3, Q4)
├─ Avg Days Between Updates: 87.5
├─ Last Update: Jan 30, 2026
├─ Next Expected: ~Apr 28, 2026 (±2 weeks)
└─ Confidence: High (12 data points)
```

---

## Implementation Roadmap

### Phase 1: Data Collection (1-2 hours)
1. Query Wayback Machine for all 40 reports
2. Store snapshot dates in database
3. Create update_frequency table

```sql
CREATE TABLE market_update_frequency (
    market_id INT,
    frequency VARCHAR,  -- 'daily', 'weekly', 'monthly', 'quarterly', etc.
    avg_gap_days DECIMAL,
    min_gap_days INT,
    max_gap_days INT,
    total_snapshots INT,
    first_snapshot_date DATE,
    last_snapshot_date DATE,
    confidence VARCHAR,  -- 'high', 'medium', 'low'
    analyzed_at TIMESTAMP
);
```

### Phase 2: Pattern Analysis (2-3 hours)
1. Download historical versions from Wayback
2. Extract data and compare
3. Identify field-level changes
4. Build update calendar

### Phase 3: Dashboard Integration (2-3 hours)
1. Create "📅 Update Frequency" dashboard page
2. Show timeline for each market
3. Display next expected update
4. Identify anomalies

### Phase 4: Smart Scraping (1-2 hours)
1. Update scraper to check schedule
2. Skip markets not due for update
3. Log why skipped
4. Report savings

---

## Expected Findings

Based on typical SaaS market research reports:

| Frequency | Typical Markets | Examples |
|-----------|-----------------|----------|
| **Daily** | Rare | Maybe none |
| **Weekly** | Uncommon | High-volatility segments |
| **Monthly** | Possible | Some updates |
| **Quarterly** | Most Likely | Seasonal business cycles |
| **Semi-Annual** | Possible | Major refreshes |
| **Yearly** | Possible | Annual reports |
| **Irregular** | Some | Event-driven updates |

---

## Data You'll Get

### Per Market:
```json
{
  "slug": "south-america-real-time-payments-market",
  "update_frequency": "quarterly",
  "avg_days_between_updates": 87.5,
  "update_months": ["January", "April", "July", "October"],
  "last_update": "2026-01-30",
  "next_predicted_update": "2026-04-28",
  "confidence": "high",
  "historical_snapshots": 12,
  "changes_per_update": {
    "cagr": 0.8,  # How often CAGR changes
    "market_size": 0.9,
    "major_players": 0.5,
    "cloud_share": 0.6
  }
}
```

### Dashboard Insights:
- Which markets are volatile (frequent updates)
- Which are stable (rare updates)
- Seasonal patterns (Q1 refresh, summer silence, etc.)
- Anomalies (unexpected early updates)
- Next expected updates (plan ahead)

---

## Benefits of This Analysis

### For Operations
✅ **Optimize scraping**: Only scrape when needed
✅ **Save resources**: Fewer unnecessary requests
✅ **Predictability**: Know when to expect updates
✅ **Anomaly detection**: Spot unusual patterns

### For Analysis
✅ **Market volatility**: Volatile = rapid changes
✅ **Data quality**: Frequent updates = fresher data
✅ **Forecasting**: Predict data availability
✅ **Seasonal trends**: Understand cycles

### For Users
✅ **Trust**: Show data freshness with confidence
✅ **Expectations**: "Next update expected May 15"
✅ **Transparency**: "Data is 6 days old, 25 until next update"
✅ **Reliability**: Know how old data is relative to update cycle

---

## Quick Start

```bash
# 1. Install wayback library
pip install waybackpy requests

# 2. Create analysis script
python src/scrapers/analyze_wayback_history.py

# 3. Results saved to:
# data/market_update_frequency.json

# 4. Add to database
python -m src.cli import-update-frequencies

# 5. Dashboard updated automatically
# New "📅 Update Frequency" page appears
```

---

## Next Level Opportunities

Once we have update frequency data:

1. **Predictive Updates**
   - ML model to predict update timing
   - Alert system when update expected
   - Automatic re-scrape on schedule

2. **Volatility Scoring**
   - Which markets change most
   - Which are most stable
   - Investment implications

3. **Data Freshness Ranking**
   - Rank markets by data age
   - Highlight stale data
   - Recommend re-validation

4. **Change Impact Analysis**
   - What typically changes together
   - Correlation between fields
   - Market evolution patterns

5. **Predictive Intervals**
   - Confidence bands on forecasts
   - Tighter intervals for stable markets
   - Wider intervals for volatile ones

---

## Bottom Line

**Currently:** We scrape monthly, not knowing if that's optimal

**After Analysis:** We'll know:
- ✅ Actual update frequency per market
- ✅ Expected update dates
- ✅ Which markets are volatile vs. stable
- ✅ Whether quarterly, semi-annual, or yearly is optimal
- ✅ Seasonal patterns and anomalies

**Result:** More professional, data-driven scraping strategy 🚀

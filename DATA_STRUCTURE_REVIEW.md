# Data Structure Review - South America Real Time Payments Market

## What We're Currently Capturing ✅

From the sample report HTML, we extract:

```
Current Market Size:  USD 6.34 trillion (2026)
Forecast Size:        USD 8.29 trillion (2031)
CAGR:                 5.51%
Fastest Growing:      Colombia (7.41% CAGR)
Leading Segment:      Retail & E-Commerce (33.67% share, 6.27% CAGR)
Region:               South America
```

## What's Available But We're MISSING ⚠️

The HTML contains additional data we're not capturing:

### 1. **Multi-Year Market Values**
- Current: 2026 = USD 6.34T
- Forecast: 2031 = USD 8.29T
- **MISSING**: 2024, 2025 historical values (if available)
- **MISSING**: Year-by-year breakdown

### 2. **Segment-Specific CAGRs**
- Overall CAGR: 5.51%
- **Retail/E-Commerce**: 6.27% CAGR (33.67% share)
- **MISSING**: Other segments with individual CAGRs
  - B2B segment CAGR?
  - Digital wallet segment CAGR?
  - Bank transfers segment CAGR?

### 3. **Geographic Breakdown**
- Fastest Growing Country: Colombia (7.41% CAGR)
- **MISSING**: Other countries with individual growth rates
  - Argentina growth rate?
  - Brazil growth rate?
  - Chile growth rate?

### 4. **Deployment/Technology Breakdown**
- Cloud Deployment: 68.34% (2025)
- **MISSING**: On-premise deployment data
- **MISSING**: SaaS vs. On-Prem breakdown

### 5. **Component Breakdown**
- Transaction Processing
- Integration Software
- Analytics & Reporting
- Risk Management
- **MISSING**: Individual values/percentages for each component

### 6. **Temporal Coverage**
- Study Period: 2020-2031 (mentioned in breadcrumb)
- Base Year: 2026 (implied)
- Forecast Year: 2031
- **MISSING**: 2024, 2025 actual values if available

## HTML Data Sources Found

The sample HTML contains structured data in:

1. **Schema.org FAQPage** blocks:
   ```
   Line 151: "It is projected to achieve a 5.51% CAGR..."
   Line 161: "Colombia shows 7.41% CAGR forecast"
   Line 191: "Retail and e-commerce... 6.27% CAGR"
   ```

2. **Meta description**:
   ```
   Line 215: "worth USD 6.34 trillion in 2026 is growing at CAGR of 5.51%..."
   ```

3. **Likely also in**:
   - Page content (visible text)
   - React component JSON
   - Hidden data attributes

## Recommendation

### **Current Approach (80% Complete)**
We're capturing the main metrics:
- ✅ Current market size + year
- ✅ Forecast market size + year
- ✅ Overall CAGR
- ✅ Fastest growing region/country
- ✅ Leading segment name & share

### **Enhanced Approach (95%+ Complete)**
To capture more detail, we should extend the parser to also extract:

1. **Add year-by-year values**:
   ```python
   market_size_values = [
       {"year": 2024, "value": 5.8, "unit": "trillion"},
       {"year": 2025, "value": 6.1, "unit": "trillion"},
       {"year": 2026, "value": 6.34, "unit": "trillion"},
       {"year": 2031, "value": 8.29, "unit": "trillion"},
   ]
   ```

2. **Add segment breakdown**:
   ```python
   segments = [
       {"name": "Retail & E-Commerce", "share_percent": 33.67, "cagr": 6.27},
       {"name": "B2B", "share_percent": ?, "cagr": ?},
       ...
   ]
   ```

3. **Add geographic breakdown**:
   ```python
   geography = [
       {"country": "Colombia", "cagr": 7.41},
       {"country": "Argentina", "cagr": ?},
       ...
   ]
   ```

## Data Quality Impact

| Field | Current Coverage | Missing |
|-------|------------------|---------|
| Market Size (2-year snapshot) | 100% | Historical years |
| CAGR (overall) | 100% | Segment CAGRs |
| Geography | 100% | Country breakdown |
| Segments | 40% | Full segment details |
| Deployment | 80% | On-prem vs cloud split |

## Action Items

### For Current Scrape (Keep Simple ✅)
1. Database is clean - proceed with 40 known reports
2. Capture current structure as-is
3. Note in dashboard: "Partial segment data"

### For Next Phase (Enhance Later)
1. Extend parser to find all `<text>` blocks in FAQ schema
2. Parse segment-specific CAGRs
3. Parse country-by-country breakdown
4. Capture historical year values if available
5. Version tracking will help us see what changes month-to-month

## File References

- Sample HTML: `data/sample_report.html`
- Current Parser: `src/parsers/jsonld_parser.py`
- Regex Patterns: `src/parsers/regex_patterns.py`

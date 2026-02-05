# Mordor Intelligence Scraper - Implementation Plan

## Overview
Build a production-ready scraper for 153 payment market reports with full versioning, change tracking, comprehensive data extraction, and advanced data directory organization for audit trails and analysis.

## Requirements
- Extract all 153 report URLs (40 from HTML __NEXT_DATA__ + 113 from API)
- Full versioning: snapshot on every field change
- Capture ALL fields: market values, CAGR, segments, geographic details, major players
- Monthly scraping with change detection
- DuckDB storage with 3 tables: reports (current), report_versions (history), scrape_log (ops)
- Advanced data organization: raw HTML archives, parsed JSON intermediate files, analysis-ready exports

## Architecture

### Data Flow
1. **URL Discovery**: Index page __NEXT_DATA__ (40) → API calls pages 2-6 (113) → 153 URLs
2. **Scraping**: HTTP GET with rate limiting (2s delay) → HTML response
3. **Parsing**: Extract 5 JSON-LD blocks → Regex parse FAQ answers → Pydantic model
4. **Change Detection**: Compute content hash → Compare with DB → Create version if changed
5. **Storage**: DuckDB with full snapshot on any field change

### JSON-LD Data Sources
Each report page contains 5 structured data blocks:
- **FAQPage**: Key metrics (market size, CAGR, segments, players) in Q&A format
- **Dataset**: Metadata (temporal coverage, spatial coverage, description)
- **WebPage**: Dates (datePublished, dateModified)
- **ImageObject**: Chart URLs
- **BreadcrumbList**: Navigation (skip)

## Advanced Data Directory Usage

### `data/raw/` - HTML Snapshots by Date
Store monthly HTML snapshots for audit trail and re-parsing:
```
data/raw/
├── 2026-02/                                    # Month-based folders
│   ├── index_20260201.html                     # Payments index page snapshot
│   ├── south-america-real-time-payments-market_20260201.html
│   ├── brazil-payments-market_20260201.html
│   └── ...                                     # All 153 report HTMLs
├── 2026-03/                                    # Next month
│   ├── index_20260301.html
│   ├── south-america-real-time-payments-market_20260301.html
│   └── ...
└── latest/                                     # Symlinks to most recent
    ├── index.html -> ../2026-03/index_20260301.html
    └── ...
```

**Benefits**:
- Historical HTML for re-parsing if schema changes
- Audit trail to verify extraction accuracy
- Re-run parser on old HTML to backfill new fields
- Monthly folders = easy cleanup (keep last 12 months, archive older)

### `data/processed/` - Parsed JSON by Run
Store extracted structured data before DB insertion:
```
data/processed/
├── runs/
│   ├── 2026-02-01_run-abc123/                  # UUID-based run folders
│   │   ├── reports.jsonl                       # All 153 parsed reports (JSONL format)
│   │   ├── errors.json                         # Parse errors/warnings
│   │   └── summary.json                        # Run stats
│   └── 2026-03-01_run-def456/
│       ├── reports.jsonl
│       ├── errors.json
│       └── summary.json
└── latest.jsonl -> runs/2026-03-01_run-def456/reports.jsonl
```

**Benefits**:
- Intermediate format for debugging parser issues
- Can re-import to DB without re-scraping
- JSONL (JSON Lines) allows streaming large files
- Easy to inspect with `jq` or `duckdb`

### `data/exports/` - Analysis-Ready Outputs
Export query results and reports:
```
data/exports/
├── monthly_changes/
│   ├── 2026-02_changes.csv                     # Reports that changed this month
│   ├── 2026-03_changes.csv
│   └── 2026-03_changes.xlsx                    # Excel with charts
├── market_snapshots/
│   ├── all_markets_2026-02.parquet             # Monthly snapshot of all 153 reports
│   └── all_markets_2026-03.parquet
├── player_analysis/
│   ├── major_players_frequency.csv             # Which companies appear most
│   └── player_market_share.csv                 # Estimated coverage
├── segment_trends/
│   ├── cloud_vs_onpremise_trend.csv
│   └── segment_growth_rates.csv
└── reports/
    ├── monthly_summary_2026-03.pdf             # Generated PDF report
    └── change_alerts_2026-03.html              # Dashboard
```

**Benefits**:
- Parquet for efficient analytics in pandas/DuckDB
- CSV for Excel/BI tools
- Ready for visualization in Tableau/Power BI
- PDF reports for stakeholders

## Database Schema

### Table 1: `reports` (Current State)
Primary table with latest version of each report:
- **Identity**: id, slug, url, title
- **Market Sizing**: market_size_current/forecast (value, unit, year, currency), cagr_percent
- **Time**: study_period_start/end, temporal_coverage
- **Geography**: region, spatial_coverage, fastest_growing_country + CAGR
- **Segments**: JSON arrays for transaction_type, component, deployment, enterprise_size, end_user_industry, geography
- **Leading Segment**: name, share_percent, cagr
- **Cloud**: cloud_share_percent, cloud_share_year
- **Players**: major_players (JSON array)
- **Metadata**: description, page_date_published/modified, faq_questions_answers, image_urls
- **Tracking**: content_hash, first_seen_at, last_updated_at, scraped_at, version_count

### Table 2: `report_versions` (History)
Complete snapshot of every version:
- All fields from `reports` table (duplicated)
- **Version Metadata**: version_id, report_id, version_number, snapshot_reason, changed_fields, scraped_at

### Table 3: `scrape_log` (Operations)
Track every scrape attempt:
- **Identity**: log_id, run_id (UUID per run), report_url, report_slug
- **Status**: status, status_message, error_type
- **Metrics**: http_status_code, response_time_ms, html_size_bytes
- **Results**: fields_extracted, fields_changed, version_created
- **Timing**: started_at, completed_at, duration_seconds

## Database Output Examples

Here are concrete examples of what the data will look like in each table:

### Example 1: `reports` table (first scrape - Feb 2026)

Single row after scraping South America Real-Time Payments report:

| Field | Value |
|-------|-------|
| id | 1 |
| slug | south-america-real-time-payments-market |
| url | https://www.mordorintelligence.com/industry-reports/south-america-real-time-payments-market |
| title | South America Real Time Payments Market Size & Share Analysis... |
| market_size_current_value | 6.34 |
| market_size_current_unit | Trillion |
| market_size_current_year | 2026 |
| cagr_percent | 5.51 |
| market_size_forecast_value | 8.29 |
| market_size_forecast_year | 2031 |
| region | South America |
| fastest_growing_country | Colombia |
| fastest_growing_country_cagr | 7.41 |
| leading_segment_name | Retail and E-Commerce |
| leading_segment_share_percent | 33.67 |
| cloud_share_percent | 68.34 |
| major_players | `["ACI Worldwide Inc.", "Mastercard Inc.", "Visa Inc.", "Fiserv Inc.", "FIS"]` |
| page_date_modified | 2026-01-30 |
| content_hash | a7f3c2d8e4b1f9a6 |
| first_seen_at | 2026-02-01 02:15:23 |
| scraped_at | 2026-02-01 02:15:23 |
| version_count | 1 |

**After March 2026 scrape** (CAGR changed: 5.51% → 5.63%, Forecast: 8.29 → 8.35):

Changed fields:
- cagr_percent: **5.63**
- market_size_forecast_value: **8.35**
- content_hash: **b9e4d3a1c5f2b8d7**
- version_count: **2**
- scraped_at: **2026-03-01 02:18:41**

### Example 2: `report_versions` table

**Version 1 (Initial - Feb 2026)**:

```sql
SELECT version_id, report_id, version_number, snapshot_reason,
       changed_fields, cagr_percent, scraped_at
FROM report_versions WHERE report_id = 1 ORDER BY version_number;
```

| version_id | report_id | version_number | snapshot_reason | changed_fields | cagr_percent | scraped_at |
|-----------|-----------|----------------|-----------------|----------------|--------------|------------|
| 1 | 1 | 1 | new_report | null | 5.51 | 2026-02-01 02:15:23 |

**Version 2 (March 2026 - CAGR changed)**:

| version_id | report_id | version_number | snapshot_reason | changed_fields | cagr_percent | scraped_at |
|-----------|-----------|----------------|-----------------|----------------|--------------|------------|
| 2 | 1 | 2 | field_change | `["cagr_percent", "market_size_forecast_value", "page_date_modified"]` | 5.63 | 2026-03-01 02:18:41 |

**Complete version row** (showing all major fields):

```json
{
  "version_id": 2,
  "report_id": 1,
  "version_number": 2,
  "slug": "south-america-real-time-payments-market",
  "title": "South America Real Time Payments Market Size...",
  "market_size_current_value": 6.34,
  "market_size_forecast_value": 8.35,
  "cagr_percent": 5.63,
  "major_players": ["ACI Worldwide Inc.", "Mastercard Inc.", ...],
  "content_hash": "b9e4d3a1c5f2b8d7",
  "snapshot_reason": "field_change",
  "changed_fields": ["cagr_percent", "market_size_forecast_value"],
  "scraped_at": "2026-03-01T02:18:41"
}
```

### Example 3: `scrape_log` table

**Successful scrape**:

| Field | Value |
|-------|-------|
| log_id | 1523 |
| run_id | abc123-def456-789 |
| report_url | https://www.mordorintelligence.com/industry-reports/south-america... |
| report_slug | south-america-real-time-payments-market |
| status | success |
| status_message | Version created: 2 |
| http_status_code | 200 |
| response_time_ms | 1247 |
| html_size_bytes | 153018 |
| fields_extracted | 28 |
| fields_changed | 3 |
| version_created | true |
| started_at | 2026-03-01 02:18:39 |
| completed_at | 2026-03-01 02:18:41 |
| duration_seconds | 2.341 |

**Failed scrape** (404 error):

| Field | Value |
|-------|-------|
| status | error |
| error_type | http_error |
| status_message | 404 Client Error: Not Found |
| http_status_code | 404 |
| version_created | false |

### Example 4: Monthly Change Analysis Query

Find all reports that changed in March 2026:

```sql
SELECT
    r.slug,
    r.title,
    rv.changed_fields,
    r.cagr_percent as current_cagr,
    r.market_size_forecast_value as current_forecast
FROM reports r
JOIN report_versions rv ON r.id = rv.report_id
WHERE rv.scraped_at >= '2026-03-01'
  AND rv.scraped_at < '2026-04-01'
  AND rv.snapshot_reason = 'field_change'
ORDER BY rv.scraped_at DESC;
```

**Result**:

| slug | title | changed_fields | current_cagr | current_forecast |
|------|-------|----------------|--------------|------------------|
| south-america-real-time-payments-market | South America Real Time... | ["cagr_percent", "market_size_forecast_value"] | 5.63 | 8.35 |
| brazil-digital-payments-market | Brazil Digital Payments... | ["major_players"] | 12.4 | 45.2 |
| asia-pacific-fintech-market | Asia Pacific Fintech... | ["cloud_share_percent"] | 18.7 | 234.5 |

### Example 5: Export to CSV

Export current market snapshot:

```sql
COPY (
    SELECT
        slug,
        title,
        region,
        cagr_percent,
        market_size_current_value,
        market_size_forecast_value,
        fastest_growing_country,
        cloud_share_percent,
        json_extract(major_players, '$[0]') as top_player
    FROM reports
    ORDER BY cagr_percent DESC
) TO 'data/exports/market_snapshots/all_markets_2026-03.csv' (HEADER, DELIMITER ',');
```

**CSV Output**:

```csv
slug,title,region,cagr_percent,market_size_current_value,market_size_forecast_value,fastest_growing_country,cloud_share_percent,top_player
asia-pacific-fintech-market,Asia Pacific Fintech Market...,Asia-Pacific,18.70,123.40,234.50,India,72.10,PayPal Holdings Inc.
brazil-digital-payments-market,Brazil Digital Payments...,South America,12.40,28.90,45.20,Brazil,65.80,Mastercard Inc.
south-america-real-time-payments-market,South America Real Time...,South America,5.63,6.34,8.35,Colombia,68.34,ACI Worldwide Inc.
```

## Implementation Files

### 1. Database Schema
**File**: `src/database/schema.sql`
- Complete SQL schema for 3 tables
- Indexes on slug, content_hash, dates
- Foreign key: report_versions.report_id → reports.id

### 2. Enhanced Pydantic Models
**File**: `src/models/schema.py` (enhance existing)
- `Report`: Complete model with all fields
  - `compute_content_hash()`: SHA256 of all fields except scraped_at
  - `get_changed_fields(other)`: Compare with another Report
- `MarketSize`, `MajorPlayer`, `FAQPair`, `SegmentData`: Nested models
- `ReportVersion`: Historical snapshot
- `ScrapeLogEntry`: Operational log

### 3. JSON-LD Parser
**File**: `src/parsers/jsonld_parser.py`
- `JSONLDParser` class:
  - `__init__(html, url)`: Parse HTML, extract all JSON-LD blocks
  - `parse_report()`: Orchestrate parsing from all sources
  - `_parse_faq_page()`: Extract metrics from FAQPage
  - `_parse_dataset()`: Extract temporal/spatial coverage
  - `_parse_webpage()`: Extract publication dates
  - `_parse_images()`: Extract chart URLs
  - `_extract_market_sizes(text)`: Regex: "USD 6.34 trillion in 2026"
  - `_extract_cagr(text)`: Regex: "5.51% CAGR"
  - `_extract_major_players(text)`: Regex: Company names ending in Inc./Ltd./etc.
  - `_extract_fastest_growing(text)`: Regex: "Colombia (7.41% CAGR)"
  - `_extract_leading_segment(text)`: Regex: "Retail (33.67%, 6.27% CAGR)"
  - `_extract_cloud_share(text)`: Regex: "68.34% (2025)"

**File**: `src/parsers/regex_patterns.py`
- Compiled regex patterns for performance
- Helper functions for number/percentage extraction

### 4. URL Discovery
**File**: `src/scrapers/url_discovery.py`
- `discover_all_report_urls()`: Main function
  - Fetch https://www.mordorintelligence.com/market-analysis/payments
  - `extract_next_data(html)`: Parse `<script id="__NEXT_DATA__">` JSON
  - `extract_report_urls_from_page(data)`: Get URLs from props.pageProps.reports
  - `identify_api_endpoint(data)`: Find API URL (likely https://api-nextjs.mordorintelligence.com/api/v1/public/reports)
  - `fetch_api_page(client, endpoint, page_num)`: GET with params: ?category=payments&page=2&limit=30
  - Loop pages 2-6 to get remaining 113 reports
  - Deduplicate and validate URLs

### 5. Versioning Logic
**File**: `src/database/versioning.py`
- `VersionManager` class:
  - `__init__(db_path)`: Connect to DuckDB
  - `should_create_version(report)`: Check if hash changed → return (bool, reason, changed_fields)
  - `create_version(report, reason, changed_fields)`: Insert into report_versions, update reports table
  - `get_version_history(slug)`: Query all versions
  - `get_changes_between_versions(slug, v1, v2)`: Diff two versions
  - `_get_or_create_report_id(report)`: Lookup or insert new report
  - `_get_next_version_number(report_id)`: MAX(version_number) + 1
  - `_flatten_report(report)`: Convert nested Pydantic to flat dict for SQL

### 6. Main Scraper
**File**: `src/scrapers/report_scraper.py`
- `ReportScraper` class:
  - `__init__(db_path)`: Setup httpx client, VersionManager, generate run_id (UUID)
  - `run_full_scrape()`: Orchestrate full workflow
    - Call discover_all_report_urls()
    - Loop through URLs with asyncio
    - Track stats: successful, errors, new_reports, versions_created, no_changes
    - Rate limit: await asyncio.sleep(2.0) between requests
  - `scrape_report(url)`: Scrape single report
    - HTTP GET with httpx
    - Parse with JSONLDParser
    - Check for changes with VersionManager
    - Create version if needed
    - Log to scrape_log
    - Return result dict
  - Error handling:
    - Retry 429/503 with exponential backoff
    - Log 404 as "report_removed"
    - Catch parsing errors and log

### 7. CLI Interface
**File**: `src/cli.py`
- Click-based CLI:
  - `scrape`: Run full scrape of 153 reports
  - `init-db`: Initialize database schema
  - `history <slug>`: Show version history
  - `diff <slug> <v1> <v2>`: Show changes between versions

### 8. Validators
**File**: `src/validators/report_validator.py`
- `ReportValidator.validate(report)`: Data quality checks
  - Required fields: title, url
  - Market size > 0
  - CAGR in reasonable range (-50% to 100%)
  - Study period: end >= start, not in far future
  - Player count: 0-20 reasonable
  - Return {'errors': [...], 'warnings': [...]}

## Implementation Sequence

### Phase 1: Foundation
1. Create `src/database/schema.sql` with complete 3-table schema
2. Enhance `src/models/schema.py` with all models
3. Run `python -m src.cli init-db` to create database

### Phase 2: Parsing
4. Implement `src/parsers/jsonld_parser.py` with regex extraction
5. Create `src/parsers/regex_patterns.py`
6. Test with `data/raw/sample_report.html`

### Phase 3: Versioning
7. Implement `src/database/versioning.py`
8. Test change detection with sample data
9. Verify snapshots created correctly

### Phase 4: Scraping
10. Implement `src/scrapers/url_discovery.py`
11. Test URL extraction (should get all 153)
12. Implement `src/scrapers/report_scraper.py`
13. Add error handling and rate limiting

### Phase 5: Integration
14. Create `src/cli.py` with commands
15. Add `src/validators/report_validator.py`
16. Run end-to-end test
17. Set up monthly cron job

## Critical Technical Details

### URL Discovery Strategy
- Index page contains __NEXT_DATA__ JSON with first 40 reports
- Remaining 113 reports require API calls
- API likely at: `https://api-nextjs.mordorintelligence.com/api/v1/public/reports?category=payments&page=N`
- 6 total pages (40 + 23*5 = 155, some variance expected)

### Content Hash for Change Detection
```python
def compute_content_hash(self) -> str:
    content_dict = self.model_dump(exclude={'scraped_at'})
    content_json = json.dumps(content_dict, sort_keys=True, default=str)
    return hashlib.sha256(content_json.encode()).hexdigest()
```

### Regex Patterns
- Market size: `(?:USD|US\$)\s*([\d,.]+)\s*(billion|trillion)\s*(?:in|by)?\s*(\d{4})`
- CAGR: `(?:CAGR\s+of\s+)?([\d.]+)%`
- Company: `([A-Z][A-Za-z0-9\s&\-\.]+(?:Inc\.|Ltd\.|LLC|Corp\.))`
- Country + CAGR: `([A-Z][a-z]+)\s*\(?([\d.]+)%\s*CAGR\)?`

### Rate Limiting
- 2 seconds between requests (config.settings.REQUEST_DELAY)
- 153 reports = ~5 minutes total runtime
- Exponential backoff on 429: wait 5s, 10s, 20s, 40s, 80s

## Verification Steps

### After Phase 2 (Parsing):
```python
from src.parsers.jsonld_parser import JSONLDParser
html = open('data/raw/sample_report.html').read()
parser = JSONLDParser(html, 'https://www.mordorintelligence.com/industry-reports/south-america-real-time-payments-market')
report = parser.parse_report()
assert report.cagr_percent == 5.51
assert report.market_size_current.value == 6.34
assert 'Mastercard' in report.major_players
```

### After Phase 3 (Versioning):
```python
from src.database.versioning import VersionManager
vm = VersionManager('data/mordor.duckdb')
should_create, reason, fields = vm.should_create_version(report)
assert should_create == True
assert reason == 'new_report'
```

### After Phase 4 (Scraping):
```bash
python -m src.cli scrape
# Should output: "Found 153 report URLs"
# Check scrape_log: SELECT COUNT(*), status FROM scrape_log GROUP BY status
# Expect: ~153 success, <10 errors
```

### End-to-End Test:
```sql
-- Check reports table
SELECT COUNT(*) FROM reports;  -- Should be ~153

-- Check versions
SELECT snapshot_reason, COUNT(*) FROM report_versions GROUP BY snapshot_reason;
-- Expect mostly "new_report"

-- Check for parsing completeness
SELECT
    AVG(CASE WHEN cagr_percent IS NOT NULL THEN 1 ELSE 0 END) as cagr_coverage,
    AVG(CASE WHEN major_players IS NOT NULL THEN 1 ELSE 0 END) as players_coverage
FROM reports;
-- Expect >90% coverage
```

## Monthly Workflow

**Cron Job**:
```bash
0 2 1 * * cd /Users/JackRobertson/mordor-intelligence && venv/bin/python -m src.cli scrape >> logs/scrape_$(date +\%Y\%m).log 2>&1
```

**Manual Run**:
```bash
cd /Users/JackRobertson/mordor-intelligence
source venv/bin/activate
python -m src.cli scrape
```

**Review Changes**:
```bash
python -m src.cli history south-america-real-time-payments-market
python -m src.cli diff south-america-real-time-payments-market 1 2
```

## Files to Create (in order)

1. `src/database/__init__.py` (empty)
2. `src/database/schema.sql` (450 lines)
3. `src/models/schema.py` (enhance, +300 lines)
4. `src/parsers/regex_patterns.py` (50 lines)
5. `src/parsers/jsonld_parser.py` (500 lines)
6. `src/database/versioning.py` (400 lines)
7. `src/scrapers/url_discovery.py` (200 lines)
8. `src/scrapers/report_scraper.py` (300 lines)
9. `src/validators/__init__.py` (empty)
10. `src/validators/report_validator.py` (150 lines)
11. `src/cli.py` (150 lines)

Total: ~2500 lines of production code

## Success Criteria

- ✅ All 153 report URLs discovered
- ✅ >95% of reports successfully parsed
- ✅ All key fields extracted: market_size, cagr, players, segments
- ✅ Versions created on every field change
- ✅ Content hash correctly detects changes
- ✅ Database stores complete snapshots
- ✅ CLI commands work for scraping and history
- ✅ Monthly cron job runs successfully
- ✅ Error logs show <5% failure rate

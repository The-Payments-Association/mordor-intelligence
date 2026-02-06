# Mordor Intelligence Scraper - Quick Start Guide

## Overview
Complete production-ready scraper for 153 payment market reports with:
- ✅ Full versioning & change tracking
- ✅ Content hashing for change detection
- ✅ JSON-LD data extraction
- ✅ DuckDB storage with 3 tables
- ✅ Comprehensive data validation

## Setup

### 1. Initialize Database
```bash
venv/bin/python -m src.cli init-db
```

Creates 3 tables:
- `reports`: Current state of all 153 reports
- `report_versions`: Complete historical snapshots
- `scrape_log`: Operational logs

### 2. Run Full Scrape
```bash
venv/bin/python -m src.cli scrape
```

Scrapes all 153 reports with:
- Rate limiting (2s delay)
- Error handling and retries
- Change detection
- Version snapshots on changes

### 3. Check Results
```bash
venv/bin/python -m src.cli stats        # See overall stats
venv/bin/python -m src.cli show <slug>  # View specific report
venv/bin/python -m src.cli history <slug>      # See version history
venv/bin/python -m src.cli diff <slug> 1 2    # Compare versions
```

## File Structure

### Source Code
```
src/
├── models/
│   └── schema.py              # Pydantic models (Report, ReportVersion, ScrapeLogEntry)
├── parsers/
│   ├── regex_patterns.py      # Regex patterns for data extraction
│   └── jsonld_parser.py       # JSON-LD parser for report pages
├── database/
│   ├── schema.sql             # DuckDB schema
│   └── versioning.py          # Version management & change detection
├── scrapers/
│   ├── url_discovery.py       # Discover 153 report URLs
│   └── report_scraper.py      # Main scraper with async support
├── validators/
│   └── report_validator.py    # Data quality validation
└── cli.py                     # CLI commands

config/
└── settings.py                # Configuration (paths, URLs, delays)

test_implementation.py          # Test suite
```

### Data Directories (Created Automatically)
```
data/
├── raw/
│   ├── 2026-02/               # Monthly HTML snapshots
│   │   ├── index_20260201.html
│   │   └── market_name_20260201.html
│   └── latest/                # Symlinks to latest
├── processed/
│   └── runs/
│       └── 2026-02-01_run-abc123/
│           ├── reports.jsonl  # All parsed reports
│           ├── errors.json    # Parse errors
│           └── summary.json   # Run statistics
├── exports/                   # Future: analysis exports
└── mordor.duckdb              # Main database
```

## Database Schema

### reports (Current State)
- `id`, `slug`, `url`, `title`, `description`
- Market sizing: `market_size_current_*`, `market_size_forecast_*`, `cagr_percent`
- Geography: `region`, `spatial_coverage`, `fastest_growing_country`, `fastest_growing_country_cagr`
- Leading segment: `leading_segment_name`, `leading_segment_share_percent`, `leading_segment_cagr`
- Deployment: `cloud_share_percent`
- Segments: `transaction_types`, `components`, `deployment_types`, etc. (JSON arrays)
- Players: `major_players` (JSON array)
- Metadata: `page_date_published`, `page_date_modified`, `faq_questions_answers`, `image_urls`
- Tracking: `content_hash`, `first_seen_at`, `last_updated_at`, `scraped_at`, `version_count`

### report_versions (History)
Complete snapshot of all fields from reports + version metadata:
- `report_id`, `version_number`, `snapshot_reason`, `changed_fields`, `scraped_at`

### scrape_log (Operations)
Every scrape attempt:
- `run_id`, `report_url`, `report_slug`, `status`, `error_type`
- Metrics: `http_status_code`, `response_time_ms`, `html_size_bytes`
- Results: `fields_extracted`, `fields_changed`, `version_created`
- Timing: `started_at`, `completed_at`, `duration_seconds`

## Key Features

### 1. Change Detection
- Computes SHA256 hash of all fields (excluding timestamp fields)
- Automatically detects when a report changes
- Creates new version with list of changed fields

```python
report.content_hash = report.compute_content_hash()
changed_fields = report.get_changed_fields(previous_report)
```

### 2. Data Extraction
Extracts from JSON-LD structured data:
- **FAQPage**: Key metrics in Q&A format
- **Dataset**: Temporal and spatial coverage
- **WebPage**: Publication dates
- **ImageObject**: Chart URLs

Uses regex patterns for parsing FAQ answers:
- Market sizes: "USD 6.34 trillion in 2026"
- CAGR: "5.51% CAGR"
- Companies: "Mastercard Inc.", "Visa Ltd.", etc.
- Fastest growing: "Brazil at 18.5% CAGR"
- Cloud share: "68.34% of the market"

### 3. Versioning
Every field change creates a snapshot:
```sql
-- See what changed between versions
SELECT * FROM report_versions
WHERE report_id = 1
ORDER BY version_number;

-- Find all changed reports in March
SELECT r.slug, rv.changed_fields
FROM reports r
JOIN report_versions rv ON r.id = rv.report_id
WHERE rv.scraped_at >= '2026-03-01'
  AND rv.snapshot_reason = 'field_change';
```

### 4. Validation
Automatic data quality checks:
- Required fields present
- Market size > 0
- CAGR in reasonable range (-100% to 100%)
- Study period valid
- Player count reasonable

## Monthly Workflow

### Automated (via cron)
```bash
0 2 1 * * cd /Users/JackRobertson/mordor-intelligence && venv/bin/python -m src.cli scrape
```

### Manual
```bash
# Run scrape
venv/bin/python -m src.cli scrape

# Check for changes
venv/bin/python -m src.cli history south-america-real-time-payments-market
venv/bin/python -m src.cli diff south-america-real-time-payments-market 1 2

# Export data
sqlite3 data/mordor.duckdb "SELECT * FROM reports WHERE cagr_percent > 10 ORDER BY cagr_percent DESC;" > exports/high_growth.csv
```

## Example Queries

### Top 10 Fastest Growing Markets
```sql
SELECT slug, cagr_percent, market_size_forecast_value, region
FROM reports
WHERE cagr_percent IS NOT NULL
ORDER BY cagr_percent DESC
LIMIT 10;
```

### Reports That Changed This Month
```sql
SELECT r.slug, COUNT(DISTINCT rv.version_number) as versions,
       rv.changed_fields, rv.scraped_at
FROM reports r
JOIN report_versions rv ON r.id = rv.report_id
WHERE rv.scraped_at >= date('now', 'start of month')
GROUP BY r.id
ORDER BY rv.scraped_at DESC;
```

### Cloud Share Trends
```sql
SELECT
    region,
    AVG(cloud_share_percent) as avg_cloud_share,
    MIN(cloud_share_percent) as min_cloud,
    MAX(cloud_share_percent) as max_cloud,
    COUNT(*) as market_count
FROM reports
WHERE cloud_share_percent IS NOT NULL
GROUP BY region
ORDER BY avg_cloud_share DESC;
```

## Testing

Run comprehensive test suite:
```bash
venv/bin/python test_implementation.py
```

Tests:
- ✅ Pydantic models
- ✅ Regex pattern extraction
- ✅ JSON-LD parser
- ✅ Data validators
- ✅ Versioning & change detection

## Performance

- **Per report**: ~2-5 seconds (includes 2s rate limit)
- **All 153 reports**: ~8-15 minutes (with 5 concurrent workers)
- **Database size**: ~50-100 MB for complete history
- **Parsed data**: ~5-10 MB per month

## Architecture Notes

### URL Discovery
- Index page (__NEXT_DATA__): 40 reports
- API calls (pages 2-6): 113 reports
- Total: 153 payment market reports

### Content Hashing
SHA256 of all fields except:
- `scraped_at` (always changes)
- `first_seen_at`, `last_updated_at` (tracking fields)
- `content_hash`, `version_count` (derived fields)

### Storage Strategy
- Raw HTML: For audit trail & re-parsing
- Processed JSONL: For debugging & re-import
- DuckDB: For querying & analysis
- Exports: For external tools (Excel, BI, etc.)

## Troubleshooting

### Q: "Failed to discover URLs"
A: The API endpoint might have changed. Check `src/scrapers/url_discovery.py` for the list of API endpoints.

### Q: "Parse errors for many reports"
A: Mordor Intelligence might have changed their page structure. Check a sample HTML and update the JSON-LD parser.

### Q: "Transaction errors"
A: DuckDB auto-commits. Remove explicit commit/rollback calls or use begin/end transactions properly.

### Q: "Memory usage high"
A: Reduce `max_concurrent` workers when calling `run_full_scrape()` (default: 5, try 2-3).

## Next Steps

1. **Monthly execution**: Set up cron job to run scrapes automatically
2. **Analysis dashboard**: Export to Tableau/Power BI for visualization
3. **Alerting**: Monitor for significant CAGR changes or new major players
4. **Archival**: Archive old HTML snapshots monthly to keep data/raw/ manageable

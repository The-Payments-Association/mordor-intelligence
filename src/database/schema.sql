-- DuckDB Schema for Mordor Intelligence Payments Market Reports
-- 3 main tables: reports (current), report_versions (history), scrape_log (operations)

-- Table 1: reports - Current state of all 153 reports
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    slug VARCHAR UNIQUE NOT NULL,
    url VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,

    -- Market Sizing
    market_size_current_value DECIMAL(20, 4),
    market_size_current_unit VARCHAR,
    market_size_current_year INTEGER,
    market_size_current_currency VARCHAR DEFAULT 'USD',

    market_size_forecast_value DECIMAL(20, 4),
    market_size_forecast_unit VARCHAR,
    market_size_forecast_year INTEGER,
    market_size_forecast_currency VARCHAR DEFAULT 'USD',

    -- CAGR & Growth
    cagr_percent DECIMAL(8, 4),

    -- Time periods
    study_period_start INTEGER,
    study_period_end INTEGER,
    temporal_coverage VARCHAR,

    -- Geography
    region VARCHAR,
    spatial_coverage VARCHAR,
    fastest_growing_country VARCHAR,
    fastest_growing_country_cagr DECIMAL(8, 4),

    -- Leading Segment
    leading_segment_name VARCHAR,
    leading_segment_share_percent DECIMAL(8, 4),
    leading_segment_cagr DECIMAL(8, 4),

    -- Cloud/Deployment
    cloud_share_percent DECIMAL(8, 4),
    cloud_share_year INTEGER,

    -- Segments (JSON arrays)
    transaction_types VARCHAR,
    components VARCHAR,
    deployment_types VARCHAR,
    enterprise_sizes VARCHAR,
    end_user_industries VARCHAR,
    geographies VARCHAR,

    -- Players
    major_players VARCHAR,

    -- Page metadata
    page_date_published TIMESTAMP,
    page_date_modified TIMESTAMP,

    -- FAQ and Images
    faq_questions_answers VARCHAR,
    image_urls VARCHAR,

    -- Tracking
    content_hash VARCHAR(64) NOT NULL,
    first_seen_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    last_updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    scraped_at TIMESTAMP NOT NULL,
    version_count INTEGER DEFAULT 1
);

-- Indexes on reports
CREATE INDEX IF NOT EXISTS idx_reports_slug ON reports(slug);
CREATE INDEX IF NOT EXISTS idx_reports_content_hash ON reports(content_hash);
CREATE INDEX IF NOT EXISTS idx_reports_scraped_at ON reports(scraped_at);
CREATE INDEX IF NOT EXISTS idx_reports_region ON reports(region);

-- Table 2: report_versions - Complete historical snapshots
CREATE TABLE IF NOT EXISTS report_versions (
    version_id INTEGER PRIMARY KEY,
    report_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,

    -- Full snapshot of all report fields
    slug VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,

    market_size_current_value DECIMAL(20, 4),
    market_size_current_unit VARCHAR,
    market_size_current_year INTEGER,
    market_size_current_currency VARCHAR,

    market_size_forecast_value DECIMAL(20, 4),
    market_size_forecast_unit VARCHAR,
    market_size_forecast_year INTEGER,
    market_size_forecast_currency VARCHAR,

    cagr_percent DECIMAL(8, 4),
    study_period_start INTEGER,
    study_period_end INTEGER,
    temporal_coverage VARCHAR,

    region VARCHAR,
    spatial_coverage VARCHAR,
    fastest_growing_country VARCHAR,
    fastest_growing_country_cagr DECIMAL(8, 4),

    leading_segment_name VARCHAR,
    leading_segment_share_percent DECIMAL(8, 4),
    leading_segment_cagr DECIMAL(8, 4),

    cloud_share_percent DECIMAL(8, 4),
    cloud_share_year INTEGER,

    transaction_types VARCHAR,
    components VARCHAR,
    deployment_types VARCHAR,
    enterprise_sizes VARCHAR,
    end_user_industries VARCHAR,
    geographies VARCHAR,

    major_players VARCHAR,

    page_date_published TIMESTAMP,
    page_date_modified TIMESTAMP,
    faq_questions_answers VARCHAR,
    image_urls VARCHAR,

    -- Version metadata
    content_hash VARCHAR(64) NOT NULL,
    snapshot_reason VARCHAR NOT NULL,
    changed_fields VARCHAR,
    scraped_at TIMESTAMP NOT NULL,

    UNIQUE (report_id, version_number)
);

-- Indexes on report_versions
CREATE INDEX IF NOT EXISTS idx_versions_report_id ON report_versions(report_id);
CREATE INDEX IF NOT EXISTS idx_versions_snapshot_reason ON report_versions(snapshot_reason);
CREATE INDEX IF NOT EXISTS idx_versions_scraped_at ON report_versions(scraped_at);

-- Table 3: scrape_log - Operational logs
CREATE TABLE IF NOT EXISTS scrape_log (
    log_id INTEGER PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    report_url VARCHAR NOT NULL,
    report_slug VARCHAR,

    -- Status
    status VARCHAR NOT NULL,
    status_message VARCHAR,
    error_type VARCHAR,

    -- HTTP metrics
    http_status_code INTEGER,
    response_time_ms INTEGER,
    html_size_bytes INTEGER,

    -- Results
    fields_extracted INTEGER,
    fields_changed INTEGER,
    version_created BOOLEAN,

    -- Timing
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds DECIMAL(10, 3),

    -- Metadata
    retry_count INTEGER DEFAULT 0
);

-- Indexes on scrape_log
CREATE INDEX IF NOT EXISTS idx_scrape_log_run_id ON scrape_log(run_id);
CREATE INDEX IF NOT EXISTS idx_scrape_log_status ON scrape_log(status);
CREATE INDEX IF NOT EXISTS idx_scrape_log_started_at ON scrape_log(started_at);

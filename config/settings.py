"""Project settings and constants."""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"

# URLs
BASE_URL = "https://www.mordorintelligence.com"
PAYMENTS_INDEX = f"{BASE_URL}/market-analysis/payments"
REPORT_PREFIX = f"{BASE_URL}/industry-reports/"

# Scraping
REQUEST_DELAY = 2.0  # seconds between requests
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Database
DB_PATH = DATA_DIR / "mordor.duckdb"

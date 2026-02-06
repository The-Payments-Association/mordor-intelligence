"""
Main scraper for 153 payment market reports.
Fetches, parses, detects changes, and stores to DuckDB with versioning.
"""

import asyncio
import httpx
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from config.settings import (
    BASE_DIR, DATA_DIR, RAW_DIR, PROCESSED_DIR,
    USER_AGENT, REQUEST_DELAY, DB_PATH
)

from src.models.schema import Report, ScrapeLogEntry
from src.parsers.jsonld_parser import JSONLDParser
from src.database.versioning import VersionManager
from src.scrapers.url_discovery import discover_all_report_urls


class ReportScraper:
    """Scrape payment market reports with versioning and change detection."""

    def __init__(self, db_path: str = str(DB_PATH)):
        """
        Initialize scraper.

        Args:
            db_path: Path to DuckDB database
        """
        self.db_path = db_path
        self.version_manager = VersionManager(db_path)
        self.run_id = str(uuid.uuid4())
        self.start_time = datetime.utcnow()

        # Create data directories
        self._create_directories()

        # Statistics
        self.stats = {
            'total_urls': 0,
            'successful': 0,
            'errors': 0,
            'new_reports': 0,
            'versions_created': 0,
            'no_changes': 0,
        }

    def _create_directories(self):
        """Create necessary data directories."""
        for dir_path in [RAW_DIR, PROCESSED_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create date-based subdirectory
        date_str = datetime.now().strftime('%Y-%m')
        (RAW_DIR / date_str).mkdir(parents=True, exist_ok=True)
        (PROCESSED_DIR / 'runs').mkdir(parents=True, exist_ok=True)

    async def run_full_scrape(self, max_concurrent: int = 5) -> Dict[str, Any]:
        """
        Execute full scrape of all 153 reports.

        Args:
            max_concurrent: Maximum concurrent HTTP requests

        Returns:
            Statistics dict with results
        """
        print(f"Starting full scrape (run_id: {self.run_id})")

        # Discover URLs
        try:
            urls = await discover_all_report_urls()
            self.stats['total_urls'] = len(urls)
            print(f"Found {len(urls)} report URLs")
        except Exception as e:
            print(f"ERROR discovering URLs: {e}")
            return self.stats

        # Scrape reports concurrently
        async with httpx.AsyncClient(timeout=30.0) as client:
            semaphore = asyncio.Semaphore(max_concurrent)

            tasks = [
                self._scrape_report_with_semaphore(client, url, semaphore)
                for url in urls
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        parsed_reports = []
        for result in results:
            if isinstance(result, Exception):
                self.stats['errors'] += 1
                continue

            if result:
                parsed_reports.append(result)
                self.stats['successful'] += 1

        # Save processed data
        self._save_processed_reports(parsed_reports)

        # Print summary
        print(f"\nScrape complete:")
        print(f"  Successful: {self.stats['successful']}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"  New reports: {self.stats['new_reports']}")
        print(f"  Versions created: {self.stats['versions_created']}")
        print(f"  No changes: {self.stats['no_changes']}")

        return self.stats

    async def _scrape_report_with_semaphore(
        self,
        client: httpx.AsyncClient,
        url: str,
        semaphore: asyncio.Semaphore
    ) -> Optional[Report]:
        """Scrape report with semaphore for rate limiting."""
        async with semaphore:
            await asyncio.sleep(REQUEST_DELAY)
            return await self.scrape_report(client, url)

    async def scrape_report(self, client: httpx.AsyncClient, url: str) -> Optional[Report]:
        """
        Scrape and parse a single report.

        Args:
            client: httpx AsyncClient
            url: Report URL

        Returns:
            Parsed Report instance or None on error
        """
        log_entry = ScrapeLogEntry(
            run_id=self.run_id,
            report_url=url,
            status='pending',
            started_at=datetime.utcnow(),
        )

        start_time = datetime.utcnow()

        try:
            # Fetch HTML
            response = await client.get(
                url,
                headers={'User-Agent': USER_AGENT}
            )
            response.raise_for_status()

            response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            html_size = len(response.content)

            log_entry.http_status_code = response.status_code
            log_entry.response_time_ms = response_time_ms
            log_entry.html_size_bytes = html_size

            # Save raw HTML
            self._save_raw_html(url, response.text)

            # Parse report
            parser = JSONLDParser(response.text, url)
            report = parser.parse_report()
            report.scraped_at = datetime.utcnow()

            log_entry.report_slug = report.slug
            log_entry.fields_extracted = self._count_non_none_fields(report)

            # Check for changes
            should_create, reason, changed_fields = self.version_manager.should_create_version(report)

            if should_create:
                # Create version
                self.version_manager.create_version(report, reason, changed_fields)

                log_entry.version_created = True
                log_entry.fields_changed = len(changed_fields) if changed_fields else 0

                if reason == "new_report":
                    self.stats['new_reports'] += 1
                    log_entry.status = 'success'
                    log_entry.status_message = f"New report created"
                else:
                    log_entry.status = 'success'
                    log_entry.status_message = f"Version {self.version_manager._get_next_version_number(self.version_manager._get_or_create_report_id(report))-1} created"
                    self.stats['versions_created'] += 1
            else:
                self.stats['no_changes'] += 1
                log_entry.status = 'skipped'
                log_entry.status_message = 'No changes detected'

            # Save log entry
            self._save_log_entry(log_entry)

            return report if should_create else None

        except httpx.HTTPStatusError as e:
            log_entry.status = 'error'
            log_entry.error_type = 'http_error'
            log_entry.http_status_code = e.response.status_code

            if e.response.status_code == 404:
                log_entry.status_message = 'Report not found (404)'
            elif e.response.status_code == 429:
                log_entry.status_message = 'Rate limited (429)'
            else:
                log_entry.status_message = str(e)

            self._save_log_entry(log_entry)
            return None

        except Exception as e:
            log_entry.status = 'error'
            log_entry.error_type = 'parse_error'
            log_entry.status_message = str(e)
            self._save_log_entry(log_entry)
            return None

        finally:
            log_entry.completed_at = datetime.utcnow()
            log_entry.duration_seconds = (
                log_entry.completed_at - log_entry.started_at
            ).total_seconds()

    def _save_raw_html(self, url: str, html: str):
        """Save raw HTML to data/raw/ for audit trail."""
        # Extract slug from URL
        slug = url.rstrip('/').split('/')[-1]
        date_str = datetime.now().strftime('%Y-%m')
        date_prefix = datetime.now().strftime('%Y%m%d')

        file_path = RAW_DIR / date_str / f"{slug}_{date_prefix}.html"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
        except Exception as e:
            print(f"Warning: Failed to save raw HTML for {slug}: {e}")

    def _save_processed_reports(self, reports: List[Report]):
        """Save processed reports as JSONL."""
        if not reports:
            return

        run_dir = PROCESSED_DIR / 'runs' / f"{datetime.now().strftime('%Y-%m-%d')}_{self.run_id[:8]}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save as JSONL
        jsonl_file = run_dir / 'reports.jsonl'
        try:
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                for report in reports:
                    f.write(json.dumps(report.model_dump(mode='json'), default=str) + '\n')
        except Exception as e:
            print(f"Warning: Failed to save processed reports: {e}")

        # Save summary
        summary_file = run_dir / 'summary.json'
        try:
            summary = {
                'run_id': self.run_id,
                'timestamp': datetime.utcnow().isoformat(),
                'total_reports': len(reports),
                'stats': self.stats
            }
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to save summary: {e}")

    def _save_log_entry(self, entry: ScrapeLogEntry):
        """Save log entry to scrape_log table."""
        try:
            # Generate log_id manually (max id + 1)
            max_id_result = self.version_manager.conn.execute(
                "SELECT COALESCE(MAX(log_id), 0) FROM scrape_log"
            ).fetchone()
            log_id = (max_id_result[0] if max_id_result else 0) + 1

            # Insert into database
            query = """
                INSERT INTO scrape_log
                (log_id, run_id, report_url, report_slug, status, status_message, error_type,
                 http_status_code, response_time_ms, html_size_bytes,
                 fields_extracted, fields_changed, version_created,
                 started_at, completed_at, duration_seconds, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.version_manager.conn.execute(query, [
                log_id,
                entry.run_id,
                entry.report_url,
                entry.report_slug,
                entry.status,
                entry.status_message,
                entry.error_type,
                entry.http_status_code,
                entry.response_time_ms,
                entry.html_size_bytes,
                entry.fields_extracted,
                entry.fields_changed,
                entry.version_created,
                entry.started_at,
                entry.completed_at,
                entry.duration_seconds,
                entry.retry_count,
            ])
            self.version_manager.conn.commit()

        except Exception as e:
            print(f"Warning: Failed to save log entry: {e}")

    def _count_non_none_fields(self, report: Report) -> int:
        """Count non-None fields in report."""
        count = 0
        for field in report.model_fields.keys():
            if getattr(report, field) is not None:
                count += 1
        return count


async def run_scrape():
    """CLI entry point for scraping."""
    scraper = ReportScraper()
    return await scraper.run_full_scrape()

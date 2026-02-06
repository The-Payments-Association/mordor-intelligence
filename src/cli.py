"""
CLI interface for Mordor Intelligence scraper.
Commands: scrape, init-db, history, diff
"""

import click
import asyncio
import duckdb
from pathlib import Path
from datetime import datetime

from config.settings import DB_PATH, RAW_DIR
from src.scrapers.report_scraper import run_scrape, ReportScraper
from src.database.versioning import VersionManager


@click.group()
def cli():
    """Mordor Intelligence Payment Market Scraper."""
    pass


@cli.command()
@click.option('--db', default=str(DB_PATH), help='Database path')
@click.option('--workers', default=5, help='Maximum concurrent requests')
def scrape(db: str, workers: int):
    """Run full scrape of all 153 payment market reports."""
    click.echo(f"Starting scrape... (database: {db}, workers: {workers})")

    try:
        stats = asyncio.run(_run_scrape_async(db, workers))

        click.echo("\n✓ Scrape completed!")
        click.echo(f"  Successful: {stats['successful']}")
        click.echo(f"  Errors: {stats['errors']}")
        click.echo(f"  New reports: {stats['new_reports']}")
        click.echo(f"  Versions created: {stats['versions_created']}")
        click.echo(f"  No changes: {stats['no_changes']}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        exit(1)


async def _run_scrape_async(db_path: str, workers: int) -> dict:
    """Run scraper asynchronously."""
    scraper = ReportScraper(db_path)
    return await scraper.run_full_scrape(max_concurrent=workers)


@cli.command()
@click.option('--db', default=str(DB_PATH), help='Database path')
def init_db(db: str):
    """Initialize database schema."""
    click.echo(f"Initializing database: {db}")

    db_path = Path(db)
    schema_file = Path(__file__).parent / 'database' / 'schema.sql'

    if not schema_file.exists():
        click.echo(f"✗ Schema file not found: {schema_file}", err=True)
        exit(1)

    try:
        # Read schema
        with open(schema_file, 'r') as f:
            schema = f.read()

        # Execute schema
        conn = duckdb.connect(str(db_path))
        conn.execute(schema)
        conn.commit()
        conn.close()

        click.echo("✓ Database initialized successfully!")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        exit(1)


@cli.command()
@click.argument('slug')
@click.option('--db', default=str(DB_PATH), help='Database path')
def history(slug: str, db: str):
    """Show version history for a report."""
    try:
        vm = VersionManager(db)
        versions = vm.get_version_history(slug)

        if not versions:
            click.echo(f"No versions found for {slug}")
            return

        click.echo(f"\nHistory for {slug}:")
        click.echo("-" * 80)

        for version in versions:
            click.echo(f"\nVersion {version.get('version_number')}:")
            click.echo(f"  Reason: {version.get('snapshot_reason')}")
            click.echo(f"  Date: {version.get('scraped_at')}")
            changed = version.get('changed_fields')
            if changed:
                if isinstance(changed, list):
                    click.echo(f"  Changed fields: {', '.join(changed)}")
                elif isinstance(changed, str):
                    click.echo(f"  Changed fields: {changed}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        exit(1)


@cli.command()
@click.argument('slug')
@click.argument('v1', type=int)
@click.argument('v2', type=int)
@click.option('--db', default=str(DB_PATH), help='Database path')
def diff(slug: str, v1: int, v2: int, db: str):
    """Show changes between two versions."""
    try:
        vm = VersionManager(db)
        changes = vm.get_changes_between_versions(slug, v1, v2)

        if not changes:
            click.echo(f"No changes between version {v1} and {v2}")
            return

        click.echo(f"\nChanges from version {v1} to {v2} ({slug}):")
        click.echo("-" * 80)

        for field, (old_val, new_val) in sorted(changes.items()):
            click.echo(f"\n{field}:")
            click.echo(f"  OLD: {old_val}")
            click.echo(f"  NEW: {new_val}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        exit(1)


@cli.command()
@click.option('--db', default=str(DB_PATH), help='Database path')
def stats(db: str):
    """Show database statistics."""
    try:
        conn = duckdb.connect(db)

        # Report count
        report_count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        click.echo(f"Total reports: {report_count}")

        # Version count
        version_count = conn.execute("SELECT COUNT(*) FROM report_versions").fetchone()[0]
        click.echo(f"Total versions: {version_count}")

        # Scrape log count
        log_count = conn.execute("SELECT COUNT(*) FROM scrape_log").fetchone()[0]
        click.echo(f"Log entries: {log_count}")

        # Success rate
        success_count = conn.execute(
            "SELECT COUNT(*) FROM scrape_log WHERE status = 'success'"
        ).fetchone()[0]
        success_rate = (success_count / log_count * 100) if log_count > 0 else 0
        click.echo(f"Success rate: {success_rate:.1f}%")

        # Recent scrapes
        recent = conn.execute("""
            SELECT COUNT(DISTINCT run_id) FROM scrape_log
            WHERE started_at > current_timestamp - INTERVAL 7 day
        """).fetchone()[0]
        click.echo(f"Runs in last 7 days: {recent}")

        conn.close()

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        exit(1)


@cli.command()
@click.argument('slug')
@click.option('--db', default=str(DB_PATH), help='Database path')
def show(slug: str, db: str):
    """Show current report data."""
    try:
        conn = duckdb.connect(db)

        result = conn.execute(
            "SELECT * FROM reports WHERE slug = ?",
            [slug]
        ).fetchone()

        if not result:
            click.echo(f"Report not found: {slug}")
            return

        # Get column names
        columns = [desc[0] for desc in conn.description]

        click.echo(f"\nReport: {slug}")
        click.echo("-" * 80)

        for col, val in zip(columns, result):
            if val is not None:
                # Truncate long values
                val_str = str(val)
                if len(val_str) > 60:
                    val_str = val_str[:60] + "..."
                click.echo(f"{col:30s} {val_str}")

        conn.close()

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        exit(1)


if __name__ == '__main__':
    cli()

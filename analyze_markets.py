#!/usr/bin/env python
"""
Market Analysis Dashboard - Interactive CLI for exploring report data
"""

import duckdb
from tabulate import tabulate
import json

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def show_top_markets(limit=15):
    """Show top markets by CAGR"""
    conn = duckdb.connect('data/mordor.duckdb')

    result = conn.execute("""
        SELECT
            slug,
            cagr_percent,
            market_size_current_value,
            market_size_current_unit,
            region
        FROM reports
        WHERE cagr_percent IS NOT NULL
        ORDER BY cagr_percent DESC
        LIMIT ?
    """, [limit]).fetchall()

    conn.close()

    print_section(f"🚀 TOP {limit} MARKETS BY GROWTH (CAGR)")

    table_data = []
    for i, (slug, cagr, size, unit, region) in enumerate(result, 1):
        table_data.append([
            i,
            slug[:35],
            f"{cagr:.2f}%",
            f"{size} {unit}",
            region or "N/A"
        ])

    print(tabulate(table_data,
                   headers=["#", "Market", "CAGR", "Current Size", "Region"],
                   tablefmt="grid"))

def show_by_region():
    """Show markets grouped by region"""
    conn = duckdb.connect('data/mordor.duckdb')

    result = conn.execute("""
        SELECT
            region,
            COUNT(*) as count,
            ROUND(AVG(cagr_percent), 2) as avg_cagr,
            MAX(cagr_percent) as max_cagr
        FROM reports
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY avg_cagr DESC
    """).fetchall()

    conn.close()

    print_section("🌍 MARKETS BY REGION")

    table_data = []
    for region, count, avg_cagr, max_cagr in result:
        table_data.append([
            region,
            count,
            f"{avg_cagr:.2f}%",
            f"{max_cagr:.2f}%"
        ])

    print(tabulate(table_data,
                   headers=["Region", "Markets", "Avg CAGR", "Max CAGR"],
                   tablefmt="grid"))

def show_data_quality():
    """Show data extraction quality"""
    conn = duckdb.connect('data/mordor.duckdb')

    total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    cagr_count = conn.execute("SELECT COUNT(*) FROM reports WHERE cagr_percent IS NOT NULL").fetchone()[0]
    size_count = conn.execute("SELECT COUNT(*) FROM reports WHERE market_size_current_value IS NOT NULL").fetchone()[0]
    players_count = conn.execute("SELECT COUNT(*) FROM reports WHERE major_players IS NOT NULL").fetchone()[0]

    conn.close()

    print_section("📊 DATA EXTRACTION QUALITY")

    table_data = [
        ["CAGR %", f"{cagr_count}/{total}", f"{100*cagr_count//total}%"],
        ["Market Size", f"{size_count}/{total}", f"{100*size_count//total}%"],
        ["Major Players", f"{players_count}/{total}", f"{100*players_count//total}%"],
    ]

    print(tabulate(table_data,
                   headers=["Field", "Extracted", "Coverage"],
                   tablefmt="grid"))

def show_market_details(slug):
    """Show detailed info for a specific market"""
    conn = duckdb.connect('data/mordor.duckdb')

    result = conn.execute("""
        SELECT
            title,
            cagr_percent,
            market_size_current_value,
            market_size_current_unit,
            market_size_forecast_value,
            market_size_forecast_unit,
            region,
            fastest_growing_country,
            fastest_growing_country_cagr,
            cloud_share_percent,
            major_players
        FROM reports
        WHERE slug = ?
    """, [slug]).fetchone()

    conn.close()

    if not result:
        print(f"❌ Market not found: {slug}")
        return

    (title, cagr, curr_size, curr_unit, forecast_size, forecast_unit,
     region, fastest, fastest_cagr, cloud, players) = result

    print_section(title)

    print(f"📈 GROWTH METRICS:")
    print(f"   Current CAGR: {cagr}%")
    if fastest:
        print(f"   Fastest Growing: {fastest} ({fastest_cagr}% CAGR)")
    print()

    print(f"💰 MARKET SIZE:")
    print(f"   Current: {curr_size} {curr_unit}")
    if forecast_size:
        print(f"   Forecast: {forecast_size} {forecast_unit}")
    print()

    print(f"🌍 GEOGRAPHY:")
    print(f"   Region: {region or 'N/A'}")
    print()

    if cloud:
        print(f"☁️ CLOUD DEPLOYMENT: {cloud}%")
        print()

    if players:
        players = json.loads(players) if isinstance(players, str) else players
        print(f"🏢 MAJOR PLAYERS: {', '.join(players)}")

def show_version_history(slug):
    """Show version history for a market"""
    conn = duckdb.connect('data/mordor.duckdb')

    result = conn.execute("""
        SELECT rv.version_number, rv.snapshot_reason, rv.scraped_at, rv.changed_fields
        FROM report_versions rv
        JOIN reports r ON rv.report_id = r.id
        WHERE r.slug = ?
        ORDER BY rv.version_number
    """, [slug]).fetchall()

    conn.close()

    if not result:
        print(f"❌ No history found: {slug}")
        return

    print_section(f"📝 VERSION HISTORY: {slug}")

    table_data = []
    for version_num, reason, date, changed in result:
        changed_str = ""
        if changed:
            try:
                changed_list = json.loads(changed)
                changed_str = ", ".join(changed_list[:3])
                if len(changed_list) > 3:
                    changed_str += f"... (+{len(changed_list)-3} more)"
            except:
                changed_str = changed

        table_data.append([
            version_num,
            reason,
            str(date)[:10],
            changed_str
        ])

    print(tabulate(table_data,
                   headers=["Version", "Reason", "Date", "Changed Fields"],
                   tablefmt="grid"))

def main():
    """Main menu"""
    while True:
        print("\n" + "="*80)
        print("  📊 MORDOR INTELLIGENCE MARKET ANALYSIS DASHBOARD")
        print("="*80)
        print("\n1. Top Markets by CAGR")
        print("2. Markets by Region")
        print("3. Data Quality Report")
        print("4. View Market Details")
        print("5. Version History")
        print("6. Export to CSV")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            limit = input("How many markets? (default 15): ").strip() or "15"
            show_top_markets(int(limit))

        elif choice == "2":
            show_by_region()

        elif choice == "3":
            show_data_quality()

        elif choice == "4":
            slug = input("Enter market slug: ").strip()
            show_market_details(slug)

        elif choice == "5":
            slug = input("Enter market slug: ").strip()
            show_version_history(slug)

        elif choice == "6":
            conn = duckdb.connect('data/mordor.duckdb')
            conn.execute("""
                COPY (
                    SELECT
                        slug,
                        title,
                        cagr_percent,
                        market_size_current_value,
                        market_size_current_unit,
                        region,
                        fastest_growing_country,
                        cloud_share_percent
                    FROM reports
                    ORDER BY cagr_percent DESC
                ) TO 'data/exports/market_reports.csv' (HEADER, DELIMITER ',')
            """)
            conn.close()
            print("\n✅ Exported to data/exports/market_reports.csv")

        elif choice == "0":
            print("\nGoodbye! 👋\n")
            break

        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()

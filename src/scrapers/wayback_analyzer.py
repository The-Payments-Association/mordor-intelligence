"""
Analyze Wayback Machine snapshots to determine report update frequency.
Helps optimize scraping schedule and predict update timing.
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict


def get_wayback_snapshots(url: str) -> List[Dict]:
    """
    Query Internet Archive Wayback Machine for all snapshots of a URL.

    Args:
        url: Full URL to analyze (e.g., https://www.mordorintelligence.com/industry-reports/...)

    Returns:
        List of snapshots with dates and status codes
    """
    base_url = "https://archive.org/wayback/available"
    params = {
        'url': url,
        'output': 'json'
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()

        snapshots = data.get('archived_snapshots', {}).get('snapshots', [])

        return [
            {
                'timestamp': snap['timestamp'],
                'date': datetime.strptime(snap['timestamp'], '%Y%m%d%H%M%S'),
                'status': snap['status']
            }
            for snap in snapshots
            if snap['status'] == '200'  # Only successful captures
        ]

    except Exception as e:
        print(f"Error fetching Wayback data for {url}: {e}")
        return []


def analyze_update_frequency(snapshots: List[Dict]) -> Dict:
    """
    Analyze snapshots to determine update frequency pattern.

    Args:
        snapshots: List of snapshot dicts with 'date' key

    Returns:
        Analysis results with frequency, gaps, pattern info
    """
    if len(snapshots) < 2:
        return {
            'status': 'insufficient_data',
            'snapshots_found': len(snapshots),
            'frequency': 'unknown',
            'confidence': 'low'
        }

    # Sort by date
    dates = sorted([s['date'] for s in snapshots])

    # Calculate gaps between consecutive snapshots
    gaps = []
    for i in range(1, len(dates)):
        gap_days = (dates[i] - dates[i-1]).days
        if gap_days > 0:
            gaps.append(gap_days)

    if not gaps:
        return {
            'status': 'no_variation',
            'snapshots_found': len(snapshots),
            'frequency': 'unknown',
            'confidence': 'low'
        }

    # Calculate statistics
    avg_gap = sum(gaps) / len(gaps)
    min_gap = min(gaps)
    max_gap = max(gaps)
    median_gap = sorted(gaps)[len(gaps) // 2]

    # Determine frequency category
    if avg_gap < 7:
        frequency = 'daily'
    elif avg_gap < 30:
        frequency = 'weekly'
    elif avg_gap < 90:
        frequency = 'monthly'
    elif avg_gap < 180:
        frequency = 'quarterly'
    elif avg_gap < 365:
        frequency = 'semi-annual'
    else:
        frequency = 'yearly'

    # Assess confidence based on data points
    confidence = 'low'
    if len(gaps) > 10:
        confidence = 'high'
    elif len(gaps) > 5:
        confidence = 'medium'

    return {
        'status': 'success',
        'frequency': frequency,
        'avg_gap_days': round(avg_gap, 1),
        'median_gap_days': median_gap,
        'min_gap_days': min_gap,
        'max_gap_days': max_gap,
        'total_snapshots': len(snapshots),
        'data_points': len(gaps),
        'date_range': {
            'first': dates[0].strftime('%Y-%m-%d'),
            'last': dates[-1].strftime('%Y-%m-%d'),
            'span_days': (dates[-1] - dates[0]).days
        },
        'confidence': confidence,
        'prediction': predict_next_update(dates)
    }


def predict_next_update(dates: List[datetime]) -> Dict:
    """
    Predict when next update might occur based on historical pattern.

    Args:
        dates: Sorted list of snapshot dates

    Returns:
        Next expected update date and confidence
    """
    if len(dates) < 2:
        return {'prediction': 'unknown', 'confidence': 'low'}

    # Calculate average gap
    gaps = []
    for i in range(1, len(dates)):
        gap_days = (dates[i] - dates[i-1]).days
        if gap_days > 0:
            gaps.append(gap_days)

    if not gaps:
        return {'prediction': 'unknown', 'confidence': 'low'}

    avg_gap = sum(gaps) / len(gaps)
    last_date = dates[-1]

    # Predict next date
    from datetime import timedelta
    next_date = last_date + timedelta(days=int(avg_gap))

    return {
        'prediction': next_date.strftime('%Y-%m-%d'),
        'confidence': 'high' if len(gaps) > 5 else 'medium',
        'avg_cycle_days': round(avg_gap),
        'margin_days': round(max(gaps) - avg_gap) if gaps else 0
    }


def detect_monthly_pattern(snapshots: List[Dict]) -> Dict:
    """
    Detect if reports are updated in specific months (seasonal pattern).

    Args:
        snapshots: List of snapshots with dates

    Returns:
        Monthly update pattern
    """
    months = defaultdict(int)
    quarters = defaultdict(int)

    for snap in snapshots:
        month_name = snap['date'].strftime('%B')
        quarter = (snap['date'].month - 1) // 3 + 1
        months[month_name] += 1
        quarters[f'Q{quarter}'] += 1

    # Find most common
    if months:
        most_common_month = max(months, key=months.get)
        most_common_quarter = max(quarters, key=quarters.get)
    else:
        most_common_month = None
        most_common_quarter = None

    return {
        'monthly_distribution': dict(months),
        'quarterly_distribution': dict(quarters),
        'most_common_month': most_common_month,
        'most_common_quarter': most_common_quarter,
        'is_seasonal': len(months) <= 4  # Updates in only a few months
    }


async def analyze_multiple_reports(base_urls: List[str]) -> Dict:
    """
    Analyze update frequency for multiple reports.

    Args:
        base_urls: List of report URLs to analyze

    Returns:
        Summary of update patterns across all reports
    """
    results = {}

    print(f"\n📊 Analyzing {len(base_urls)} reports from Wayback Machine...")
    print("(This may take a minute or two)\n")

    for i, url in enumerate(base_urls, 1):
        # Extract slug from URL
        slug = url.split('/')[-1]

        print(f"[{i}/{len(base_urls)}] {slug}...", end=' ', flush=True)

        # Get snapshots
        snapshots = get_wayback_snapshots(url)

        if snapshots:
            analysis = analyze_update_frequency(snapshots)
            monthly = detect_monthly_pattern(snapshots)

            results[slug] = {
                'url': url,
                'analysis': analysis,
                'seasonal': monthly
            }

            freq = analysis.get('frequency', 'unknown')
            conf = analysis.get('confidence', 'unknown')
            print(f"✓ {freq} ({conf})")
        else:
            results[slug] = {
                'url': url,
                'analysis': {'status': 'no_snapshots', 'frequency': 'unknown'}
            }
            print("✗ No snapshots")

    return results


def generate_report(analysis_results: Dict) -> str:
    """
    Generate human-readable report of update frequency analysis.

    Args:
        analysis_results: Results from analyze_multiple_reports()

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 100)
    report.append("MARKET REPORT UPDATE FREQUENCY ANALYSIS")
    report.append("=" * 100)
    report.append("")

    # Group by frequency
    by_frequency = defaultdict(list)

    for slug, data in analysis_results.items():
        freq = data['analysis'].get('frequency', 'unknown')
        by_frequency[freq].append(slug)

    # Show summary
    report.append("📊 SUMMARY BY FREQUENCY")
    report.append("-" * 100)
    for freq in ['daily', 'weekly', 'monthly', 'quarterly', 'semi-annual', 'yearly', 'unknown']:
        markets = by_frequency.get(freq, [])
        if markets:
            report.append(f"\n{freq.upper()}: {len(markets)} markets")
            for slug in markets[:3]:
                report.append(f"  • {slug}")
            if len(markets) > 3:
                report.append(f"  ... and {len(markets) - 3} more")

    # Detailed analysis
    report.append("\n" + "=" * 100)
    report.append("DETAILED ANALYSIS")
    report.append("=" * 100)

    for slug, data in sorted(analysis_results.items())[:10]:  # Top 10
        analysis = data['analysis']

        if analysis['status'] == 'success':
            report.append(f"\n📍 {slug}")
            report.append(f"  Frequency: {analysis['frequency']}")
            report.append(f"  Confidence: {analysis['confidence']}")
            report.append(f"  Snapshots: {analysis['total_snapshots']}")
            report.append(f"  Avg Gap: {analysis['avg_gap_days']} days")
            report.append(f"  Range: {analysis['min_gap_days']}-{analysis['max_gap_days']} days")
            report.append(f"  Data Span: {analysis['date_range']['span_days']} days")
            report.append(f"  Latest: {analysis['date_range']['last']}")

            if analysis.get('prediction'):
                pred = analysis['prediction']
                report.append(f"  Next Expected: {pred['prediction']} (±{pred['margin_days']} days)")

            # Seasonal info
            seasonal = data['seasonal']
            if seasonal.get('is_seasonal'):
                report.append(f"  Pattern: Seasonal updates in {seasonal['most_common_month']}")

    return "\n".join(report)


# Example usage
if __name__ == "__main__":
    # Test with a sample URL
    sample_url = "https://www.mordorintelligence.com/industry-reports/south-america-real-time-payments-market"

    print(f"Analyzing: {sample_url}\n")

    snapshots = get_wayback_snapshots(sample_url)
    print(f"Found {len(snapshots)} snapshots\n")

    if snapshots:
        analysis = analyze_update_frequency(snapshots)
        monthly = detect_monthly_pattern(snapshots)

        print("Update Frequency Analysis:")
        print(json.dumps(analysis, indent=2, default=str))

        print("\nSeasonal Pattern:")
        print(json.dumps(monthly, indent=2))

        # Prediction
        if analysis.get('prediction'):
            pred = analysis['prediction']
            print(f"\n🎯 Next Update Predicted: {pred['prediction']}")
            print(f"   Confidence: {pred['confidence']}")
            print(f"   Typical Cycle: ~{pred['avg_cycle_days']} days")

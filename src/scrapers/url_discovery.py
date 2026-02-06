"""
URL discovery for 153 payment market reports.
Uses Playwright for JavaScript rendering to get all reports including paginated ones.
"""

import json
import re
import httpx
from typing import List, Set
from urllib.parse import urljoin, urlparse

from config.settings import BASE_URL, PAYMENTS_INDEX, USER_AGENT, REQUEST_DELAY
import asyncio

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


async def discover_all_report_urls() -> List[str]:
    """
    Discover payment market report URLs using Playwright for JavaScript rendering.

    Handles pagination to get all ~153 payment market reports.
    Falls back to __NEXT_DATA__ extraction if Playwright not available.

    Returns:
        List of unique report URLs
    """
    urls = set()

    # Try Playwright first (handles JavaScript pagination)
    if PLAYWRIGHT_AVAILABLE:
        try:
            playwright_urls = await _discover_with_playwright()
            urls.update(playwright_urls)
            if len(urls) > 40:
                print(f"✓ Playwright: Found {len(urls)} reports with pagination")
                return list(urls)
        except Exception as e:
            print(f"⚠ Playwright failed ({e}), falling back to __NEXT_DATA__...")

    # Fallback: Extract from __NEXT_DATA__ (only gets first 40)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            index_urls = await _extract_next_data_urls(client)
            urls.update(index_urls)
            print(f"✓ __NEXT_DATA__: Found {len(index_urls)} reports")
    except Exception as e:
        raise RuntimeError(f"Failed to discover URLs: {e}")

    # Validate and deduplicate
    unique_urls = list(urls)
    unique_urls = [u for u in unique_urls if _is_valid_report_url(u)]
    unique_urls.sort()

    return unique_urls


async def _discover_with_playwright() -> Set[str]:
    """
    Use Playwright to render JavaScript and discover all reports including paginated ones.

    Returns:
        Set of report URLs
    """
    urls = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            # Navigate to payments index
            print(f"🌐 Opening {PAYMENTS_INDEX}...")
            await page.goto(PAYMENTS_INDEX, wait_until='networkidle', timeout=60000)

            # Get initial report count from page
            report_elements = await page.locator('a[href*="/industry-reports/"]').all()
            print(f"   Found {len(report_elements)} report links initially")

            # Scroll through all pages to load all reports
            # The site uses pagination, so we need to click "Load More" or similar
            max_scrolls = 20
            scroll_count = 0

            while scroll_count < max_scrolls:
                # Get current report count
                current_reports = await page.locator('a[href*="/industry-reports/"]').all()

                # Scroll to bottom to trigger pagination
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)  # Wait for content to load

                # Check if new reports loaded
                new_reports = await page.locator('a[href*="/industry-reports/"]').all()

                if len(new_reports) == len(current_reports):
                    # No new reports loaded, we're done
                    break

                scroll_count += 1
                print(f"   Scroll {scroll_count}: {len(new_reports)} reports found")

                # Don't scroll too many times
                if scroll_count > 1 and len(new_reports) > 150:
                    break

            # Extract all report URLs
            final_reports = await page.locator('a[href*="/industry-reports/"]').all()
            print(f"✓ Total reports found: {len(final_reports)}")

            for element in final_reports:
                try:
                    href = await element.get_attribute('href')
                    if href:
                        full_url = urljoin(BASE_URL, href)
                        urls.add(full_url)
                except:
                    pass

        except Exception as e:
            print(f"   Error during pagination: {e}")

        finally:
            await browser.close()

    return urls


async def _extract_next_data_urls(client: httpx.AsyncClient) -> Set[str]:
    """
    Extract report URLs from __NEXT_DATA__ JSON on index page.
    This contains the first 40 reports.

    Returns:
        Set of report URLs
    """
    urls = set()

    try:
        response = await client.get(
            PAYMENTS_INDEX,
            headers={'User-Agent': USER_AGENT}
        )
        response.raise_for_status()

        # Extract __NEXT_DATA__ JSON
        match = re.search(
            r'<script id="__NEXT_DATA__"\s+type="application/json"[^>]*>([^<]+)</script>',
            response.text
        )

        if not match:
            raise ValueError("Could not find __NEXT_DATA__ in response")

        next_data = json.loads(match.group(1))

        # Navigate to reports list - actual path: props -> pageProps -> response -> content -> reportList
        props = next_data.get('props', {})
        page_props = props.get('pageProps', {})
        response_data = page_props.get('response', {})
        content = response_data.get('content', {})

        # Try different possible paths
        reports = (
            content.get('reportList') or  # Current structure
            page_props.get('reports') or   # Alternative
            page_props.get('listings') or  # Fallback
            page_props.get('data', {}).get('reports')  # Old structure
        )

        if not reports:
            raise ValueError("Could not find reports in pageProps")

        # Extract URLs from reports
        for report in reports:
            if isinstance(report, dict):
                # Try to get URL directly, or build from slug
                url = report.get('url') or report.get('link') or report.get('href')

                if not url and report.get('slug'):
                    # Build URL from slug: /industry-reports/{slug}
                    slug = report.get('slug')
                    url = f"/industry-reports/{slug}"

                if url:
                    full_url = urljoin(BASE_URL, url)
                    urls.add(full_url)

    except Exception as e:
        raise RuntimeError(f"Failed to extract __NEXT_DATA__ URLs: {e}")

    return urls


async def _fetch_api_pages(
    client: httpx.AsyncClient,
    start_page: int,
    end_page: int
) -> Set[str]:
    """
    Fetch report URLs from API for pages 2-6.
    Remaining ~113 reports are on subsequent pages.

    Args:
        client: httpx AsyncClient
        start_page: Starting page number (usually 2)
        end_page: Ending page number (usually 6)

    Returns:
        Set of report URLs
    """
    urls = set()

    # Try to identify API endpoint
    # Common patterns: api.mordorintelligence.com, api-nextjs.mordorintelligence.com
    api_endpoints = [
        'https://api-nextjs.mordorintelligence.com/api/v1/public/reports',
        'https://api.mordorintelligence.com/v1/reports',
        'https://api.mordorintelligence.com/api/reports',
    ]

    for endpoint in api_endpoints:
        try:
            for page in range(start_page, end_page + 1):
                try:
                    params = {
                        'category': 'payments',
                        'page': page,
                        'limit': 30
                    }

                    response = await client.get(
                        endpoint,
                        params=params,
                        headers={'User-Agent': USER_AGENT},
                        timeout=30.0
                    )

                    if response.status_code == 404:
                        # Try next endpoint
                        break

                    response.raise_for_status()

                    data = response.json()

                    # Extract URLs from response
                    reports = data.get('data', data.get('reports', []))
                    if not reports:
                        break

                    for report in reports:
                        if isinstance(report, dict):
                            url = report.get('url') or report.get('link') or report.get('href')
                            if url:
                                full_url = urljoin(BASE_URL, url)
                                urls.add(full_url)

                    # Rate limiting
                    await asyncio.sleep(REQUEST_DELAY)

                except httpx.RequestError:
                    continue

            # If we got some URLs, this endpoint works
            if urls:
                break

        except Exception as e:
            continue

    return urls


def _is_valid_report_url(url: str) -> bool:
    """
    Validate that URL is a valid Mordor Intelligence report.

    Args:
        url: URL to validate

    Returns:
        True if valid report URL
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)

        # Check domain
        if 'mordorintelligence.com' not in parsed.netloc:
            return False

        # Check path pattern
        if '/industry-reports/' not in parsed.path:
            return False

        return True

    except:
        return False


async def validate_urls_batch(urls: List[str], max_workers: int = 5) -> dict:
    """
    Validate URLs by checking HTTP HEAD response.
    Returns mapping of valid/invalid URLs.

    Args:
        urls: List of URLs to validate
        max_workers: Number of concurrent requests

    Returns:
        Dict with 'valid', 'invalid', 'unreachable' lists
    """
    result = {'valid': [], 'invalid': [], 'unreachable': []}

    async def check_url(client: httpx.AsyncClient, url: str):
        try:
            response = await client.head(url, allow_redirects=True, timeout=10.0)
            if response.status_code == 200:
                result['valid'].append(url)
            elif 400 <= response.status_code < 500:
                result['invalid'].append(url)
            else:
                result['unreachable'].append(url)
        except Exception:
            result['unreachable'].append(url)

    async with httpx.AsyncClient() as client:
        # Process in batches
        for i in range(0, len(urls), max_workers):
            batch = urls[i:i + max_workers]
            tasks = [check_url(client, url) for url in batch]
            await asyncio.gather(*tasks)

    return result

"""
Compiled regex patterns for parsing payment market report data.
Patterns extracted from FAQ answers and metadata fields.
"""

import re
from typing import Optional, List, Tuple
from decimal import Decimal


# Market size patterns: "USD 6.34 trillion in 2026"
MARKET_SIZE_PATTERN = re.compile(
    r'(?:USD|US\$|₹|\$)?\s*([0-9,]+(?:\.[0-9]{1,2})?)\s*(billion|trillion|million)\s*(?:in|by|as of)?\s*(?:(\d{4}))?',
    re.IGNORECASE
)

# CAGR patterns: "5.51% CAGR" or "CAGR of 5.51%"
CAGR_PATTERN = re.compile(
    r'(?:CAGR\s+(?:of\s+)?|Compound Annual Growth Rate\s+(?:of\s+)?)?([0-9.]+)%\s*(?:CAGR)?',
    re.IGNORECASE
)

# Company names: "Mastercard Inc.", "Visa Ltd.", etc.
COMPANY_PATTERN = re.compile(
    r'\b([A-Z][A-Za-z0-9\s&\-\.]+(?:Inc\.?|Ltd\.?|LLC|Corp\.?|Corporation|Limited|Incorporated))\b'
)

# Country + CAGR: "Colombia (7.41% CAGR)" or "India at 15.3% CAGR"
COUNTRY_CAGR_PATTERN = re.compile(
    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:at|with|@)?\s*\(?([0-9.]+)%\s*(?:CAGR)?\)?',
    re.IGNORECASE
)

# Leading segment: "Retail (33.67%, 6.27% CAGR)"
LEADING_SEGMENT_PATTERN = re.compile(
    r'(?:leading|top|largest)\s+(?:segment|type|category|channel).*?(?:is|:)?\s*([A-Z][A-Za-z\s&\-]+?)\s*\(?([0-9.]+)%(?:.*?([0-9.]+)%\s*CAGR)?\)?',
    re.IGNORECASE
)

# Cloud share: "68.34% of the market" or "Cloud deployment at 68.34%"
CLOUD_SHARE_PATTERN = re.compile(
    r'(?:cloud|cloud-based)\s+(?:accounted for|held|represent).*?([0-9.]+)%\s*(?:of\s+(?:the\s+)?market)?',
    re.IGNORECASE
)

# Study period: "2022-2031" or "from 2022 to 2031"
STUDY_PERIOD_PATTERN = re.compile(
    r'(?:from|during|over|in)?\s*(\d{4})\s*(?:to|through|-)\s*(\d{4})',
    re.IGNORECASE
)

# Fastest growing country/region: "fastest growing at 12.3%" or "highest CAGR 12.3%"
FASTEST_GROWING_PATTERN = re.compile(
    r'(?:fastest\s+growing|highest\s+(?:CAGR|growth))\s+(?:country|region|market)?\s*(?:is|:)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:at|with)?\s*\(?([0-9.]+)%',
    re.IGNORECASE
)

# Temporal coverage: "2015-2025" or "2020-2030"
TEMPORAL_COVERAGE_PATTERN = re.compile(
    r'(?:temporal\s+coverage|time\s+period|study\s+period).*?(\d{4})\s*(?:to|through|-)\s*(\d{4})',
    re.IGNORECASE
)


def extract_market_sizes(text: str) -> Tuple[Optional[Decimal], Optional[str], Optional[int]]:
    """
    Extract market size value, unit, and year from text.
    Returns (value, unit, year) or (None, None, None) if not found.
    """
    if not text:
        return None, None, None

    match = MARKET_SIZE_PATTERN.search(text)
    if not match:
        return None, None, None

    value_str = match.group(1).replace(',', '')
    try:
        value = Decimal(value_str)
    except:
        return None, None, None

    unit = match.group(2).lower().capitalize()
    year = int(match.group(3)) if match.group(3) else None

    return value, unit, year


def extract_all_market_sizes(text: str) -> List[Tuple[Decimal, str, int]]:
    """Extract all market sizes from text (current and forecast)."""
    results = []
    for match in MARKET_SIZE_PATTERN.finditer(text):
        value_str = match.group(1).replace(',', '')
        try:
            value = Decimal(value_str)
        except:
            continue

        unit = match.group(2).lower().capitalize()
        year = int(match.group(3)) if match.group(3) else None

        results.append((value, unit, year))

    return results


def extract_cagr(text: str) -> Optional[Decimal]:
    """Extract CAGR percentage from text."""
    if not text:
        return None

    match = CAGR_PATTERN.search(text)
    if not match:
        return None

    try:
        return Decimal(match.group(1))
    except:
        return None


def extract_all_cagrs(text: str) -> List[Decimal]:
    """Extract all CAGR values from text."""
    results = []
    for match in CAGR_PATTERN.finditer(text):
        try:
            results.append(Decimal(match.group(1)))
        except:
            continue
    return results


def extract_companies(text: str) -> List[str]:
    """Extract company names from text."""
    if not text:
        return []

    companies = []
    for match in COMPANY_PATTERN.finditer(text):
        company = match.group(1).strip()
        # Avoid duplicates
        if company not in companies:
            companies.append(company)

    return companies


def extract_fastest_growing(text: str) -> Optional[Tuple[str, Decimal]]:
    """
    Extract fastest growing country and its CAGR.
    Returns (country_name, cagr_percent) or (None, None).
    """
    if not text:
        return None, None

    match = FASTEST_GROWING_PATTERN.search(text)
    if not match:
        return None, None

    country = match.group(1).strip()
    try:
        cagr = Decimal(match.group(2))
    except:
        return None, None

    return country, cagr


def extract_leading_segment(text: str) -> Optional[Tuple[str, Optional[Decimal], Optional[Decimal]]]:
    """
    Extract leading segment name, share percentage, and CAGR.
    Returns (name, share_percent, cagr_percent) or (None, None, None).
    """
    if not text:
        return None, None, None

    match = LEADING_SEGMENT_PATTERN.search(text)
    if not match:
        return None, None, None

    name = match.group(1).strip()
    try:
        share = Decimal(match.group(2))
    except:
        share = None

    try:
        cagr = Decimal(match.group(3)) if match.group(3) else None
    except:
        cagr = None

    return name, share, cagr


def extract_cloud_share(text: str) -> Optional[Decimal]:
    """Extract cloud share percentage from text."""
    if not text:
        return None

    match = CLOUD_SHARE_PATTERN.search(text)
    if not match:
        return None

    try:
        return Decimal(match.group(1))
    except:
        return None


def extract_study_period(text: str) -> Optional[Tuple[int, int]]:
    """
    Extract study period start and end years.
    Returns (start_year, end_year) or (None, None).
    """
    if not text:
        return None, None

    match = STUDY_PERIOD_PATTERN.search(text)
    if not match:
        return None, None

    try:
        start = int(match.group(1))
        end = int(match.group(2))
        return start, end
    except:
        return None, None


def extract_percentage(text: str, label: str = None) -> Optional[Decimal]:
    """
    Extract a percentage from text, optionally with a label prefix.
    Example: extract_percentage("Market share: 45.67%") -> Decimal('45.67')
    """
    if not text:
        return None

    pattern = r'([0-9.]+)%'
    if label:
        pattern = f'{re.escape(label)}.*?({pattern})'

    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None

    try:
        return Decimal(match.group(1))
    except:
        return None


def extract_year(text: str) -> Optional[int]:
    """Extract a year (4-digit number) from text."""
    if not text:
        return None

    match = re.search(r'\b(20\d{2})\b', text)
    if not match:
        return None

    try:
        return int(match.group(1))
    except:
        return None


def extract_all_years(text: str) -> List[int]:
    """Extract all years (4-digit numbers) from text."""
    if not text:
        return []

    years = []
    for match in re.finditer(r'\b(20\d{2})\b', text):
        try:
            year = int(match.group(1))
            if year not in years:
                years.append(year)
        except:
            continue

    return years


def extract_currency(text: str) -> Optional[str]:
    """Extract currency code from text (USD, EUR, INR, GBP, etc.)."""
    if not text:
        return None

    # Look for ISO currency codes or symbols
    currency_map = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR',
        'USD': 'USD',
        'EUR': 'EUR',
        'GBP': 'GBP',
        'JPY': 'JPY',
        'INR': 'INR',
    }

    for symbol, code in currency_map.items():
        if symbol in text:
            return code

    return 'USD'  # Default

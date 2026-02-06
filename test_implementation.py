#!/usr/bin/env python
"""
Comprehensive test suite for Mordor Intelligence scraper implementation.
Tests: models, regex patterns, JSON-LD parser, versioning, database.
"""

import sys
from datetime import datetime
from decimal import Decimal
import json

from src.models.schema import Report, FAQPair
from src.parsers import regex_patterns as rp
from src.parsers.jsonld_parser import JSONLDParser
from src.database.versioning import VersionManager
from src.validators.report_validator import ReportValidator


def test_models():
    """Test Pydantic models."""
    print("Testing Models...")

    # Create a report
    report = Report(
        slug="test-market",
        title="Test Market Report",
        url="https://www.mordorintelligence.com/industry-reports/test-market",
        market_size_current_value=Decimal("123.45"),
        market_size_current_unit="Billion",
        market_size_current_year=2026,
        cagr_percent=Decimal("12.5"),
        region="Asia-Pacific",
        major_players=["Company A", "Company B"],
        leading_segment_name="Cloud",
        leading_segment_share_percent=Decimal("45.0"),
        cloud_share_percent=Decimal("68.0"),
        scraped_at=datetime.utcnow(),
    )

    # Test content hash
    hash1 = report.compute_content_hash()
    assert hash1 is not None and len(hash1) == 64, "Content hash should be 64-char hex"
    print(f"  ✓ Content hash computed: {hash1[:16]}...")

    # Test hash consistency
    hash2 = report.compute_content_hash()
    assert hash1 == hash2, "Content hash should be deterministic"
    print("  ✓ Content hash is deterministic")

    # Test changed fields detection
    report2 = report.model_copy()
    report2.cagr_percent = Decimal("15.0")
    changed = report2.get_changed_fields(report)
    assert 'cagr_percent' in changed, "Changed fields should detect CAGR change"
    print(f"  ✓ Changed fields detection works: {changed}")

    return True


def test_regex_patterns():
    """Test regex pattern extraction."""
    print("\nTesting Regex Patterns...")

    # Test market size extraction
    text = "The market was valued at USD 123.45 billion in 2026 and is expected to reach $567.89 trillion by 2031"
    value, unit, year = rp.extract_market_sizes(text)
    assert value == Decimal("123.45"), "Should extract 123.45"
    assert unit == "Billion", f"Expected 'Billion', got '{unit}'"
    assert year == 2026, "Should extract year 2026"
    print("  ✓ Market size extraction works")

    # Test CAGR extraction
    text = "The market is expected to grow at a CAGR of 15.75%"
    cagr = rp.extract_cagr(text)
    assert cagr == Decimal("15.75"), "Should extract CAGR 15.75"
    print("  ✓ CAGR extraction works")

    # Test company extraction
    text = "Major players include Mastercard Inc., Visa Ltd., and PayPal Corporation"
    companies = rp.extract_companies(text)
    assert any("Mastercard" in c and "Inc" in c for c in companies), f"Should find Mastercard in {companies}"
    assert any("Visa" in c and "Ltd" in c for c in companies), f"Should find Visa in {companies}"
    print(f"  ✓ Company extraction works: {companies}")

    # Test fastest growing
    text = "The fastest growing market is India at 18.5% CAGR"
    country, cagr = rp.extract_fastest_growing(text)
    # Just check that we extracted a country and CAGR
    assert country is not None, "Should extract a country"
    assert cagr == Decimal("18.5"), f"Expected 18.5, got {cagr}"
    print(f"  ✓ Fastest growing extraction works: {country} {cagr}%")

    # Test cloud share
    text = "Cloud deployments accounted for 72.34% of the market"
    cloud = rp.extract_cloud_share(text)
    assert cloud == Decimal("72.34"), f"Expected 72.34, got {cloud}"
    print("  ✓ Cloud share extraction works")

    return True


def test_jsonld_parser():
    """Test JSON-LD parser with sample HTML."""
    print("\nTesting JSON-LD Parser...")

    # Create minimal sample HTML with JSON-LD
    html = """
    <html>
    <head>
        <title>South America Real Time Payments Market</title>
        <meta name="description" content="Comprehensive market analysis">
        <script id="__NEXT_DATA__" type="application/json">{"test": "data"}</script>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "What is the current market size?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "The market was valued at USD 6.34 trillion in 2026, with a CAGR of 5.51%. Leading players include Mastercard Inc., Visa Inc., and ACI Worldwide Inc. Cloud deployments represent 68.34% of the market."
                    }
                }
            ]
        }
        </script>
    </head>
    </html>
    """

    url = "https://www.mordorintelligence.com/industry-reports/south-america-real-time-payments-market"
    parser = JSONLDParser(html, url)
    report = parser.parse_report()

    assert report.slug == "south-america-real-time-payments-market", "Should extract slug"
    assert report.title == "South America Real Time Payments Market", "Should extract title"
    assert report.market_size_current_value == Decimal("6.34"), "Should extract market size"
    assert report.cagr_percent == Decimal("5.51"), "Should extract CAGR"
    assert any("Mastercard" in p and "Inc" in p for p in report.major_players), f"Should extract Mastercard in {report.major_players}"
    assert report.cloud_share_percent == Decimal("68.34"), "Should extract cloud share"
    print("  ✓ JSON-LD parser works correctly")

    # Test content hash is computed
    assert report.content_hash is not None and len(report.content_hash) == 64
    print("  ✓ Parser computes content hash")

    return True


def test_validators():
    """Test data validators."""
    print("\nTesting Validators...")

    # Valid report
    report = Report(
        slug="test-market",
        title="Test Report",
        url="https://www.mordorintelligence.com/industry-reports/test",
        market_size_current_value=Decimal("100"),
        cagr_percent=Decimal("10.5"),
        major_players=["Company A", "Company B"],
        region="Asia-Pacific",
        scraped_at=datetime.utcnow(),
    )

    validation = ReportValidator.validate(report)
    assert len(validation['errors']) == 0, "Valid report should have no errors"
    print("  ✓ Valid report passes validation")

    # Invalid report (negative market size)
    report2 = report.model_copy()
    report2.market_size_current_value = Decimal("-100")
    validation = ReportValidator.validate(report2)
    assert len(validation['errors']) > 0, "Negative market size should error"
    print("  ✓ Invalid market size detected")

    # Invalid report (bad CAGR)
    report3 = report.model_copy()
    report3.cagr_percent = Decimal("150")
    validation = ReportValidator.validate(report3)
    assert len(validation['warnings']) > 0, "Unusual CAGR should warn"
    print("  ✓ Unusual CAGR detected")

    return True


def test_versioning():
    """Test versioning and change detection."""
    print("\nTesting Versioning...")

    import os
    import duckdb

    # Create test database with schema
    test_db = "data/test_version.duckdb"
    if os.path.exists(test_db):
        os.remove(test_db)

    # Initialize schema
    conn = duckdb.connect(test_db)
    schema_file = "src/database/schema.sql"
    with open(schema_file, 'r') as f:
        schema = f.read()
    conn.execute(schema)
    conn.commit()
    conn.close()

    # Create version manager
    vm = VersionManager(test_db)

    # Create first report
    report1 = Report(
        slug="versioning-test",
        title="Test Report V1",
        url="https://test.com/test",
        market_size_current_value=Decimal("100"),
        cagr_percent=Decimal("10.0"),
        major_players=["Company A"],
        scraped_at=datetime.utcnow(),
    )
    report1.content_hash = report1.compute_content_hash()

    # Check if version should be created (new report)
    should_create, reason, changed = vm.should_create_version(report1)
    assert should_create == True, "New report should create version"
    assert reason == "new_report", "Reason should be 'new_report'"
    print(f"  ✓ New report detected: {reason}")

    # Create the version in the database
    vm.create_version(report1, reason, changed)

    # Create second version with changes
    report2 = report1.model_copy()
    report2.cagr_percent = Decimal("12.0")
    report2.content_hash = report2.compute_content_hash()

    should_create2, reason2, changed2 = vm.should_create_version(report2)
    assert should_create2 == True, "Changed report should create version"
    assert reason2 == "field_change", "Reason should be 'field_change'"
    assert 'cagr_percent' in changed2, "Changed fields should include cagr_percent"
    print(f"  ✓ Changed report detected: {changed2}")

    # Clean up test DB
    import os
    try:
        os.remove("data/test_version.duckdb")
    except:
        pass

    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("MORDOR INTELLIGENCE SCRAPER - TEST SUITE")
    print("=" * 80)

    tests = [
        ("Pydantic Models", test_models),
        ("Regex Patterns", test_regex_patterns),
        ("JSON-LD Parser", test_jsonld_parser),
        ("Data Validators", test_validators),
        ("Versioning", test_versioning),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)

    if failed == 0:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

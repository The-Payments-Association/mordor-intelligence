"""
Data quality validators for parsed reports.
Validates extracted fields meet expected constraints.
"""

from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal

from src.models.schema import Report


class ReportValidator:
    """Validate report data quality."""

    @staticmethod
    def validate(report: Report) -> Dict[str, List[str]]:
        """
        Validate report data quality.

        Returns:
            Dict with 'errors' and 'warnings' lists
        """
        result = {'errors': [], 'warnings': []}

        # Required fields
        if not report.slug:
            result['errors'].append('Missing slug')
        if not report.title:
            result['errors'].append('Missing title')
        if not report.url:
            result['errors'].append('Missing url')

        # Market size validation
        if report.market_size_current_value is not None:
            if report.market_size_current_value <= 0:
                result['errors'].append(
                    f'Invalid current market size: {report.market_size_current_value}'
                )

        if report.market_size_forecast_value is not None:
            if report.market_size_forecast_value <= 0:
                result['errors'].append(
                    f'Invalid forecast market size: {report.market_size_forecast_value}'
                )

        # CAGR validation
        if report.cagr_percent is not None:
            if report.cagr_percent < -100 or report.cagr_percent > 100:
                result['warnings'].append(
                    f'Unusual CAGR: {report.cagr_percent}%'
                )

        # Fastest growing CAGR
        if report.fastest_growing_country_cagr is not None:
            if report.fastest_growing_country_cagr < -100 or report.fastest_growing_country_cagr > 100:
                result['warnings'].append(
                    f'Unusual fastest growing CAGR: {report.fastest_growing_country_cagr}%'
                )

        # Study period validation
        if report.study_period_start and report.study_period_end:
            if report.study_period_end < report.study_period_start:
                result['errors'].append(
                    f'Study period end ({report.study_period_end}) before start ({report.study_period_start})'
                )

            # Check for reasonable date range
            current_year = datetime.now().year
            if report.study_period_end > current_year + 50:
                result['warnings'].append(
                    f'Study period end year seems too far in future: {report.study_period_end}'
                )

        # Players count
        if report.major_players:
            if len(report.major_players) > 20:
                result['warnings'].append(
                    f'Many major players listed: {len(report.major_players)}'
                )
            elif len(report.major_players) == 0:
                result['warnings'].append('No major players extracted')

        # Segment share validation
        if report.leading_segment_share_percent is not None:
            if report.leading_segment_share_percent < 0 or report.leading_segment_share_percent > 100:
                result['errors'].append(
                    f'Invalid leading segment share: {report.leading_segment_share_percent}%'
                )

        # Cloud share validation
        if report.cloud_share_percent is not None:
            if report.cloud_share_percent < 0 or report.cloud_share_percent > 100:
                result['errors'].append(
                    f'Invalid cloud share: {report.cloud_share_percent}%'
                )

        # Check that at least some key fields are populated
        key_fields = [
            'market_size_current_value', 'cagr_percent', 'major_players',
            'leading_segment_name', 'region'
        ]
        populated = sum(1 for field in key_fields if getattr(report, field) is not None)
        if populated < 2:
            result['warnings'].append(
                f'Few key fields populated: {populated}/{len(key_fields)}'
            )

        return result

    @staticmethod
    def is_valid(report: Report) -> bool:
        """Check if report is valid (no critical errors)."""
        validation = ReportValidator.validate(report)
        return len(validation['errors']) == 0

    @staticmethod
    def format_validation_report(validation: Dict[str, List[str]]) -> str:
        """Format validation result as string."""
        lines = []

        if validation['errors']:
            lines.append('ERRORS:')
            for error in validation['errors']:
                lines.append(f'  - {error}')

        if validation['warnings']:
            lines.append('WARNINGS:')
            for warning in validation['warnings']:
                lines.append(f'  - {warning}')

        if not validation['errors'] and not validation['warnings']:
            lines.append('✓ Valid')

        return '\n'.join(lines)

"""
JSON-LD parser for Mordor Intelligence payment market reports.
Extracts structured data from 5 JSON-LD blocks on each report page.
"""

import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from src.models.schema import Report, FAQPair
from src.parsers import regex_patterns as rp


class JSONLDParser:
    """Parse JSON-LD structured data from payment market report HTML."""

    def __init__(self, html: str, url: str):
        """
        Initialize parser with HTML content and report URL.

        Args:
            html: Complete HTML page content
            url: Report URL for context
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, 'html.parser')
        self.jsonld_blocks = self._extract_jsonld_blocks()

    def _extract_jsonld_blocks(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract all JSON-LD script blocks from HTML.
        Returns dict with keys: faq_page, dataset, web_page, image_object, breadcrumb
        """
        blocks = {
            'faq_page': None,
            'dataset': None,
            'web_page': None,
            'image_object': None,
            'breadcrumb': None,
        }

        scripts = self.soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)

                # Handle @type as either string or list
                type_value = data.get('@type', '')
                if isinstance(type_value, list):
                    types = type_value
                else:
                    types = [type_value]

                if 'FAQPage' in types:
                    blocks['faq_page'] = data
                elif 'Dataset' in types:
                    blocks['dataset'] = data
                elif 'WebPage' in types:
                    blocks['web_page'] = data
                elif 'ImageObject' in types:
                    blocks['image_object'] = data
                elif 'BreadcrumbList' in types:
                    blocks['breadcrumb'] = data

            except (json.JSONDecodeError, ValueError):
                continue

        return blocks

    def parse_report(self) -> Report:
        """
        Orchestrate parsing of all JSON-LD sources to build complete Report.
        """
        # Extract slug from URL
        parsed_url = urlparse(self.url)
        slug = parsed_url.path.strip('/').split('/')[-1]

        # Parse metadata first
        title = self._parse_title()
        description = self._parse_description()
        page_dates = self._parse_webpage_dates()

        # Parse FAQ for metrics
        faq_data = self._parse_faq_page()

        # Parse dataset for coverage info
        dataset_data = self._parse_dataset()

        # Parse images
        image_urls = self._parse_images()

        # Build Report object
        report = Report(
            slug=slug,
            url=self.url,
            title=title,
            description=description,
            page_date_published=page_dates.get('published'),
            page_date_modified=page_dates.get('modified'),
            image_urls=image_urls,
            **faq_data,
            **dataset_data,
        )

        # Compute content hash
        report.content_hash = report.compute_content_hash()

        return report

    def _parse_title(self) -> str:
        """Extract title from meta tags or page heading."""
        # Try meta title
        meta_title = self.soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content']

        # Try standard title tag
        title_tag = self.soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        # Fallback to h1
        h1 = self.soup.find('h1')
        if h1:
            return h1.get_text().strip()

        return "Unknown"

    def _parse_description(self) -> Optional[str]:
        """Extract description from meta tags."""
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']

        og_desc = self.soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content']

        return None

    def _parse_webpage_dates(self) -> Dict[str, Optional[datetime]]:
        """Extract publication and modification dates from WebPage schema."""
        dates = {'published': None, 'modified': None}

        if not self.jsonld_blocks['web_page']:
            return dates

        web_page = self.jsonld_blocks['web_page']
        try:
            if 'datePublished' in web_page:
                dates['published'] = datetime.fromisoformat(
                    web_page['datePublished'].replace('Z', '+00:00')
                )
        except (ValueError, KeyError):
            pass

        try:
            if 'dateModified' in web_page:
                dates['modified'] = datetime.fromisoformat(
                    web_page['dateModified'].replace('Z', '+00:00')
                )
        except (ValueError, KeyError):
            pass

        return dates

    def _parse_faq_page(self) -> Dict[str, Any]:
        """
        Extract metrics from FAQPage JSON-LD.
        Returns dict with extracted metrics like market_size, cagr, players, etc.
        """
        result = {
            'market_size_current_value': None,
            'market_size_current_unit': None,
            'market_size_current_year': None,
            'market_size_forecast_value': None,
            'market_size_forecast_unit': None,
            'market_size_forecast_year': None,
            'cagr_percent': None,
            'region': None,
            'fastest_growing_country': None,
            'fastest_growing_country_cagr': None,
            'leading_segment_name': None,
            'leading_segment_share_percent': None,
            'leading_segment_cagr': None,
            'cloud_share_percent': None,
            'major_players': None,
            'faq_questions_answers': None,
        }

        if not self.jsonld_blocks['faq_page']:
            return result

        faq_page = self.jsonld_blocks['faq_page']
        faq_items = faq_page.get('mainEntity', [])
        if not isinstance(faq_items, list):
            faq_items = [faq_items]

        # Parse FAQ items
        faq_pairs = []
        combined_text = ""

        for item in faq_items:
            if item.get('@type') != 'Question':
                continue

            question = item.get('name', '')
            answer_obj = item.get('acceptedAnswer', {})
            answer_text = answer_obj.get('text', '') if answer_obj else ''

            if question and answer_text:
                faq_pairs.append(FAQPair(question=question, answer=answer_text))
                combined_text += f"\n{question}\n{answer_text}\n"

        result['faq_questions_answers'] = faq_pairs if faq_pairs else None

        # Extract metrics from combined FAQ text
        if combined_text:
            # Market sizes (current and forecast)
            sizes = rp.extract_all_market_sizes(combined_text)
            if len(sizes) >= 1:
                value, unit, year = sizes[0]
                result['market_size_current_value'] = value
                result['market_size_current_unit'] = unit
                result['market_size_current_year'] = year

            if len(sizes) >= 2:
                value, unit, year = sizes[1]
                result['market_size_forecast_value'] = value
                result['market_size_forecast_unit'] = unit
                result['market_size_forecast_year'] = year

            # CAGR
            cagrs = rp.extract_all_cagrs(combined_text)
            if cagrs:
                result['cagr_percent'] = cagrs[0]

            # Fastest growing
            country, cagr = rp.extract_fastest_growing(combined_text)
            if country:
                result['fastest_growing_country'] = country
                result['fastest_growing_country_cagr'] = cagr

            # Leading segment
            seg_name, seg_share, seg_cagr = rp.extract_leading_segment(combined_text)
            if seg_name:
                result['leading_segment_name'] = seg_name
                result['leading_segment_share_percent'] = seg_share
                result['leading_segment_cagr'] = seg_cagr

            # Cloud share
            cloud = rp.extract_cloud_share(combined_text)
            if cloud:
                result['cloud_share_percent'] = cloud

            # Major players
            players = rp.extract_companies(combined_text)
            if players:
                result['major_players'] = players

            # Extract region from first FAQ or description
            # Look for region keywords in first answer
            if faq_items:
                first_answer = faq_items[0].get('acceptedAnswer', {}).get('text', '')
                for region_name in [
                    'Asia-Pacific', 'North America', 'Europe', 'South America',
                    'Middle East', 'Africa', 'Latin America'
                ]:
                    if region_name.lower() in first_answer.lower():
                        result['region'] = region_name
                        break

        return result

    def _parse_dataset(self) -> Dict[str, Any]:
        """Extract temporal and spatial coverage from Dataset schema."""
        result = {
            'temporal_coverage': None,
            'spatial_coverage': None,
            'study_period_start': None,
            'study_period_end': None,
        }

        if not self.jsonld_blocks['dataset']:
            return result

        dataset = self.jsonld_blocks['dataset']

        # Temporal coverage
        if 'temporalCoverage' in dataset:
            result['temporal_coverage'] = dataset['temporalCoverage']

            # Try to parse dates
            coverage = dataset['temporalCoverage']
            start, end = rp.extract_study_period(coverage)
            if start:
                result['study_period_start'] = start
                result['study_period_end'] = end

        # Spatial coverage
        if 'spatialCoverage' in dataset:
            spatial = dataset['spatialCoverage']
            if isinstance(spatial, dict):
                result['spatial_coverage'] = spatial.get('name', None)
            elif isinstance(spatial, str):
                result['spatial_coverage'] = spatial

        return result

    def _parse_images(self) -> Optional[List[str]]:
        """Extract image URLs from ImageObject or meta tags."""
        urls = []

        # From ImageObject
        if self.jsonld_blocks['image_object']:
            img_obj = self.jsonld_blocks['image_object']
            if isinstance(img_obj, list):
                for item in img_obj:
                    url = item.get('url')
                    if url and url not in urls:
                        urls.append(url)
            else:
                url = img_obj.get('url')
                if url:
                    urls.append(url)

        # From og:image meta tags
        og_images = self.soup.find_all('meta', property='og:image')
        for og_img in og_images:
            url = og_img.get('content')
            if url and url not in urls:
                urls.append(url)

        # From twitter:image
        twitter_images = self.soup.find_all('meta', attrs={'name': 'twitter:image'})
        for tw_img in twitter_images:
            url = tw_img.get('content')
            if url and url not in urls:
                urls.append(url)

        return urls if urls else None

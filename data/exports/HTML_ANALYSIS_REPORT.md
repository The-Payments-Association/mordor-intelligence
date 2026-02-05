# HTML Analysis Report: Mordor Intelligence Report Pages

## Overview
The Mordor Intelligence report pages contain all market data in **JSON-LD structured data** blocks embedded in the HTML. This is excellent for scraping!

---

## Data Extraction Strategy

### ✅ Best Approach: Parse JSON-LD
The HTML contains 5 JSON-LD `<script type="application/ld+json">` blocks with all report data:

1. **BreadcrumbList** - Navigation hierarchy (less useful)
2. **Dataset** - Report metadata (name, description, temporal/spatial coverage)
3. **FAQPage** - Key metrics in Q&A format ⭐
4. **ImageObject Graph** - Chart/image descriptions
5. **WebPage** - Page metadata (title, description, publish date)

---

## Extracted Data Example: South America Real-Time Payments Market

### From FAQPage Schema:
```json
{
  "title": "South America Real Time Payments Market Size & Share Analysis - Growth Trends and Forecast (2026 - 2031)",
  "current_value": "USD 6.34 trillion (2026)",
  "forecast_value": "USD 8.29 trillion (2031)",
  "cagr": "5.51%",
  "fastest_growing_country": "Colombia (7.41% CAGR)",
  "cloud_share": "68.34% (2025)",
  "leading_segment": "Retail and e-commerce (33.67%, 6.27% CAGR)",
  "major_players": [
    "ACI Worldwide Inc.",
    "Mastercard Inc.",
    "Visa Inc.",
    "Fiserv Inc.",
    "Fidelity National Information Services Inc. (FIS)"
  ]
}
```

### From Dataset Schema:
```json
{
  "description": "Segmented by Transaction Type, Component, Deployment Mode, Enterprise Size, End-User Industry, and Geography",
  "temporal_coverage": "2020 - 2031",
  "spatial_coverage": "South America",
  "published_date": "2026-01-22",
  "modified_date": "2026-01-30"
}
```

### From WebPage Schema:
```json
{
  "url": "https://www.mordorintelligence.com/industry-reports/south-america-real-time-payments-market",
  "publication_date": "2026-01-22",
  "last_modified": "2026-01-30"
}
```

---

## Schema Parsing Code Pattern

```python
from bs4 import BeautifulSoup
import json
import re

# Load and parse HTML
soup = BeautifulSoup(html_content, 'html.parser')

# Find JSON-LD blocks
jsonld_scripts = soup.find_all('script', type='application/ld+json')

report_data = {}

for script in jsonld_scripts:
    data = json.loads(script.string)

    # Extract FAQPage data (key metrics)
    if data.get('@type') == 'FAQPage':
        for item in data.get('mainEntity', []):
            question = item.get('name', '')
            answer = item.get('acceptedAnswer', {}).get('text', '')
            # Extract numbers and values from answer
            report_data['qa_pairs'].append({
                'question': question,
                'answer': answer
            })

    # Extract Dataset metadata
    elif data.get('@type') == 'Dataset':
        report_data['name'] = data.get('name')
        report_data['description'] = data.get('description')
        report_data['temporal_coverage'] = data.get('temporalCoverage')
        report_data['spatial_coverage'] = data.get('spatialCoverage')

    # Extract WebPage date info
    elif data.get('@type') == 'WebPage':
        report_data['published_date'] = data.get('datePublished')
        report_data['modified_date'] = data.get('dateModified')
```

---

## Key Findings

### 📊 Data Availability
✅ Market size values (USD)
✅ CAGR percentages
✅ Major companies/players
✅ Temporal coverage (2020-2031)
✅ Geographic region
✅ Segment breakdowns
✅ Publication dates

### 🚫 Not Available (in JSON-LD)
❌ Historical data points (need to scrape table/image text)
❌ Detailed segment breakdown tables
❌ Full competitive analysis text

### 📈 Next Steps for Scraper

1. **Extract JSON-LD** from every report page
2. **Parse FAQPage** questions/answers for metrics
3. **Use regex** to extract numbers (USD, %, CAGR)
4. **Parse company names** from text
5. **Store in database** with report URL and metadata

---

## Segmentation Found in Descriptions

From the Dataset description, reports are segmented by:
- **Transaction Type**: Peer-To-Peer, Peer-To-Business
- **Component**: Platform/Solution, Services
- **Deployment Mode**: Cloud, On-Premise
- **Enterprise Size**: Large Enterprises, SMEs
- **End-User Industry**: Retail & E-Commerce, BFSI, Utilities, Telecom
- **Geography**: Multiple countries in the region

These segments need to be extracted from detailed content on the page.

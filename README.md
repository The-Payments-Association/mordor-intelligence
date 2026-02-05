# Mordor Intelligence Payments Scraper

Monthly scraper for 153 payment market reports.

## Quick Start

1. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run mitmproxy to analyze API:**
   ```bash
   mitmproxy -s mitmproxy/scripts/mordor_capture.py
   ```
   Then browse to https://www.mordorintelligence.com/market-analysis/payments
   with proxy configured (localhost:8080)

3. **Analyze captured flows** in `mitmproxy/flows/`

## Project Status

- [ ] Phase 1: mitmproxy analysis
- [ ] Phase 2: Schema finalization
- [ ] Phase 3: Scraper implementation
- [ ] Phase 4: Change tracking DB

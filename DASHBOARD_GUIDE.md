# Web Dashboard Guide

## 🚀 Quick Start

### Option 1: Using the Shell Script (Easiest)
```bash
./run_dashboard.sh
```

### Option 2: Manual Start
```bash
venv/bin/streamlit run dashboard.py
```

### Option 3: With Custom Port
```bash
venv/bin/streamlit run dashboard.py --server.port 8502
```

## 📖 Accessing the Dashboard

Once started, open your browser to:
```
http://localhost:8501
```

You should see the Mordor Intelligence Market Dashboard with a left sidebar for navigation.

## 📊 Dashboard Pages Overview

### 1. **Overview** (📈)
The main landing page with key metrics and top markets.

**Features:**
- Total markets count
- Average CAGR across all markets
- Total market size
- Last data update timestamp
- Interactive bar chart of top 10 markets by CAGR
- Detailed table with market data

**Use Case:** Get a quick overview of the market landscape

---

### 2. **Market Analysis** (🌍)
Deep dive into individual markets.

**Features:**
- Market selector dropdown
- Key metrics (CAGR, size, region)
- Market info (title, study period, fastest growing country)
- Deployment data (cloud share %)
- Leading segment information
- Market forecast visualization (current vs forecast size)
- Complete version history

**Use Case:** Research specific markets, track changes over time

---

### 3. **Regional Breakdown** (📊)
Geographic analysis of payment markets.

**Features:**
- Pie chart: Markets by region
- Bar chart: Average CAGR by region
- Detailed statistics table with:
  - Number of markets per region
  - Average CAGR
  - Maximum CAGR
  - Total market size

**Regions Covered:**
- Asia-Pacific
- Africa / Middle East & Africa
- Europe
- Middle East
- Americas (North & South)

**Use Case:** Identify regional market opportunities

---

### 4. **Data Quality** (💾)
Monitor data extraction quality and coverage.

**Features:**
- Coverage metrics for each field:
  - CAGR %
  - Market Size
  - Major Players
- Visual coverage chart (bar graph)
- Target line at 100%
- Detailed field statistics:
  - Extracted count
  - Missing count
  - Coverage percentage

**Current Coverage:**
- CAGR: 97.5% (39/40)
- Market Size: 95.0% (38/40)
- Major Players: 7.5% (3/40)

**Use Case:** Understand data completeness, identify gaps

---

### 5. **Version History** (📝)
Track all scraping runs and changes.

**Features:**
- Scrape runs table:
  - Run ID
  - Start time
  - Number of reports checked
- Scrape summary pie chart:
  - Success (green)
  - Errors (red)
  - Skipped (orange)
- Recent scrape logs:
  - Market name
  - Status
  - Error type
  - Response time
  - Timestamp

**Use Case:** Monitor scraper health, track historical changes

---

### 6. **System Info** (⚙️)
Database statistics and export options.

**Features:**
- Key metrics:
  - Total reports: 40
  - Total versions: 40+
  - Total log entries: 100+
- Last scrape run details
- Data coverage summary
- **Export buttons:**
  - Download as CSV
  - Download as JSON

**Use Case:** Monitor system health, export data for external analysis

---

## 🎨 Interactive Features

### Filters & Selection
- **Market Selector:** Search and select any market from the dropdown
- **Real-time Updates:** Dashboard refreshes data from database

### Charts
- **Plotly Charts:** Hover for detailed info, zoom, pan
- **Interactive Tables:** Click headers to sort, scroll horizontally

### Download Data
- **CSV Export:** Open in Excel
- **JSON Export:** Use in other applications
- **Timestamps:** Automatic with export

---

## 🔍 Common Workflows

### Finding High-Growth Markets
1. Go to **Overview** page
2. Look at "Top 10 Fastest Growing Markets" chart
3. Click on a market name to see more details in **Market Analysis**

### Regional Market Analysis
1. Navigate to **Regional Breakdown**
2. View pie chart for market distribution
3. Compare average CAGRs between regions
4. Click on specific markets to deep dive

### Checking Data Quality
1. Go to **Data Quality** page
2. Review coverage percentages
3. Identify which markets have missing fields
4. Use this info to prioritize data enrichment

### Exporting for Analysis
1. Go to **System Info** page
2. Click "Export Reports as CSV" or "Export as JSON"
3. Download file to your computer
4. Use in Excel, Python, or BI tools

### Monitoring Scraper Health
1. Go to **Version History** page
2. Check success rate in pie chart
3. Review recent scrape logs for errors
4. If errors exist, check error types

---

## 🛠️ Troubleshooting

### Dashboard Won't Load
```bash
# Check if port 8501 is already in use
lsof -i :8501

# Use different port
venv/bin/streamlit run dashboard.py --server.port 8502
```

### Data Not Updating
```bash
# Refresh page in browser (F5)
# Or restart dashboard:
# 1. Stop current instance (Ctrl+C)
# 2. Re-run: ./run_dashboard.sh
```

### Missing Data in Charts
- Ensure scraper has been run: `venv/bin/python -m src.cli scrape`
- Check **Data Quality** page to see coverage
- Some fields may not be available for all markets

---

## 📱 Dashboard Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Refresh | F5 |
| Full Screen | F11 |
| Developer Tools | F12 |
| Menu Toggle | Ctrl+M |

---

## 🚀 Deploying to Production

### Using Streamlit Cloud (Free)
1. Push code to GitHub
2. Visit https://streamlit.io/cloud
3. Connect your GitHub repo
4. Deploy with one click

### Using Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "dashboard.py"]
```

### Using Heroku
```bash
# Create Procfile
echo "web: venv/bin/streamlit run dashboard.py --server.port $PORT" > Procfile

# Deploy
git push heroku main
```

---

## 📊 API Endpoints (Future Enhancement)

Future versions could add REST API:
```
/api/reports
/api/reports/<slug>
/api/versions/<report_id>
/api/stats
```

---

## 💡 Tips & Tricks

1. **Bookmark the dashboard:** Save `http://localhost:8501` to favorites
2. **Use keyboard shortcuts:** Ctrl+M toggles sidebar
3. **Export regularly:** Keep CSV backups of market data
4. **Monitor trends:** Check dashboard weekly for new market insights
5. **Share findings:** Use export feature to share with team

---

## 📞 Support

For issues with:
- **Dashboard features:** Check this guide
- **Data accuracy:** Review Data Quality page
- **Scraper issues:** See main README.md
- **Database issues:** Run `venv/bin/python -m src.cli stats`

---

**Happy analyzing! 📈**

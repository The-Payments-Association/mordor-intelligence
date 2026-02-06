# Monitor Update Frequency - Build Your Own Historical Data

## The Situation

Wayback Machine doesn't have snapshots for Mordor Intelligence reports yet (likely too new or site blocks it). But we can **build our own historical tracking** starting NOW.

---

## Strategy: Monthly Tracking Over Time

Instead of relying on Wayback Machine, we'll track update patterns ourselves:

### What We'll Do

**Month 1 (Feb 2026):** Scrape and note dates
```
South America RTP: Modified Jan 30, 2026
Brazil Payments: Modified Jan 15, 2026
UK Gateway: Modified Feb 1, 2026
```

**Month 2 (Mar 2026):** Scrape again and compare
```
South America RTP: Still Jan 30 (no change) ❌
Brazil Payments: Now Feb 10, 2026 (CHANGED) ✅
UK Gateway: Still Feb 1 (no change) ❌

Update: Brazil market was updated in the past month
```

**Month 3 (Apr 2026):** Continue pattern
```
...continue tracking...
```

**After 12 Months:** You'll have clear update patterns 📊

---

## Implementation: Track Updates in Database

### Step 1: Add Update Tracking Table

```sql
CREATE TABLE market_update_tracking (
    tracking_id INTEGER PRIMARY KEY,
    report_id INTEGER,
    scrape_date DATE,
    page_date_modified DATE,
    changed_fields TEXT,  -- JSON list of what changed
    is_update BOOLEAN,    -- Did anything change since last check?
    days_since_last_update INT,
    FOREIGN KEY(report_id) REFERENCES reports(id)
);
```

### Step 2: Track on Each Scrape

```python
# In src/scrapers/report_scraper.py

def track_update(report_id, scrape_date, new_modified_date, changed_fields):
    """
    Track when a report was last updated.
    """
    conn = duckdb.connect('data/mordor.duckdb')

    # Get previous record
    previous = conn.execute("""
        SELECT page_date_modified, scrape_date
        FROM market_update_tracking
        WHERE report_id = ?
        ORDER BY scrape_date DESC
        LIMIT 1
    """, [report_id]).fetchone()

    if previous:
        prev_date, prev_scrape = previous
        is_update = (new_modified_date != prev_date)
        days_since = (scrape_date - prev_scrape).days
    else:
        is_update = True  # First time
        days_since = 0

    # Record this tracking
    conn.execute("""
        INSERT INTO market_update_tracking
        (report_id, scrape_date, page_date_modified, changed_fields, is_update, days_since_last_update)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [report_id, scrape_date, new_modified_date,
          json.dumps(changed_fields), is_update, days_since])

    conn.commit()
    conn.close()
```

### Step 3: Analyze Patterns Monthly

```python
# src/analytics/update_frequency_monitor.py

def analyze_monthly_updates():
    """
    Analyze update patterns from our tracking data.
    Run this at end of each month.
    """
    conn = duckdb.connect('data/mordor.duckdb')

    # Get all markets' update history
    history = conn.execute("""
        SELECT
            r.slug,
            mut.scrape_date,
            mut.is_update,
            LAG(mut.scrape_date) OVER (PARTITION BY r.id ORDER BY mut.scrape_date) as prev_scrape
        FROM market_update_tracking mut
        JOIN reports r ON mut.report_id = r.id
        ORDER BY r.slug, mut.scrape_date
    """).fetchall()

    # Calculate stats per market
    updates_by_market = {}

    for slug, scrape_date, is_update, prev_scrape in history:
        if slug not in updates_by_market:
            updates_by_market[slug] = {
                'total_checks': 0,
                'updates_found': 0,
                'days_between_updates': [],
                'last_update': None
            }

        updates_by_market[slug]['total_checks'] += 1

        if is_update:
            updates_by_market[slug]['updates_found'] += 1
            updates_by_market[slug]['last_update'] = scrape_date

            if prev_scrape:
                days = (scrape_date - prev_scrape).days
                updates_by_market[slug]['days_between_updates'].append(days)

    # Generate report
    print_frequency_report(updates_by_market)

    return updates_by_market


def print_frequency_report(stats):
    """
    Print human-readable frequency report.
    """
    print("\n" + "=" * 100)
    print("📊 UPDATE FREQUENCY REPORT")
    print("=" * 100)

    for slug, data in sorted(stats.items()):
        total = data['total_checks']
        updates = data['updates_found']
        update_rate = (updates / total * 100) if total > 0 else 0

        print(f"\n{slug}")
        print(f"  Checks: {total} | Updates: {updates} ({update_rate:.0f}%)")

        if data['days_between_updates']:
            avg_gap = sum(data['days_between_updates']) / len(data['days_between_updates'])
            print(f"  Avg days between updates: {avg_gap:.0f}")

            # Determine frequency
            if avg_gap < 30:
                freq = "MONTHLY"
            elif avg_gap < 90:
                freq = "QUARTERLY"
            elif avg_gap < 180:
                freq = "SEMI-ANNUAL"
            else:
                freq = "YEARLY"

            print(f"  Estimated frequency: {freq}")

        if data['last_update']:
            days_ago = (datetime.now().date() - data['last_update']).days
            print(f"  Last update: {days_ago} days ago")
```

---

## Dashboard Feature: Update Tracker

### Add to Dashboard: "📊 Update Frequency Monitor"

```python
# In dashboard.py

elif page == "📊 Update Frequency Monitor":
    st.header("📊 Market Update Frequency Monitor")

    st.markdown("""
    <div class='assumption-box'>
    <h4>⏱️ Tracking Update Patterns</h4>
    <p>We monitor when each report is updated to optimize scraping frequency.
    This page shows patterns discovered so far.</p>
    </div>
    """, unsafe_allow_html=True)

    # Get current tracking data
    conn = get_connection()
    tracking = conn.execute("""
        SELECT
            r.slug,
            r.title,
            COUNT(*) as checks,
            SUM(CASE WHEN mut.is_update THEN 1 ELSE 0 END) as updates,
            MAX(mut.page_date_modified) as last_modified,
            MAX(mut.scrape_date) as last_check
        FROM market_update_tracking mut
        JOIN reports r ON mut.report_id = r.id
        GROUP BY r.slug, r.title
        ORDER BY updates DESC
    """).df()

    conn.close()

    # Show metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Markets Tracked", len(tracking))

    with col2:
        total_updates = tracking['updates'].sum()
        st.metric("Total Updates Found", int(total_updates))

    with col3:
        avg_updates = tracking['updates'].mean()
        st.metric("Avg Updates per Market", f"{avg_updates:.1f}")

    with col4:
        st.metric("Monitoring Since", "Feb 2026")

    st.divider()

    # Show detailed tracking table
    st.subheader("📋 Update History by Market")

    tracking['update_rate'] = (tracking['updates'] / tracking['checks'] * 100).round(1)
    tracking['last_modified'] = pd.to_datetime(tracking['last_modified']).dt.strftime('%Y-%m-%d')
    tracking['last_check'] = pd.to_datetime(tracking['last_check']).dt.strftime('%Y-%m-%d')

    display_cols = ['slug', 'checks', 'updates', 'update_rate', 'last_modified', 'last_check']

    st.dataframe(
        tracking[display_cols].rename(columns={
            'slug': 'Market',
            'checks': 'Scrapes',
            'updates': 'Updates Found',
            'update_rate': 'Update %',
            'last_modified': 'Last Modified',
            'last_check': 'Last Checked'
        }),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # Prediction section
    st.subheader("🎯 Update Predictions (After 6+ months)")

    st.info("""
    After monitoring for 6-12 months, we'll be able to predict:

    ✓ Which markets update monthly, quarterly, or yearly
    ✓ Optimal scraping frequency for each market
    ✓ When to expect next updates
    ✓ Which markets are most volatile
    ✓ Seasonal update patterns

    Check back in Q3 2026 for detailed predictions!
    """)
```

---

## Quarterly Analysis Reports

### Q2 2026 Analysis (3 months of data)

```
MARKET REPORT UPDATE FREQUENCY
Q2 2026 (Feb, Mar, Apr)

SUMMARY:
- Markets Monitored: 40
- Scrapes Performed: 120
- Updates Found: 32
- Overall Update Rate: 26.7%

FREQUENCY GROUPS:

FREQUENT UPDATERS (Update >40%):
- Brazil Payments: 60% updates
- Colombia Fintech: 50% updates
- Mexico Digital: 45% updates

REGULAR UPDATERS (20-40%):
- South America RTP: 33%
- Asia Pacific Mobile: 25%
- UK Payment Gateway: 20%

STABLE (< 20%):
- Australia Payments: 15%
- Europe Banking: 10%
- Africa Markets: 5%

RECOMMENDATIONS:
- For frequent updaters: Scrape monthly ✓ (current plan)
- For regular: Monitor carefully, may skip summer
- For stable: Consider quarterly scraping to save resources

NEXT REVIEW: Q3 2026
```

---

## Build Your Own Timeline

### Now Through Rest of 2026

| Month | Action | What We Learn |
|-------|--------|---------------|
| **Feb** | Initial scrape | Baseline |
| **Mar** | Scrape & compare | Which changed since Feb? |
| **Apr** | Scrape & compare | Quarterly pattern starting? |
| **May** | Scrape & compare | Monthly pattern clear? |
| **Jun** | Scrape & compare | Summer updates? |
| **Jul** | Analyze patterns | 5 months of data |
| **Aug** | Scrape & compare | Seasonal patterns? |
| **Sep** | Analyze patterns | 7 months of data |
| **Oct** | Scrape & compare | Quarterly refresh? |
| **Nov** | Analyze patterns | 9 months = strong patterns |
| **Dec** | Full analysis | Year-end review |

### By January 2027:
- ✅ Clear update frequency per market
- ✅ Seasonal patterns identified
- ✅ Optimal scraping schedule determined
- ✅ Cost optimization opportunities
- ✅ Predictive model for next updates

---

## Cost Impact Analysis

### Current Plan (Monthly Scraping)
```
Costs:
- 12 scrapes/year × 40 markets = 480 scrape operations
- ~$5/month in bandwidth = $60/year

After Analysis (Optimized Scraping):
- 6 monthly markets × 12 = 72
- 12 quarterly markets × 4 = 48
- 22 yearly markets × 1 = 22
Total: 142 scrape operations (-70%)

Savings: $42/year (modest, but principle of efficiency)
Benefits: Better data organization, smarter operations
```

---

## Implementation Checklist

### Phase 1: Setup (This Month)
- [x] Create update_tracking table
- [x] Add tracking to scraper
- [x] Add dashboard monitoring page
- [x] Start collecting data

### Phase 2: Monthly Monitoring (Feb-Jun)
- [ ] Run scraper on 1st of each month
- [ ] Review tracking data weekly
- [ ] Document any anomalies
- [ ] Note seasonal patterns

### Phase 3: Analysis (July)
- [ ] Analyze 5 months of patterns
- [ ] Generate frequency report
- [ ] Identify market groups
- [ ] Make optimization recommendations

### Phase 4: Implementation (Aug-Sep)
- [ ] Test optimized schedule
- [ ] Implement selective scraping
- [ ] Monitor for missed updates
- [ ] Adjust if needed

### Phase 5: Prediction (Oct-Dec)
- [ ] Build update prediction model
- [ ] Create quarterly reports
- [ ] Plan next year's strategy
- [ ] Share findings with team

---

## Real-World Insights You'll Get

### Example Findings

**Brazil Digital Payments:**
- Updates every month on ~20th
- CAGR updates in Jan, Apr, Aug
- Market size updates all year
- Action: Scrape weekly (catch updates early)

**Australia Payments:**
- Updates quarterly: Feb, May, Aug, Nov
- Predictable cycle
- Action: Scrape these 4 months only

**Europe Banking:**
- Yearly update in January
- Very stable
- Action: Scrape Jan 1st only

**Africa Markets:**
- Sporadic updates
- No clear pattern
- Action: Scrape monthly but flag anomalies

---

## Next Level: Predictive Insights

After 12 months, you can:

1. **Predict Update Dates**
   - "Brazil market will update March 20 ± 3 days"
   - "Australia is due for Q2 update"

2. **Detect Anomalies**
   - "This market is 2 weeks late for expected update"
   - "Unusual number of changes this month"

3. **Optimize Alerts**
   - "New data available - 15% growth in Colombia"
   - "Forecast accuracy: Below expectations"

4. **Plan Resources**
   - Batch high-update months
   - Slack off in low-update months
   - Budget accordingly

---

## Start Today

### This Month (Feb 2026):
1. ✅ Scrape all 40 reports (done!)
2. ✅ Record page_date_modified for each
3. ✅ Create update_tracking table
4. ✅ Add monitoring dashboard
5. ✅ Document baseline

### Next Month (Mar 2026):
1. Run scraper again
2. Compare dates
3. Record which changed
4. Generate first monthly report

### Repeat monthly through 2026...

By end of year, you'll have **12 months of real data** showing exactly how frequently each market updates!

---

## Questions You'll Answer

✅ Do we really need monthly scraping?
✅ Which markets are volatile?
✅ Which are stable?
✅ Is there a quarterly refresh pattern?
✅ Do updates happen in specific months?
✅ Which fields change most?
✅ Can we predict next update?
✅ Should we optimize resources?

**All answered by December 2026!** 📊

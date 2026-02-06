"""
Web Dashboard for Mordor Intelligence Market Reports
Built with Streamlit
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Mordor Intelligence Markets",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .header-title {
        color: #1f77b4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_connection():
    return duckdb.connect('data/mordor.duckdb')

def load_reports():
    """Load all reports"""
    conn = get_connection()
    return conn.execute("SELECT * FROM reports").df()

def load_versions():
    """Load version history"""
    conn = get_connection()
    return conn.execute("""
        SELECT rv.*, r.slug as report_slug
        FROM report_versions rv
        JOIN reports r ON rv.report_id = r.id
    """).df()

def load_logs():
    """Load scrape logs"""
    conn = get_connection()
    return conn.execute("SELECT * FROM scrape_log").df()

# Title
st.markdown('<div class="header-title">📊 Mordor Intelligence Market Dashboard</div>', unsafe_allow_html=True)
st.markdown("Analysis of payment market reports with real-time versioning and change tracking")

# Sidebar navigation
st.sidebar.title("🗂️ Navigation")
page = st.sidebar.radio("Select View", [
    "📈 Overview",
    "🌍 Market Analysis",
    "📊 Regional Breakdown",
    "💾 Data Quality",
    "📝 Version History",
    "⚙️ System Info"
])

# Load data
reports_df = load_reports()
versions_df = load_versions()
logs_df = load_logs()

# ==================== OVERVIEW PAGE ====================
if page == "📈 Overview":
    st.header("Dashboard Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Markets",
            len(reports_df),
            "40 discoverable"
        )

    with col2:
        avg_cagr = reports_df['cagr_percent'].mean()
        st.metric(
            "Avg CAGR",
            f"{avg_cagr:.2f}%",
            "Across all markets"
        )

    with col3:
        total_size = reports_df['market_size_current_value'].sum()
        st.metric(
            "Total Market Size",
            f"${total_size:,.0f}B",
            "Current value"
        )

    with col4:
        last_scrape = logs_df['started_at'].max()
        st.metric(
            "Last Updated",
            last_scrape.strftime('%Y-%m-%d'),
            "Data freshness"
        )

    st.divider()

    # Top 10 markets by CAGR
    st.subheader("🚀 Top 10 Fastest Growing Markets")

    top_10 = reports_df[reports_df['cagr_percent'].notna()].nlargest(10, 'cagr_percent')[
        ['slug', 'cagr_percent', 'market_size_current_value', 'region']
    ].reset_index(drop=True)

    if len(top_10) > 0:
        # Create chart
        fig = px.bar(
            top_10,
            x='slug',
            y='cagr_percent',
            color='cagr_percent',
            color_continuous_scale='RdYlGn',
            hover_data=['market_size_current_value', 'region'],
            title='CAGR Comparison',
            labels={'cagr_percent': 'CAGR %', 'slug': 'Market'}
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Table
        st.dataframe(
            top_10.rename(columns={
                'slug': 'Market',
                'cagr_percent': 'CAGR %',
                'market_size_current_value': 'Current Size',
                'region': 'Region'
            }),
            use_container_width=True,
            hide_index=True
        )

# ==================== MARKET ANALYSIS PAGE ====================
elif page == "🌍 Market Analysis":
    st.header("Market Details")

    # Select market
    markets = reports_df['slug'].tolist()
    selected_market = st.selectbox("Select a market:", markets)

    # Get market data
    market_data = reports_df[reports_df['slug'] == selected_market].iloc[0]

    # Display details
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("CAGR", f"{market_data['cagr_percent']:.2f}%" if pd.notna(market_data['cagr_percent']) else "N/A")

    with col2:
        st.metric("Current Market Size", f"${market_data['market_size_current_value']:.2f} {market_data['market_size_current_unit']}"
                  if pd.notna(market_data['market_size_current_value']) else "N/A")

    with col3:
        st.metric("Region", market_data['region'] if pd.notna(market_data['region']) else "N/A")

    st.divider()

    # Market details
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Market Info")
        st.write(f"**Title:** {market_data['title']}")
        st.write(f"**Study Period:** {market_data['study_period_start']} - {market_data['study_period_end']}")

        if pd.notna(market_data['fastest_growing_country']):
            st.write(f"**Fastest Growing:** {market_data['fastest_growing_country']} ({market_data['fastest_growing_country_cagr']:.2f}% CAGR)")

    with col2:
        st.subheader("☁️ Deployment")
        if pd.notna(market_data['cloud_share_percent']):
            st.write(f"**Cloud Share:** {market_data['cloud_share_percent']:.2f}%")

        if pd.notna(market_data['leading_segment_name']):
            st.write(f"**Leading Segment:** {market_data['leading_segment_name']}")
            st.write(f"**Share:** {market_data['leading_segment_share_percent']:.2f}%")

    st.divider()

    # Forecast chart
    if pd.notna(market_data['market_size_forecast_value']):
        st.subheader("📈 Market Forecast")

        forecast_data = pd.DataFrame({
            'Year': [
                market_data['market_size_current_year'],
                market_data['market_size_forecast_year']
            ],
            'Size': [
                market_data['market_size_current_value'],
                market_data['market_size_forecast_value']
            ]
        })

        fig = px.line(
            forecast_data,
            x='Year',
            y='Size',
            markers=True,
            title=f"Market Size Forecast ({market_data['market_size_current_unit']})"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Version history
    st.subheader("📝 Version History")
    market_versions = versions_df[versions_df['report_slug'] == selected_market].sort_values('version_number')

    if len(market_versions) > 0:
        version_table = market_versions[[
            'version_number', 'snapshot_reason', 'scraped_at', 'changed_fields'
        ]].rename(columns={
            'version_number': 'Version',
            'snapshot_reason': 'Reason',
            'scraped_at': 'Date',
            'changed_fields': 'Changed Fields'
        })

        st.dataframe(version_table, use_container_width=True, hide_index=True)

# ==================== REGIONAL ANALYSIS PAGE ====================
elif page == "📊 Regional Breakdown":
    st.header("Markets by Region")

    # Group by region
    conn = get_connection()
    regional_stats = conn.execute("""
        SELECT
            region,
            COUNT(*) as market_count,
            ROUND(AVG(cagr_percent), 2) as avg_cagr,
            MAX(cagr_percent) as max_cagr,
            ROUND(SUM(market_size_current_value), 2) as total_size
        FROM reports
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY avg_cagr DESC
    """).df()

    if len(regional_stats) > 0:
        # Pie chart - markets by region
        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(
                regional_stats,
                values='market_count',
                names='region',
                title='Markets by Region'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                regional_stats,
                x='region',
                y='avg_cagr',
                color='avg_cagr',
                color_continuous_scale='Viridis',
                title='Average CAGR by Region'
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Regional Statistics")

        st.dataframe(
            regional_stats.rename(columns={
                'region': 'Region',
                'market_count': 'Markets',
                'avg_cagr': 'Avg CAGR %',
                'max_cagr': 'Max CAGR %',
                'total_size': 'Total Size'
            }),
            use_container_width=True,
            hide_index=True
        )

# ==================== DATA QUALITY PAGE ====================
elif page == "💾 Data Quality":
    st.header("Data Extraction Quality")

    total_reports = len(reports_df)

    # Calculate coverage
    cagr_coverage = (reports_df['cagr_percent'].notna().sum() / total_reports * 100)
    size_coverage = (reports_df['market_size_current_value'].notna().sum() / total_reports * 100)
    players_coverage = (reports_df['major_players'].notna().sum() / total_reports * 100)

    # Display metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("CAGR Coverage", f"{cagr_coverage:.1f}%")

    with col2:
        st.metric("Market Size Coverage", f"{size_coverage:.1f}%")

    with col3:
        st.metric("Major Players Coverage", f"{players_coverage:.1f}%")

    st.divider()

    # Coverage chart
    coverage_data = pd.DataFrame({
        'Field': ['CAGR %', 'Market Size', 'Major Players'],
        'Coverage %': [cagr_coverage, size_coverage, players_coverage]
    })

    fig = px.bar(
        coverage_data,
        x='Field',
        y='Coverage %',
        color='Coverage %',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100],
        title='Data Extraction Coverage',
        labels={'Coverage %': 'Coverage %'}
    )
    fig.add_hline(y=100, line_dash="dash", line_color="green", annotation_text="Target: 100%")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Detailed stats
    st.subheader("Field Statistics")

    stats_data = pd.DataFrame({
        'Field': [
            'CAGR %',
            'Market Size (Current)',
            'Market Size (Forecast)',
            'Region',
            'Fastest Growing Country',
            'Cloud Share %',
            'Major Players'
        ],
        'Extracted': [
            reports_df['cagr_percent'].notna().sum(),
            reports_df['market_size_current_value'].notna().sum(),
            reports_df['market_size_forecast_value'].notna().sum(),
            reports_df['region'].notna().sum(),
            reports_df['fastest_growing_country'].notna().sum(),
            reports_df['cloud_share_percent'].notna().sum(),
            reports_df['major_players'].notna().sum()
        ],
        'Missing': [
            reports_df['cagr_percent'].isna().sum(),
            reports_df['market_size_current_value'].isna().sum(),
            reports_df['market_size_forecast_value'].isna().sum(),
            reports_df['region'].isna().sum(),
            reports_df['fastest_growing_country'].isna().sum(),
            reports_df['cloud_share_percent'].isna().sum(),
            reports_df['major_players'].isna().sum()
        ]
    })

    st.dataframe(stats_data, use_container_width=True, hide_index=True)

# ==================== VERSION HISTORY PAGE ====================
elif page == "📝 Version History":
    st.header("Version & Change History")

    # Scrape runs
    conn = get_connection()
    runs = conn.execute("""
        SELECT DISTINCT run_id, MIN(started_at) as start_time, COUNT(*) as reports_checked
        FROM scrape_log
        GROUP BY run_id
        ORDER BY start_time DESC
    """).df()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Scrape Runs")
        st.dataframe(
            runs.rename(columns={
                'run_id': 'Run ID',
                'start_time': 'Start Time',
                'reports_checked': 'Reports'
            }),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("📊 Scrape Summary")

        success = logs_df[logs_df['status'] == 'success'].shape[0]
        errors = logs_df[logs_df['status'] == 'error'].shape[0]
        skipped = logs_df[logs_df['status'] == 'skipped'].shape[0]

        summary_data = pd.DataFrame({
            'Status': ['Success', 'Error', 'Skipped'],
            'Count': [success, errors, skipped]
        })

        fig = px.pie(
            summary_data,
            values='Count',
            names='Status',
            color='Status',
            color_discrete_map={'Success': 'green', 'Error': 'red', 'Skipped': 'orange'}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Recent scrape logs
    st.subheader("Recent Scrape Logs")

    recent_logs = logs_df.nlargest(20, 'started_at')[[
        'report_slug', 'status', 'error_type', 'response_time_ms', 'started_at'
    ]].rename(columns={
        'report_slug': 'Market',
        'status': 'Status',
        'error_type': 'Error Type',
        'response_time_ms': 'Response (ms)',
        'started_at': 'Time'
    })

    st.dataframe(recent_logs, use_container_width=True, hide_index=True)

# ==================== SYSTEM INFO PAGE ====================
elif page == "⚙️ System Info":
    st.header("System Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Reports", len(reports_df))

    with col2:
        st.metric("Total Versions", len(versions_df))

    with col3:
        st.metric("Total Log Entries", len(logs_df))

    st.divider()

    # Database stats
    st.subheader("📊 Database Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Last Scrape Run:**")
        last_run = logs_df['started_at'].max()
        st.write(f"- Time: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"- Success Rate: {(logs_df['status'] == 'success').sum() / len(logs_df) * 100:.1f}%")

    with col2:
        st.write("**Data Coverage:**")
        st.write(f"- CAGR: {(reports_df['cagr_percent'].notna().sum() / len(reports_df) * 100):.1f}%")
        st.write(f"- Market Size: {(reports_df['market_size_current_value'].notna().sum() / len(reports_df) * 100):.1f}%")
        st.write(f"- Region: {(reports_df['region'].notna().sum() / len(reports_df) * 100):.1f}%")

    st.divider()

    # Export options
    st.subheader("📥 Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Export Reports as CSV"):
            csv = reports_df[[
                'slug', 'title', 'cagr_percent', 'market_size_current_value',
                'market_size_current_unit', 'region', 'fastest_growing_country'
            ]].to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"market_reports_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("📥 Export as JSON"):
            json_data = reports_df[[
                'slug', 'title', 'cagr_percent', 'market_size_current_value',
                'region'
            ]].to_json(orient='records', indent=2)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"market_reports_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

    st.divider()

    # Help
    st.subheader("ℹ️ About This Dashboard")
    st.write("""
    This dashboard provides real-time analysis of Mordor Intelligence payment market reports.

    **Features:**
    - 📈 Real-time market analysis
    - 🌍 Regional breakdowns
    - 📊 Data quality metrics
    - 📝 Full version history tracking
    - 💾 Export capabilities

    **Database:**
    - Location: `data/mordor.duckdb`
    - Reports: 40 payment market reports
    - Versioning: Complete change tracking
    - Last Updated: {logs_df['started_at'].max().strftime('%Y-%m-%d %H:%M:%S')}
    """.format(**{'logs_df': logs_df}))

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em; margin-top: 50px;'>
    🔄 Auto-refreshes every 5 minutes | 📊 Mordor Intelligence Market Dashboard
</div>
""", unsafe_allow_html=True)

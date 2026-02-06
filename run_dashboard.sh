#!/bin/bash
# Launch Mordor Intelligence Web Dashboard

echo "🚀 Starting Mordor Intelligence Dashboard..."
echo ""
echo "📊 Open your browser to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

venv/bin/streamlit run dashboard.py \
    --logger.level=error \
    --client.showErrorDetails=false \
    --theme.primaryColor="#1f77b4" \
    --theme.backgroundColor="#ffffff" \
    --theme.secondaryBackgroundColor="#f0f2f6"

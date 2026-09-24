#!/bin/bash
# Stop any existing Streamlit process holding port 8501
echo "Freeing port 8501..."
pkill -f streamlit 2>/dev/null || true
fuser -k 8501/tcp 2>/dev/null || true
sleep 1

echo "Starting Streamlit on port 8501..."
python3 -m streamlit run app_streamlit.py --server.port 8501 --server.address 0.0.0.0

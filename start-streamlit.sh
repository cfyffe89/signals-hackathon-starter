#!/bin/bash
# Free port 8501 robustly
echo "Stopping any existing Streamlit processes on port 8501..."
pkill -9 -f streamlit 2>/dev/null || true
pkill -9 -f app_streamlit.py 2>/dev/null || true
if command -v fuser &> /dev/null; then
    fuser -k -9 8501/tcp 2>/dev/null || true
fi
if command -v lsof &> /dev/null; then
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
fi
sleep 1

echo "Starting Streamlit dashboard on port 8501..."
python3 -m streamlit run app_streamlit.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

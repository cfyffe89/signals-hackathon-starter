#!/usr/bin/env bash
# Start (or restart) the two apps.   ./scripts/start.sh [api|ui|all]   (default: all)
# Logs: /tmp/api.log and /tmp/ui.log
cd "$(dirname "$0")/.."
what="${1:-all}"
if [[ "$what" == "api" || "$what" == "all" ]]; then
  pkill -f "uvicorn backend.app:app" 2>/dev/null || true
  nohup python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload > /tmp/api.log 2>&1 &
  echo "FastAPI   → port 8000 (log: /tmp/api.log)"
fi
if [[ "$what" == "ui" || "$what" == "all" ]]; then
  pkill -f "streamlit run app_streamlit.py" 2>/dev/null || true
  nohup python -m streamlit run app_streamlit.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > /tmp/ui.log 2>&1 &
  echo "Streamlit → port 8501 (log: /tmp/ui.log)"
fi

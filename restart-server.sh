#!/bin/bash
# Restart the Signals Hackathon Starter server interactively
echo 'Restarting Signals Starter Dashboard...'
pkill -f 'uvicorn backend.app:app' 2>/dev/null || true
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

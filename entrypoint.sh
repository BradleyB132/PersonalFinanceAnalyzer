#!/bin/bash
# Entrypoint script to run both Streamlit and health check server

# Start health check server in background
python src/health_check.py &
HEALTH_PID=$!

# Start Streamlit app in foreground
streamlit run src/app.py --server.port=8501 --server.address=0.0.0.0

# Cleanup on exit
trap "kill $HEALTH_PID" EXIT

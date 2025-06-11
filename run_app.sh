#!/bin/bash

echo "Starting Products Finder Application..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and fill in your MongoDB credentials."
    exit 1
fi

echo ""
echo "Starting FastAPI server in background..."
uvicorn main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "Waiting for API server to start..."
sleep 5

echo ""
echo "Starting Streamlit UI..."
echo ""
echo "========================================"
echo "  FastAPI Server: http://localhost:8000"
echo "  Streamlit UI:   http://localhost:8501"
echo "========================================"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $API_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start Streamlit
streamlit run streamlit_app.py --server.port 8501

# Cleanup when Streamlit exits
cleanup
#!/bin/bash

echo "🚀 Starting Tazama API Test Client..."
echo ""
echo "📡 Target: TMS Service at http://localhost:5001"
echo "🌐 Web UI: http://localhost:8080"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Start FastAPI
echo ""
echo "✅ Starting server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

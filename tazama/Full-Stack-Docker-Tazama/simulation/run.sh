#!/bin/bash

# Ensure cleanup of background processes on exit
trap "kill 0" EXIT

echo "🔥 Starting Tazama Velocity Attack Simulation..."

# Start FastAPI Mock Server in the background
echo "🟢 Starting Mock TMS Server (Port 8000)..."
uvicorn main:app --port 8000 --log-level warning &

# Allow server time to boot
sleep 2

# Run the Attack Simulation
echo "⚔️  Launching Velocity Attack Client..."
python3 simulation.py

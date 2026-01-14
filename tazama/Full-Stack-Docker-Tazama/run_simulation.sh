#!/bin/bash

echo "🚀 Building and Running Velocity Attack Simulation..."

# Ensure we are in the right directory
# If executed from outside, cd into it
if [ ! -f "docker-compose.simulation.yaml" ]; then
    echo "❌ Error: Could not find docker-compose.simulation.yaml"
    echo "Please run this script from the Full-Stack-Docker-Tazama root directory."
    exit 1
fi

# Run the simulation container attached to the existing tazama project
# We use 'docker compose run' to execute it as a one-off task
# using the same network as the running stack (assuming project name 'tazama')
docker compose -p tazama -f docker-compose.simulation.yaml build
docker compose -p tazama -f docker-compose.simulation.yaml run --rm velocity-sim

echo "✅ Simulation container finished."

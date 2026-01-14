#!/bin/bash
echo "🚀 Configuring Tazama Database with Extra Rules..."

# 1. Copy SQL file to container
docker cp setup_extra_rules.sql tazama-postgres-1:/tmp/setup_extra_rules.sql
if [ $? -ne 0 ]; then
    echo "❌ Failed to copy SQL file to container. Is 'tazama-postgres-1' running?"
    exit 1
fi

# 2. Execute SQL via psql
docker exec -i tazama-postgres-1 psql -U postgres -d configuration -f /tmp/setup_extra_rules.sql
if [ $? -ne 0 ]; then
    echo "❌ Failed to execute SQL script."
    exit 1
fi

echo "✅ Database configuration updated successfully!"
echo "Please restart the simulation/client to verify results."

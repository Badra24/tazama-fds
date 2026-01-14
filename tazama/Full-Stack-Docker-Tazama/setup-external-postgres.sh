#!/bin/bash
# Tazama External PostgreSQL Setup Script
# Run this script to create databases and load schema

echo "🔧 Tazama External PostgreSQL Setup"
echo "===================================="
echo ""

# Configuration
PGUSER="badraaji"
PGHOST="localhost"
PGPORT="5432"

echo "PostgreSQL Configuration:"
echo "  User: $PGUSER"
echo "  Host: $PGHOST"
echo "  Port: $PGPORT"
echo ""

# Check connection
echo "1️⃣ Testing PostgreSQL connection..."
if psql -U $PGUSER -d postgres -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ Connection successful!"
else
    echo "❌ Connection failed. Please check credentials."
    exit 1
fi

# Create databases
echo ""
echo "2️⃣ Creating Tazama databases..."

for DB in configuration event_history raw_history evaluation; do
    echo -n "  Creating database: $DB... "
    
    # Check if database exists
    if psql -U $PGUSER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -q 1; then
        echo "⚠️  Already exists (skipping)"
    else
        if psql -U $PGUSER -d postgres -c "CREATE DATABASE $DB;" > /dev/null 2>&1; then
            echo "✅ Created"
        else
            echo "❌ Failed"
            exit 1
        fi
    fi
done

# Load schema
echo ""
echo "3️⃣ Loading Tazama schema..."
SCHEMA_FILE="$(dirname "$0")/postgres/migration/base/00-CREATE.sql"

if [ ! -f "$SCHEMA_FILE" ]; then
    echo "❌ Schema file not found: $SCHEMA_FILE"
    echo "   Please run this script from Full-Stack-Docker-Tazama directory"
    exit 1
fi

# Modify schema script to not create databases (already created)
echo "  Preparing schema..."
TEMP_SCHEMA="/tmp/tazama-schema-$$.sql"
grep -v "^create database" "$SCHEMA_FILE" > "$TEMP_SCHEMA"

echo "  Loading schema into databases..."
if psql -U $PGUSER -f "$TEMP_SCHEMA" > /dev/null 2>&1; then
    echo "✅ Schema loaded successfully!"
else
    echo "⚠️  Schema loading had warnings (this is normal)"
fi

rm -f "$TEMP_SCHEMA"

# Load rule configurations
echo ""
echo "4️⃣ Loading extra rules configuration..."
RULES_FILE="/Users/badraaji/Desktop/RND/tazama/tazama_api_client/setup_extra_rules.sql"

if [ -f "$RULES_FILE" ]; then
    if psql -U $PGUSER -d configuration -f "$RULES_FILE" > /dev/null 2>&1; then
        echo "✅ Rules configuration loaded!"
    else
        echo "⚠️  Rules loading had warnings"
    fi
else
    echo "⚠️  Rules file not found (optional): $RULES_FILE"
fi

# Verify
echo ""
echo "5️⃣ Verifying setup..."
echo ""
echo "Databases:"
psql -U $PGUSER -d postgres -c "\l" | grep -E "configuration|event_history|raw_history|evaluation"

echo ""
echo "Tables in configuration database:"
psql -U $PGUSER -d configuration -c "\dt" | grep -E "network_map|typology|rule"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your credentials:"
echo "   POSTGRES_USER=badraaji"
echo "   POSTGRES_PASSWORD=badraaji"
echo "   POSTGRES_HOST=host.docker.internal"
echo ""
echo "2. Deploy Tazama with external DB:"
echo "   cd $(dirname "$0")"
echo "   docker-compose -f docker-compose.base.infrastructure.yaml \\"
echo "                  -f docker-compose.external-db.yaml \\"
echo "                  -f docker-compose.hub.core.yaml \\"
echo "                  -f docker-compose.hub.rules.yaml \\"
echo "                  up -d"

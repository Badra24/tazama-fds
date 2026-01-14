#!/bin/bash
# Tazama Startup Script - With Local PostgreSQL
# Database: badraaji (port 5430)

set -e

echo "🚀 Starting Tazama with Local PostgreSQL"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PostgreSQL is running
echo -n "1️⃣  Checking PostgreSQL connection... "
if psql -p 5430 -U badraaji -d badraaji -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    echo ""
    echo "⚠️  PostgreSQL not accessible at port 5430"
    echo "   Please ensure Postgres.app is running"
    echo "   or run: psql -p 5430 -U badraaji -d badraaji"
    exit 1
fi

# Check if tazama schema exists
echo -n "2️⃣  Checking tazama schema... "
SCHEMA_EXISTS=$(psql -p 5430 -U badraaji -d badraaji -tAc "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'tazama'")
if [ "$SCHEMA_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo ""
    echo "⚠️  Schema 'tazama' does not exist in database 'badraaji'"
    echo "   Please run schema setup first"
    exit 1
fi

# Check rules count
echo -n "3️⃣  Checking rules configuration... "
RULES_COUNT=$(psql -p 5430 -U badraaji -d badraaji -tAc "SELECT COUNT(*) FROM tazama.rule")
if [ "$RULES_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✓ $RULES_COUNT rules loaded${NC}"
else
    echo -e "${YELLOW}⚠ No rules found${NC}"
fi

echo ""
echo "4️⃣  Starting Docker containers..."
echo ""

# Stop any existing containers
docker-compose -f docker-compose.yml -f docker-compose.rules.yml down 2>/dev/null || true

# Start services
docker-compose -f docker-compose.yml -f docker-compose.rules.yml up -d

echo ""
echo "5️⃣  Waiting for services to be ready..."
sleep 5

# Check service health
echo ""
echo "Service Status:"
echo "---------------"
docker-compose -f docker-compose.yml -f docker-compose.rules.yml ps

echo ""
echo -e "${GREEN}✅ Tazama is running!${NC}"
echo ""
echo "📊 Endpoints:"
echo "   - TMS API:        http://localhost:3001"
echo "   - NATS:           nats://localhost:4222"
echo "   - NATS Monitor:   http://localhost:8222"
echo ""
echo "📝 PostgreSQL:"
echo "   - Database: badraaji"
echo "   - Schema:   tazama"
echo "   - Port:     5430"
echo "   - Rules:    $RULES_COUNT"
echo ""
echo "💡 Note: TMS runs on port 3001 to avoid conflict with Full Docker (port 3001)"
echo ""
echo "🔍 Logs:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.rules.yml logs -f"
echo ""
echo "🛑 Stop:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.rules.yml down"
echo ""

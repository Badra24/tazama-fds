#!/bin/bash
docker exec -i tazama-postgres-1 psql -U postgres -d configuration -c "SELECT configuration->>'name' as name, configuration->>'active' as active, configuration->>'cfg' as version FROM network_map;"

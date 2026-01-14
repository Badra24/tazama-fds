# Tazama Fraud Detection System

A comprehensive fraud detection system built with Tazama, featuring a full-stack Docker deployment and an API client interface.

## Quick Start

### 1. Start the Full Stack Docker Environment

Navigate to the Full-Stack-Docker-Tazama directory and start all services using the interactive script:

```bash
cd Full-Stack-Docker-Tazama
./tazama.sh
```

Then select:
1. Choose **2** for "Public (DockerHub)"
2. Toggle desired addons (pgAdmin and Hasura are enabled by default)
3. Press **a** to apply, then **e** to execute

**Alternative: Direct command**

```bash
cd Full-Stack-Docker-Tazama
docker compose \
  -f docker-compose.base.infrastructure.yaml \
  -f docker-compose.base.override.yaml \
  -f docker-compose.hub.cfg.yaml \
  -f docker-compose.hub.core.yaml \
  -f docker-compose.hub.rules.yaml \
  -f docker-compose.utils.pgadmin.yaml \
  -f docker-compose.utils.hasura.yaml \
  -p tazama up -d
```

This will start all the required Tazama services including:
- PostgreSQL, Valkey (Redis), NATS
- TMS (Transaction Monitoring Service)
- Rule processors (006, 018, 901, 902)
- pgAdmin and Hasura GraphQL

### 2. Run the Tazama API Client

Once the Docker services are running, start the API client:

```bash
cd tazama_api_client
./start.sh
```

The API client will be available at `http://localhost:8080`

## Services & Ports

| Service | URL |
|---------|-----|
| Tazama API Client | http://localhost:8080 |
| TMS API | http://localhost:5001 |
| pgAdmin | http://localhost:15050 |
| Hasura GraphQL | http://localhost:6100 |
| PostgreSQL | localhost:15432 |

## Project Structure

```
tazama/
├── Full-Stack-Docker-Tazama/    # Docker compose setup for all Tazama services
├── tazama_api_client/           # FastAPI-based API client and web interface
└── tazama-local-db/             # Local database setup for development
```

## Requirements

- Docker and Docker Compose
- Python 3.8+
- macOS, Linux, or Windows (with WSL)

## Stop Services

```bash
cd Full-Stack-Docker-Tazama
docker compose -p tazama down
```

## Additional Information

For more detailed configuration and troubleshooting, please refer to the documentation in each subdirectory.

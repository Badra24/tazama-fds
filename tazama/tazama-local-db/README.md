# Tazama - Local PostgreSQL Deployment

Tazama fraud detection system dengan PostgreSQL lokal (Postgres.app port 5430).

## 📋 Prerequisites

- ✅ Docker & Docker Compose installed
- ✅ PostgreSQL 17 (Postgres.app) running on port 5430
- ✅ Database `badraaji` with schema `tazama` created
- ✅ 33 rules loaded in `tazama.rule` table

---

## 🚀 Quick Start

```bash
cd /Users/badraaji/Desktop/RND/tazama/tazama-local-db

# Start Tazama
./start.sh
```

---

## 📊 Configuration

### Database
- **Database**: `badraaji`
- **Schema**: `tazama`
- **Port**: `5430` (Postgres.app)
- **User**: `badraaji`
- **Tables**: 17 tables in `tazama` schema

### Services
- **TMS API**: http://localhost:3001 (Port 3001 to avoid conflict with Full Docker)
- **NATS**: nats://localhost:4222
- **NATS Monitor**: http://localhost:8222
- **Valkey/Redis**: redis://localhost:6379

### Rules Deployed
- Rule 006 (Structuring)
- Rule 018 (High Value Transfer)
- Rule 901 (Debtor Velocity)
- Rule 902 (Creditor Velocity)

---

## 🔧 Manual Commands

### Start Services
```bash
docker-compose -f docker-compose.yml -f docker-compose.rules.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.yml -f docker-compose.rules.yml down
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.yml -f docker-compose.rules.yml logs -f

# Specific service
docker-compose logs -f tms
docker-compose logs -f rule-901
```

### Check Status
```bash
docker-compose -f docker-compose.yml -f docker-compose.rules.yml ps
```

---

## 🗄️ Database Management

### Connect to PostgreSQL
```bash
psql -p 5430 -U badraaji -d badraaji
```

### Check Data
```sql
-- Set schema
SET search_path TO tazama;

-- View rules
SELECT ruleid, configuration->>'desc' FROM rule;

-- View transactions
SELECT source, destination, amt FROM transaction LIMIT 10;

-- Count transactions
SELECT COUNT(*) FROM transaction;
```

### Backup Database
```bash
pg_dump -p 5430 -U badraaji -d badraaji > tazama_backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
psql -p 5430 -U badraaji -d badraaji < tazama_backup_YYYYMMDD.sql
```

---

## 📝 Testing

### Health Check
```bash
curl http://localhost:3001/health
```

### Send Test Transaction
```bash
curl -X POST http://localhost:3000/execute \
  -H "Content-Type: application/json" \
  -d @test-transaction.json
```

---

## 🐛 Troubleshooting

### Issue: PostgreSQL Connection Failed

**Solution:**
```bash
# Check PostgreSQL is running
ps aux | grep postgres | grep 5430

# Check connection
psql -p 5430 -U badraaji -d badraaji -c "SELECT version();"
```

### Issue: Docker Can't Connect to DB

**Solution:**
```bash
# Test from Docker container
docker run --rm -it postgres:17 psql -h host.docker.internal -p 5430 -U badraaji -d badraaji
```

### Issue: Rules Not Triggering

**Solution:**
```bash
# Check rule logs
docker logs tazama-local-db-rule-901-1 --tail 50

# Verify rules in DB
psql -p 5430 -U badraaji -d badraaji -c "SELECT COUNT(*) FROM tazama.rule;"
```

---

## 📂 Directory Structure

```
tazama-local-db/
├── .env                        # Environment configuration
├── docker-compose.yml          # Core services (TMS, TP, TADP, NATS, Valkey)
├── docker-compose.rules.yml    # Rules (006, 018, 901, 902)
├── start.sh                    # Startup script
└── README.md                   # This file
```

---

## 🔄 Updating Configuration

### Add More Rules

Edit `.env` to add more DATABASE_SCHEMA references if needed, then:

```bash
# Deploy with all 33 rules (requires more resources)
# Create docker-compose.all-rules.yml with all rule containers
```

### Change Database

Edit `.env`:
```bash
POSTGRES_PORT=5430  # Change port if needed
POSTGRES_USER=badraaji
POSTGRES_PASSWORD=badraaji
```

Then restart:
```bash
./start.sh
```

---

## 📈 Monitoring

### View Container Stats
```bash
docker stats
```

### Check Database Connections
```sql
SELECT pid, usename, application_name, state 
FROM pg_stat_activity 
WHERE datname = 'badraaji';
```

---

## 🛡️ Security Notes

- This setup is for **development/testing only**
- PostgreSQL uses **trust authentication** for localhost
- Credentials are stored in **plain text** in `.env`
- For production, use:
  - Encrypted passwords
  - SSL/TLS connections
  - Properly configured `pg_hba.conf`
  - Secret management (Vault, AWS Secrets Manager)

---

## 📚 Resources

- [Tazama Documentation](https://github.com/tazama-lf)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## 🆘 Support

For issues, check:
1. Docker logs: `docker-compose logs`
2. PostgreSQL logs: Check Postgres.app logs
3. Tazama GitHub: https://github.com/tazama-lf/Full-Stack-Docker-Tazama

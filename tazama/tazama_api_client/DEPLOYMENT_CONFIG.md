# Tazama API Client - Deployment Configuration Guide

## 🔧 Switching Between Tazama Deployments

Tazama API Client dapat connect ke 2 deployment berbeda. Edit `config.py` untuk switch.

---

## 📍 **OPTION 1: Full Docker Stack (Original)**

**Deployment:** `Full-Stack-Docker-Tazama`  
**Port:** 3000  
**PostgreSQL:** Dalam Docker container  
**Rules:** 4 rules (006, 018, 901, 902)

### Cara Aktifkan:

Edit `/Users/badraaji/Desktop/RND/tazama/tazama_api_client/config.py`:

```python
# OPTION 1: Full Docker Stack (Full-Stack-Docker-Tazama - Port 3000)
# Uncomment line below if using original full docker stack
TMS_BASE_URL = os.getenv("TMS_BASE_URL", "http://localhost:3000")  # ← UNCOMMENT

# OPTION 2: Local PostgreSQL (tazama-local-db - Port 3000)
# Uncomment line below if using tazama-local-db directory
# TMS_BASE_URL = os.getenv("TMS_BASE_URL", "http://localhost:3000")  # ← COMMENT
```

**Start Deployment:**
```bash
cd /Users/badraaji/Desktop/RND/tazama/Full-Stack-Docker-Tazama
docker-compose -f docker-compose.base.infrastructure.yaml \
               -f docker-compose.hub.core.yaml \
               -f docker-compose.hub.rules.yaml \
               up -d
```

---

## 📍 **OPTION 2: Local PostgreSQL (tazama-local-db)** ⭐ **RECOMMENDED**

**Deployment:** `tazama-local-db`  
**Port:** 3001 (to avoid conflict with Full Docker on 3000)  
**PostgreSQL:** Lokal Postgres.app (port 5430)  
**Database:** badraaji (schema: tazama)  
**Rules:** 33 rules lengkap!

### Cara Aktifkan:

Edit `/Users/badraaji/Desktop/RND/tazama/tazama_api_client/config.py`:

```python
# OPTION 1: Full Docker Stack (Full-Stack-Docker-Tazama - Port 3000)
# Uncomment line below if using original full docker stack
# TMS_BASE_URL = os.getenv("TMS_BASE_URL", "http://localhost:3000")  # ← COMMENT

# OPTION 2: Local PostgreSQL (tazama-local-db - Port 3001)
# Uncomment line below if using tazama-local-db directory
TMS_BASE_URL = os.getenv("TMS_BASE_URL", "http://localhost:3001")  # ← UNCOMMENT
```

**Start Deployment:**
```bash
cd /Users/badraaji/Desktop/RND/tazama/tazama-local-db
./start.sh
```

---

## 🚀 **Quick Comparison**

| Feature | Full Docker | Local PostgreSQL |
|---------|-------------|------------------|
| **Setup** | Complex | Simple |
| **PostgreSQL** | In Docker | Postgres.app (local) |
| **Rules** | 4 rules | 33 rules |
| **Data Persistence** | Lost on `docker down` | **Persists** in local DB |
| **Performance** | Good | **Better** (no DB in Docker) |
| **Debugging** | Docker logs only | **pgAdmin access** |
| **Recommended For** | Quick demo | **Development & Testing** |

---

## 🔄 **Full Workflow Example**

### **Using Local PostgreSQL (Current Setup):**

1. **Ensure PostgreSQL Running:**
   ```bash
   psql -p 5430 -d badraaji -c "SELECT COUNT(*) FROM tazama.rule;"
   # Should return: 33
   ```

2. **Start Tazama:**
   ```bash
   cd /Users/badraaji/Desktop/RND/tazama/tazama-local-db
   ./start.sh
   ```

3. **Start API Client:**
   ```bash
   cd /Users/badraaji/Desktop/RND/tazama/tazama_api_client
   source ../.venv/bin/activate
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access UI:**
   ```
   http://localhost:8000
   ```

5. **Test Transaction:**
   - Open UI
   - Fill form
   - Click "Send Transaction"
   - Check fraud alerts

6. **View Data in PostgreSQL:**
   ```bash
   psql -p 5430 -d badraaji
   SET search_path TO tazama;
   SELECT * FROM transaction ORDER BY credttm DESC LIMIT 10;
   ```

---

## 📝 **Environment Variable Override**

Anda juga bisa override via environment variable (tanpa edit `config.py`):

```bash
# Temporary override
export TMS_BASE_URL="http://localhost:3000"
python -m uvicorn main:app --reload
```

---

## 🐛 **Troubleshooting**

### Issue: Connection Refused

**Check TMS is running:**
```bash
curl http://localhost:3000/health
# Should return: 200 OK
```

**Check containers:**
```bash
docker ps | grep tazama
```

### Issue: Wrong Deployment Active

**Check which TMS_BASE_URL is active:**
```bash
cd /Users/badraaji/Desktop/RND/tazama/tazama_api_client
python -c "from config import TMS_BASE_URL; print(TMS_BASE_URL)"
```

Expected: `http://localhost:3000`

---

## ✅ **Current Configuration** (as of setup)

- ✅ **API Client** configured for `tazama-local-db`
- ✅ **PostgreSQL** port 5430 with 33 rules
- ✅ **TMS** endpoint: `http://localhost:3000`
- ✅ **Database** persists after Docker restart

Ready to go! 🎉

# Tazama API Test Client

Web-based interactive client untuk test Tazama Transaction Monitoring Service (TMS).

## 🎯 Fungsi

Tool ini memungkinkan Anda untuk:
- ✅ Check TMS service status (UP/DOWN)
- ✅ Send pacs.008 test transaction
- ✅ Send pacs.002 confirmation
- ✅ Run full transaction test (008 + 002)
- ✅ View test history
- ✅ Monitor response times

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd tazama_api_client
pip install -r requirements.txt
```

### 2. Start Application

```bash
python main.py
```

atau

```bash
uvicorn main:app --reload --port 8080
```

### 3. Open Browser

```
http://localhost:8080
```

## 📊 Features

### Health Check
- Real-time TMS status monitoring
- Response time measurement
- Auto-refresh capability

### Test pacs.008 (Transfer Request)
- Generate random or specific debtor account
- Custom transaction amount
- Auto-generated realistic ISO 20022 payload
- Full response display

### Test pacs.002 (Confirmation)
- Link to pacs.008 message ID
- Support ACCC, ACSC, RJCT status codes
- Automatic confirmation generation

### Full Transaction Test
- Automated pacs.008 + pacs.002 flow
- Single-click complete transaction
- Step-by-step result visualization

### Test History
- Track all sent transactions
- Success/failure indicators
- Response time logging
- Clear history option

## 🔧 Configuration

Edit `main.py` untuk mengubah TMS URL:

```python
TMS_BASE_URL = "http://localhost:5001"  # Change port if different
```

## 📝 API Endpoints

### Web UI
```
GET  /                   - Main dashboard
```

### REST API
```
GET  /api/health        - Check TMS status
POST /api/test/pacs008  - Test pacs.008
POST /api/test/pacs002  - Test pacs.002
POST /api/test/full-transaction - Full test
GET  /api/history       - Get test history
DELETE /api/history     - Clear history
```

## 🎨 Screenshots

### Main Dashboard
- Status indicator (online/offline)
- Three test panels
- Real-time response display
- Test history timeline

## 🧪 Usage Examples

### Example 1: Test Single Transaction
1. Open http://localhost:8080
2. Enter amount (e.g., 5000)
3. Click "Send pacs.008"
4. Copy Message ID from response
5. Paste to pacs.002 form
6. Click "Send pacs.002"

### Example 2: Quick Full Test
1. Enter amount
2. Click "Run Full Test"
3. View complete flow results

### Example 3: Velocity Attack Simulation
1. Enter fixed debtor account
2. Click "Run Full Test" multiple times
3. Same account will trigger velocity detection

## 🔍 Troubleshooting

### TMS Shows Offline
```bash
# Check if TMS is running
docker ps --filter "name=tazama-tms"

# Check TMS logs
docker logs tazama-tms-1

# Verify port
curl http://localhost:5001/
```

### Connection Refused
- Verify TMS_PORT in deployment (.env file)
- Check if port changed from 5000 to 5001
- Update TMS_BASE_URL in main.py

### No Response
- Check Postgres is healthy
- Verify all Tazama services running
- Wait 30s after deployment for initialization

## 💡 Tips

**For Testing Fraud Rules:**
- Use same debtor account multiple times (velocity)
- Vary amounts to test thresholds
- Mix successful (ACCC) and failed (RJCT) transactions

**For Performance Testing:**
- Monitor response times in history
- Run multiple full transactions
- Check database impact

## 🆚 vs Other Tools

| Feature | This Tool | Postman | Newman CLI |
|---------|-----------|---------|------------|
| Web UI | ✅ | ✅ | ❌ |
| Auto Payload Gen | ✅ | ❌ | ❌ |
| History Tracking | ✅ | ✅ | ❌ |
| One-Click Full Test | ✅ | ❌ | ❌ |
| Real-time Status | ✅ | ❌ | ❌ |
| Programming Required | ❌ | ❌ | ✅ |

## 📚 Related

- [Postman Collections](../postman/) - Official test collections
- [Mock Simulator](../tazama_fastapi_sim/) - Local mock TMS
- [Full Stack Deployment](../Full-Stack-Docker-Tazama/) - Real Tazama

---

**Made with ❤️ for Tazama Transaction Monitoring Testing**

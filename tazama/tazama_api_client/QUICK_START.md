# 🚀 Tazama API Test Client - Quick Start Guide

## ✅ **Sudah Dibuat untuk Anda:**

```
/Users/badraaji/Desktop/RND/tazama/tazama_api_client/
├── main.py                    ← FastAPI application
├── requirements.txt           ← Dependencies
├── start.sh                   ← Quick start script
├── README.md                  ← Full documentation
├── templates/
│   └── index.html            ← Web UI (beautiful!)
└── utils/
    ├── __init__.py
    └── payload_generator.py  ← ISO 20022 payload generator
```

## 🎯 **Apa Fungsinya?**

Web application untuk test Tazama TMS service secara interaktif dengan UI yang cantik!

**Features:**
- ✅ **Real-time TMS Status** - Check apakah service UP/DOWN
- ✅ **Test pacs.008** - Send transfer request
- ✅ **Test pacs.002** - Send confirmation
- ✅ **Full Transaction Test** - Auto send 008 + 002
- ✅ **Test History** - Track semua test dengan timestamp
- ✅ **Auto Payload Generation** - Random realistic data

## 🚀 **Cara Menggunakan:**

### Step 1: Start Application

```bash
cd /Users/badraaji/Desktop/RND/tazama/tazama_api_client
./start.sh
```

### Step 2: Open Browser

```
http://localhost:8090
```

### Step 3: Test!

**Option A: Quick Full Test**
1. Enter amount (e.g., 5000)
2. Click "🚀 Run Full Test"
3. Done! Lihat response

**Option B: Step by Step**
1. Test pacs.008 first
2. Copy Message ID dari response
3. Test pacs.002 dengan Message ID itu
4. See results

## 📸 **UI Preview:**

```
╔═══════════════════════════════════════════════════════════╗
║  🚀 Tazama API Test Client                                ║
║  Interactive testing tool for Tazama TMS                  ║
╠═══════════════════════════════════════════════════════════╣
║  ● Online | TMS Online - Response: 45.23ms    🔄 Refresh ║
╠═══════════════════════════════════════════════════════════╣
║  📤 Test pacs.008    📥 Test pacs.002    🔄 Full Test     ║
║  [Transfer Request]  [Confirmation]      [Both Auto]      ║
║                                                            ║
║  📊 Test History                           [Clear History]║
║  ✅ pacs.008 - 200 | 12:34:56 | 45ms                      ║
║  ✅ pacs.002 - 200 | 12:35:01 | 38ms                      ║
╚═══════════════════════════════════════════════════════════╝
```

## 🎨 **Use Cases:**

### 1. **Quick Health Check**
```
→ Open http://localhost:8090
→ Check status indicator (green = UP)
→ Click "Refresh Status"
```

### 2. **Single Transaction Test**
```
→ Enter amount: 5000
→ Click "Send pacs.008"
→ Check response (should be 200)
→ Copy Message ID
→ Paste to pacs.002 form
→ Click "Send pacs.002"
```

### 3. **Velocity Attack Simulation**
```
→ Enter fixed debtor account: GB123456789
→ Enter amount: 1000
→ Click "Run Full Test" → 10 times
→ Check history (same account, multiple transactions)
```

### 4. **Performance Testing**
```
→ Run multiple full tests
→ Check response times in history
→ Monitor TMS performance
```

## 🔧 **Configuration:**

Default TMS URL: `http://localhost:5001`

Jika port berbeda, edit `main.py`:
```python
TMS_BASE_URL = "http://localhost:5001"  # Change here
```

## 🆚 **vs Tools Lain:**

| Feature | API Client | Postman | tazama_fastapi_sim |
|---------|------------|---------|---------------------|
| Web UI | ✅ Modern | ✅ Desktop | ❌ None |
| Auto Payload | ✅ | ❌ Manual | ✅ |
| Real TMS | ✅ | ✅ | ❌ Mock only |
| History Track | ✅ Visual | ✅ | ❌ |
| One-Click | ✅ | ❌ Multiple steps | ✅ |
| Programming | ❌ None | ❌ None | ⚠️ Optional |

## 💡 **Tips:**

1. **Keep TMS Running** - Pastikan Tazama Docker stack aktif
2. **Check Port** - Default 5001 (bukan 5000)
3. **Use History** - Track performance trends
4. **Test Patterns** - Simulate different fraud scenarios

## 📚 **Documentation:**

Full docs: `/Users/badraaji/Desktop/RND/tazama/tazama_api_client/README.md`

---

## 🎉 **Ready to Test!**

```bash
cd tazama_api_client
./start.sh
```

Then open: **http://localhost:8090** 🚀

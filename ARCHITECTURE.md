# Tazama FDS - Fraud Detection System

## Arsitektur dan Dokumentasi Teknis Lengkap

Dokumentasi ini menjelaskan secara detail bagaimana Tazama FDS mendeteksi fraud, termasuk arsitektur microservices, alur data, konfigurasi rule, dan contoh kasus deteksi **Velocity Attack** (40 transaksi dalam waktu singkat).

---

## Daftar Isi

1. [Arsitektur Overview](#1-arsitektur-overview)
2. [Komponen Microservices](#2-komponen-microservices)
3. [Alur Deteksi Fraud Step-by-Step](#3-alur-deteksi-fraud-step-by-step)
4. [Contoh Kasus: Velocity Attack (40 Transaksi)](#4-contoh-kasus-velocity-attack-40-transaksi)
5. [Konfigurasi Rule dan Threshold](#5-konfigurasi-rule-dan-threshold)
6. [API Integration](#6-api-integration)
7. [Database Schema](#7-database-schema)
8. [Cara Menjalankan](#8-cara-menjalankan)

---

## 1. Arsitektur Overview

### 1.1. Diagram Arsitektur Lengkap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TAZAMA FDS ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                                                            │
│  │  External    │                                                            │
│  │  API Client  │ ─── POST /v1/evaluate/iso20022/pacs.008 ───┐              │
│  │  (Bank/App)  │                                             │              │
│  └──────────────┘                                             ▼              │
│                                                    ┌──────────────────┐      │
│                                                    │   TMS Service    │      │
│                                                    │   (Port 3000)    │      │
│                                                    │                  │      │
│                                                    │ • Validate       │      │
│                                                    │ • Cache          │      │
│                                                    │ • Store to DB    │      │
│                                                    └────────┬─────────┘      │
│                                                             │ NATS           │
│                                                             ▼                │
│                                                    ┌──────────────────┐      │
│                                                    │  Event Director  │      │
│                                                    │                  │      │
│                                                    │ • Read NetworkMap│      │
│                                                    │ • Route to Rules │      │
│                                                    └────────┬─────────┘      │
│                                                             │ NATS           │
│                              ┌──────────────────────────────┼───────────┐    │
│                              ▼              ▼               ▼           ▼    │
│                        ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│                        │ Rule 901 │  │ Rule 902 │  │ Rule 006 │  │ Rule 018 ││
│                        │ Debtor   │  │ Creditor │  │Structuring│ │HighValue ││
│                        │ Velocity │  │ Velocity │  │          │  │          ││
│                        └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘│
│                              │              │            │            │      │
│                              └──────────────┴─────┬──────┴────────────┘      │
│                                                   │ NATS                     │
│                                                   ▼                          │
│                                          ┌──────────────────┐                │
│                                          │    Typology      │                │
│                                          │    Processor     │                │
│                                          │                  │                │
│                                          │ • Aggregate      │                │
│                                          │ • Calculate Score│                │
│                                          └────────┬─────────┘                │
│                                                   │ NATS                     │
│                                                   ▼                          │
│                                          ┌──────────────────┐                │
│                                          │      TADP        │                │
│                                          │                  │                │
│                                          │ • Final Decision │                │
│                                          │ • Save Result    │                │
│                                          │ • Send Alert     │                │
│                                          └──────────────────┘                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           INFRASTRUCTURE                                 │ │
│  │  ┌──────────┐    ┌──────────────┐    ┌──────────┐                       │ │
│  │  │   NATS   │    │  PostgreSQL  │    │  Valkey  │                       │ │
│  │  │  :4222   │    │    :5433     │    │  :6380   │                       │ │
│  │  │ Message  │    │   Database   │    │  Cache   │                       │ │
│  │  │  Broker  │    │              │    │  (Redis) │                       │ │
│  │  └──────────┘    └──────────────┘    └──────────┘                       │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2. Sequence Diagram

```
┌──────┐     ┌─────┐     ┌────┐     ┌──────┐     ┌────┐     ┌──────┐
│Client│     │ TMS │     │ ED │     │Rules │     │ TP │     │ TADP │
└──┬───┘     └──┬──┘     └─┬──┘     └──┬───┘     └─┬──┘     └──┬───┘
   │            │          │           │           │           │
   │ POST pacs.008         │           │           │           │
   │──────────────────────>│           │           │           │
   │            │          │           │           │           │
   │            │ Save to DB           │           │           │
   │            │──────────>           │           │           │
   │            │          │           │           │           │
   │            │ NATS: event-director │           │           │
   │            │─────────────────────>│           │           │
   │            │          │           │           │           │
   │            │          │ Get NetworkMap        │           │
   │            │          │───────────>           │           │
   │            │          │           │           │           │
   │            │          │ NATS: sub-rule-901, 006, etc.     │
   │            │          │──────────────────────>│           │
   │            │          │           │           │           │
   │            │          │           │ Query Historical      │
   │            │          │           │───────────>           │
   │            │          │           │           │           │
   │            │          │           │ Calculate Score       │
   │            │          │           │───────────>           │
   │            │          │           │           │           │
   │            │          │           │ NATS: typology-processor
   │            │          │           │──────────────────────>│
   │            │          │           │           │           │
   │            │          │           │           │ Aggregate │
   │            │          │           │           │───────────>
   │            │          │           │           │           │
   │            │          │           │           │ NATS: tadp│
   │            │          │           │           │──────────>│
   │            │          │           │           │           │
   │            │          │           │           │    Save   │
   │            │          │           │           │    Result │
   │            │          │           │           │    ───────>
   │            │          │           │           │           │
   │<──────────────────────────────────────────────────────────│
   │            200 OK + Alert Status                          │
   │            │          │           │           │           │
```

---

## 2. Komponen Microservices

### 2.1. TMS Service (Transaction Monitoring Service)

**Fungsi:** Entry point untuk semua transaksi. Validasi, cache, dan forward ke Event Director.

| File | Line | Fungsi |
|------|------|--------|
| [`src/router.ts`](services/tms-service/src/router.ts) | 33-39 | Route POST `/v1/evaluate/iso20022/pacs.008` |
| [`src/app.controller.ts`](services/tms-service/src/app.controller.ts) | 69-86 | `Pacs008Handler` - Handle request |
| [`src/logic.service.ts`](services/tms-service/src/logic.service.ts) | 287-382 | `handlePacs008` - Process & forward |
| [`src/logic.service.ts`](services/tms-service/src/logic.service.ts) | 28-37 | `notifyEventDirector` - NATS publish |

**Kode Kunci:**
```typescript
// src/logic.service.ts:378-380
notifyEventDirector(transaction, dataCache, startTime);
loggerService.log('Transaction send to event-director service', logContext, id);
```

---

### 2.2. Event Director

**Fungsi:** Membaca Network Map dan routing transaksi ke rule processors yang sesuai.

| File | Line | Fungsi |
|------|------|--------|
| [`src/index.ts`](services/event-director/src/index.ts) | 28 | NATS subscribe ke `handleTransaction` |
| [`src/services/logic.service.ts`](services/event-director/src/services/logic.service.ts) | 35-53 | `getRuleMap` - Extract rules from NetworkMap |
| [`src/services/logic.service.ts`](services/event-director/src/services/logic.service.ts) | 66-152 | `handleTransaction` - Main routing logic |
| [`src/services/logic.service.ts`](services/event-director/src/services/logic.service.ts) | 154-175 | `sendRuleToRuleProcessor` - NATS publish |

**Kode Kunci:**
```typescript
// src/services/logic.service.ts:132-140
const rules = getRuleMap(networkMap, parsedRequest.transaction.TxTp);
for (const rule of rules) {
  promises.push(sendRuleToRuleProcessor(rule, networkSubMap, ...));
}
await Promise.all(promises);
```

---

### 2.3. Rule Processor (Rule Executer)

**Fungsi:** Menjalankan logika deteksi fraud spesifik (Velocity, Structuring, dll).

| File | Line | Fungsi |
|------|------|--------|
| [`src/index.ts`](services/rule-executer/src/index.ts) | 33-38 | NATS subscribe ke `sub-rule-{id}` |
| [`src/controllers/execute.ts`](services/rule-executer/src/controllers/execute.ts) | 19-157 | `execute` - Main execution logic |
| [`src/controllers/execute.ts`](services/rule-executer/src/controllers/execute.ts) | 115 | Call rule-specific `handleTransaction` |
| [`src/controllers/execute.ts`](services/rule-executer/src/controllers/execute.ts) | 146-149 | Send result to Typology Processor |

**Kode Kunci:**
```typescript
// src/controllers/execute.ts:115
ruleRes = await handleTransaction(normalizedRequest, determineOutcome, ruleRes, ...);

// src/controllers/execute.ts:146-149
await server.handleResponse({
  ...request,
  ruleResult: ruleRes,
});
```

---

### 2.4. Typology Processor

**Fungsi:** Mengumpulkan hasil semua rules dan menghitung skor weighted.

| File | Line | Fungsi |
|------|------|--------|
| [`src/logic.service.ts`](services/typology-processor/src/logic.service.ts) | 172-243 | `handleTransaction` - Main aggregation |
| [`src/logic.service.ts`](services/typology-processor/src/logic.service.ts) | 22-53 | `ruleResultAggregation` - Collect results |
| [`src/logic.service.ts`](services/typology-processor/src/logic.service.ts) | 55-170 | `evaluateTypologySendRequest` - Scoring |
| [`src/utils/evaluateTExpression.ts`](services/typology-processor/src/utils/evaluateTExpression.ts) | - | Expression evaluation |

**Kode Kunci:**
```typescript
// src/logic.service.ts:84
const typologyResultValue = evaluateTypologyExpression(
  expression.rules, 
  currTypologyResult.ruleResults, 
  expression.expression
);

// src/logic.service.ts:95-102
if (typologyResultValue >= currTypologyResult.workflow.alertThreshold) {
  currTypologyResult.review = true; // Mark for ALERT
}
```

---

### 2.5. TADP (Transaction Aggregation & Decisioning Processor)

**Fungsi:** Keputusan final (ALRT/NALT), simpan hasil, kirim alert.

| File | Line | Fungsi |
|------|------|--------|
| [`src/services/logic.service.ts`](services/transaction-aggregation-decisioning-processor/src/services/logic.service.ts) | 14-89 | `handleExecute` - Final decision |
| [`src/services/logic.service.ts`](services/transaction-aggregation-decisioning-processor/src/services/logic.service.ts) | 57-63 | Create Alert object |
| [`src/services/logic.service.ts`](services/transaction-aggregation-decisioning-processor/src/services/logic.service.ts) | 66 | Save to database |
| [`src/services/logic.service.ts`](services/transaction-aggregation-decisioning-processor/src/services/logic.service.ts) | 78 | Send alert to CMS |

**Kode Kunci:**
```typescript
// src/services/logic.service.ts:57-63
const alert: Alert = {
  evaluationID: v7(),
  tadpResult,
  status: review ? 'ALRT' : 'NALT',  // <-- FINAL DECISION
  metaData,
  timestamp: new Date().toISOString(),
};

// src/services/logic.service.ts:66
await databaseManager.saveEvaluationResult(transactionID, transaction, networkMap, alert, dataCache);
```

---

## 3. Alur Deteksi Fraud Step-by-Step

### Step 1: API Client Mengirim Transaksi

```bash
POST http://localhost:3000/v1/evaluate/iso20022/pacs.008.001.10
Content-Type: application/json
SourceTenantId: DEFAULT

{
  "TxTp": "pacs.008.001.10",
  "TenantId": "DEFAULT",
  "FIToFICstmrCdtTrf": {
    "GrpHdr": {
      "MsgId": "uuid-12345",
      "CreDtTm": "2025-12-17T10:00:00.000Z"
    },
    "CdtTrfTxInf": {
      "InstdAmt": { "Amt": { "Amt": 5000000, "Ccy": "IDR" } },
      "Dbtr": { "Nm": "John Doe", ... },
      "DbtrAcct": { "Id": { "Othr": [{ "Id": "1234567890" }] } },
      "Cdtr": { "Nm": "Jane Smith", ... },
      "CdtrAcct": { "Id": { "Othr": [{ "Id": "0987654321" }] } }
    }
  }
}
```

### Step 2: TMS Menerima dan Forward

```
[TMS] Receive POST /v1/evaluate/iso20022/pacs.008
      ↓
[TMS] Validate payload structure
      ↓
[TMS] Save to PostgreSQL (transaction_history, transaction_details)
      ↓
[TMS] Cache to Valkey (Redis)
      ↓
[TMS] NATS Publish → "event-director" subject
```

### Step 3: Event Director Routing

```
[ED] NATS Subscribe ← "event-director"
     ↓
[ED] Parse transaction, extract TenantId & TxTp
     ↓
[ED] Query NetworkMap from cache/DB
     ↓
[ED] Match txTp="pacs.008.001.10" → Rules: [901, 902, 006, 018, EFRuP]
     ↓
[ED] NATS Publish (parallel):
     ├── "sub-rule-901@1.0.0"
     ├── "sub-rule-902@1.0.0"
     ├── "sub-rule-006@1.0.0"
     ├── "sub-rule-018@1.0.0"
     └── "sub-rule-EFRuP@1.0.0"
```

### Step 4: Rule Processors Execute

```
[Rule 901 - Velocity]
     ↓
Query: SELECT COUNT(*) FROM transactions 
       WHERE debtor_id = 'xxx' 
       AND timestamp > NOW() - INTERVAL '24 hours'
     ↓
If count >= threshold → subRuleRef = ".02" (ALERT)
Else → subRuleRef = ".01" (OK)
     ↓
NATS Publish → "typology-processor"
```

### Step 5: Typology Processor Scoring

```
[TP] Receive rule results from Redis cache
     ↓
[TP] Wait until all rules complete
     ↓
[TP] Calculate: Score = Σ(RuleScore × Weight)
     ↓
[TP] Compare Score vs Threshold
     ↓
If Score >= AlertThreshold → review = true
     ↓
NATS Publish → "tadp"
```

### Step 6: TADP Final Decision

```
[TADP] Receive typologyResult
       ↓
[TADP] If review == true → status = "ALRT"
       Else → status = "NALT"
       ↓
[TADP] Save to PostgreSQL (evaluation table)
       ↓
[TADP] NATS Publish → "cms-alert" (Dashboard notification)
```

---

## 4. Contoh Kasus: Velocity Attack (40 Transaksi)

### Skenario
Attacker mengirim **40 transaksi** dari akun yang sama dalam waktu **5 menit** untuk mencuci uang.

### Timeline Deteksi

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    VELOCITY ATTACK DETECTION TIMELINE                       │
├──────────┬─────┬─────────────────────────────────────────────────┬─────────┤
│   Time   │ Tx# │ Rule 901 Check                                  │ Result  │
├──────────┼─────┼─────────────────────────────────────────────────┼─────────┤
│ 10:00:00 │  1  │ Query: COUNT=1 (threshold=3)                    │ ✅ NALT │
│ 10:00:05 │  2  │ Query: COUNT=2 (threshold=3)                    │ ✅ NALT │
│ 10:00:10 │  3  │ Query: COUNT=3 (threshold=3) ⚠️ THRESHOLD MET   │ 🚨 ALRT │
│ 10:00:15 │  4  │ Query: COUNT=4 (threshold=3)                    │ 🚨 ALRT │
│ 10:00:20 │  5  │ Query: COUNT=5 (threshold=3)                    │ 🚨 ALRT │
│   ...    │ ... │ ...                                             │ 🚨 ALRT │
│ 10:05:00 │ 40  │ Query: COUNT=40 (threshold=3)                   │ 🚨 ALRT │
└──────────┴─────┴─────────────────────────────────────────────────┴─────────┘
```

### Hasil di Database

```sql
SELECT tx_id, status, rule_901_score, total_score, created_at
FROM evaluation_results
WHERE debtor_id = 'attacker-123'
ORDER BY created_at;

┌─────────────┬────────┬────────────────┬─────────────┬─────────────────────┐
│   tx_id     │ status │ rule_901_score │ total_score │     created_at      │
├─────────────┼────────┼────────────────┼─────────────┼─────────────────────┤
│ tx-001      │ NALT   │ 0              │ 0           │ 2025-12-17 10:00:00 │
│ tx-002      │ NALT   │ 0              │ 0           │ 2025-12-17 10:00:05 │
│ tx-003      │ ALRT   │ 100            │ 50          │ 2025-12-17 10:00:10 │
│ tx-004      │ ALRT   │ 100            │ 50          │ 2025-12-17 10:00:15 │
│ ...         │ ALRT   │ 100            │ 50          │ ...                 │
│ tx-040      │ ALRT   │ 100            │ 50          │ 2025-12-17 10:05:00 │
└─────────────┴────────┴────────────────┴─────────────┴─────────────────────┘

-- Total: 38 ALRT, 2 NALT
```

### Kode yang Bekerja

**1. Rule 901 Query Historical (Pseudocode):**
```typescript
// Dalam rule-901 library (tidak tersedia di repo, ini pseudocode)
const historicalCount = await db.query(`
  SELECT COUNT(*) 
  FROM transaction_details 
  WHERE source = $1 
  AND "CreDtTm" > NOW() - INTERVAL '${maxQueryRange} milliseconds'
`, [debtorAccountId]);

if (historicalCount >= threshold) {
  return { subRuleRef: ".02", reason: "High velocity detected" };
}
```

**2. Typology Scoring:**
```typescript
// services/typology-processor/src/logic.service.ts:84
const typologyResultValue = evaluateTypologyExpression(
  expression.rules,           // [{id: "901", weight: 0.5}, ...]
  currTypologyResult.ruleResults,  // [{id: "901", score: 100}, ...]
  expression.expression       // "(901 * 0.5) + (006 * 0.3) + ..."
);
// Result: 100 * 0.5 = 50
```

**3. TADP Decision:**
```typescript
// services/tadp/src/services/logic.service.ts:60
const alert: Alert = {
  status: review ? 'ALRT' : 'NALT',  // review=true karena score>=threshold
  // ...
};
```

---

## 5. Konfigurasi Rule dan Threshold

### 5.1. Network Map Configuration

**File:** [`init-db/05-setup-extra-rules.sql`](init-db/05-setup-extra-rules.sql) (Line 426-502)

```json
{
  "active": true,
  "tenantId": "DEFAULT",
  "messages": [
    {
      "txTp": "pacs.008.001.10",
      "typologies": [{
        "rules": [
          { "id": "EFRuP@1.0.0", "cfg": "none" },
          { "id": "901@1.0.0", "cfg": "1.0.0" },
          { "id": "902@1.0.0", "cfg": "1.0.0" },
          { "id": "006@1.0.0", "cfg": "1.0.0" },
          { "id": "018@1.0.0", "cfg": "1.0.0" }
        ]
      }]
    }
  ]
}
```

### 5.2. Rule 006 - Structuring Detection

**File:** [`init-db/05-setup-extra-rules.sql`](init-db/05-setup-extra-rules.sql) (Line 155-190)

| Parameter | Value | Keterangan |
|-----------|-------|------------|
| `maxQueryLimit` | 5 | Periksa 5 transaksi terakhir |
| `tolerance` | 0.2 | Toleransi 20% untuk "mirip" |
| `bands.lowerLimit` | 5 | Alert jika ≥ 5 transaksi mirip |

### 5.3. Rule 018 - High Value Detection

**File:** [`init-db/05-setup-extra-rules.sql`](init-db/05-setup-extra-rules.sql) (Line 362-395)

| Parameter | Value | Keterangan |
|-----------|-------|------------|
| `maxQueryRange` | 2592000000 | 30 hari (milliseconds) |
| `bands.lowerLimit` | 1.5 | Alert jika ≥ 1.5x rata-rata historical |

### 5.4. Cara Mengubah Threshold

```bash
# Edit init-db/05-setup-extra-rules.sql
# Ubah parameter yang diinginkan
# Lalu jalankan:

psql -U postgres -d configuration -f init-db/05-setup-extra-rules.sql
docker restart tazama-rule-006 tazama-rule-018 tazama-rule-901
```

---

## 6. API Integration

### 6.1. Payload Generator

**File:** [`tazama-api-client/tazama_api_client/utils/payload_generator.py`](tazama-api-client/tazama_api_client/utils/payload_generator.py)

| Function | Line | Purpose |
|----------|------|---------|
| `generate_pacs008()` | 507-734 | Generate credit transfer |
| `generate_pacs002()` | 737-799 | Generate confirmation |
| `generate_pain001()` | 16-263 | Generate payment initiation |

### 6.2. TMS Client

**File:** [`tazama-api-client/tazama_api_client/services/tms_client.py`](tazama-api-client/tazama_api_client/services/tms_client.py)

| Method | Line | Purpose |
|--------|------|---------|
| `send_pacs008()` | 46-67 | Send credit transfer |
| `send_pacs002()` | 69-90 | Send confirmation |
| `send_transaction()` | 138-170 | Auto-detect and send |

---

## 7. Database Schema

### 7.1. PostgreSQL Databases

| Database | Purpose |
|----------|---------|
| `configuration` | NetworkMap, Rule Config, Typology Config |
| `evaluation` | Hasil evaluasi fraud |
| `raw_history` | Raw transaction messages |
| `event_history` | Event processing history |

### 7.2. Key Tables

**File:** [`init-db/02-base-schema.sql`](init-db/02-base-schema.sql)

```sql
-- configuration.network_map
CREATE TABLE network_map (
  id SERIAL PRIMARY KEY,
  configuration JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- configuration.rule
CREATE TABLE rule (
  id SERIAL PRIMARY KEY,
  ruleid VARCHAR(50),
  tenantid VARCHAR(50),
  configuration JSONB NOT NULL
);
```

---

## 8. Cara Menjalankan

### 8.1. Prerequisites

- Docker & Docker Compose
- Git

### 8.2. Quick Start

```bash
# Clone repository
git clone <repo-url>
cd tazama-fds

# Start all services
docker-compose up -d

# Verify services
docker ps

# Check TMS health
curl http://localhost:3000/health
```

### 8.3. Test Fraud Detection

```bash
# Start API Client
cd tazama-api-client
./start.sh

# Open browser
open http://localhost:8091

# Simulate Velocity Attack
# → Click "Velocity Attack" button
# → Send 10+ transactions
# → Check "Fraud Alerts" section
```

---

## References

- [Tazama Official Documentation](https://tazama.org)
- [ISO 20022 Message Definitions](https://www.iso20022.org)
- [NATS Messaging](https://nats.io)

---

*Last Updated: December 17, 2025*

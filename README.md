```
External Client
       │
       ▼
┌───────────────────┐
│   TMS (port 3000) │ ◄── Entry Point (ISO20022 messages)
└───────────────────┘
       │ NATS
       ▼
┌──────────────────┐
│  Event Director  │ ◄── Routes to rules based on Network Map
└──────────────────┘
       │ NATS
       ▼
┌──────────────────────────────────────┐
│      Rule Processors (parallel)      │
│  ┌─────────────┐  ┌─────────────┐    │
│  │ rule-901    │  │ event-flow  │    │
│  │ (executer)  │  │  (EFRuP)    │    │
│  └─────────────┘  └─────────────┘    │
└──────────────────────────────────────┘
       │ NATS
       ▼
┌──────────────────────┐
│  Typology Processor  │ ◄── Calculates scores, checks thresholds
└──────────────────────┘
       │ NATS                │
       ▼                     ▼ (if interdiction threshold breached)
┌──────────────────┐   ┌────────────────────┐
│      TADP        │   │ Interdiction Svc   │
└──────────────────┘   └────────────────────┘
       │ NATS                     │
       ▼                          ▼
┌──────────────────┐   ┌────────────────────┐
│  Relay Service   │   │   Relay Service    │  ◄── OPTIONAL (if external)
│   (optional)     │   │    (optional)      │
└──────────────────┘   └────────────────────┘
       │                          │
       ▼                          ▼
   External CMS            External System
```

---

### Quick Start

All services have been cloned and infrastructure is ready. See **[QUICKSTART.md](QUICKSTART.md)** for immediate next steps.

**Infrastructure Running:**
- ✅ NATS (Message Broker) - http://localhost:8222
- ✅ PostgreSQL (Database) - localhost:5433  
- ✅ Valkey (Cache) - localhost:6380

---

## Core Service Files  
admin-service: Administration API (port 3100) 
tms: Transaction Monitoring Service API (port 3000) 
ed: Event Director rule-901: Rule 901 processor (built from rule-executer) 
tp: Typology Processor 
tadp: Transaction Aggregation and Decisioning Processor 
ef: Event Flow rule processor 

------ Verify this: 
https://github.com/tazama-lf/admin-service 
https://github.com/tazama-lf/tms-service 
https://github.com/tazama-lf/event-director 
https://github.com/tazama-lf/rule-executer 
https://github.com/tazama-lf/typology-processor 
https://github.com/tazama-lf/transaction-aggregation-decisioning-processor 
https://github.com/tazama-lf/event-flow  
https://github.com/tazama-lf/relay-service 



1. admin-service
URL: https://github.com/tazama-lf/admin-service
Port: 3100 (as you mentioned)
Purpose: Administration API for managing configurations, reports, and event flow control conditions.
Key Functions: 
Get reports by message ID from PostgreSQL
Manage event flow control conditions for entities and accounts (block/override transactions)
CRUD operations for Network Map, Rule Config, and Typology Config
JWT-based authentication with capability-based permissions


2. tms-service (TMS)
URL: https://github.com/tazama-lf/tms-service
Port: 3000 (as you mentioned)
Purpose: Transaction Monitoring Service - the entry point for all transactions.
Key Functions:
Accepts ISO20022 messages (pain.001, pain.013, pacs.008, pacs.002)
Validates incoming transactions
Stores transaction data in PostgreSQL
Caches data in Valkey (Redis)
Sends messages to Event Director via NATS. 

Flow: External Client → TMS → Event Director

3. event-director (ED)
URL: https://github.com/tazama-lf/event-director
Purpose: Routes transactions to rules for processing based on the Network Map.
Key Functions:
Fetches active Network Map (from cache or database)
Filters Network Map for relevant message types
Deduplicates rules across typologies
Dispatches messages to Rule Processors via NATS

Flow: TMS → Event Director → Rule Processors (rule-901, event-flow, etc.)

4. rule-executer
URL: https://github.com/tazama-lf/rule-executer
Purpose: Generic rule execution framework - this is a template/executor, not a specific rule.
Key Functions: 
Receives messages from Event Director
Loads specific rule logic as a library (e.g., rule-901)
Executes rule logic and produces RuleResult
Sends results to Typology Processor

Note: "rule-901" is built FROM rule-executer by installing a rule library (like @tazama-lf/rule-901)
Flow: Event Director → Rule Executer (with rule-901 library) → Typology Processor

5. typology-processor (TP)
URL: https://github.com/tazama-lf/typology-processor
Purpose: Calculates typology scores based on rule results.
Key Functions:
Aggregates all rule results for a typology
Calculates weighted typology score using configured expressions
Checks alert and interdiction thresholds
Can trigger interdiction (if threshold breached)
Sends results to TADP

Flow: Rule Processors → Typology Processor → TADP (and optionally Interdiction Service)

6. transaction-aggregation-decisioning-processor (TADP)
URL: https://github.com/tazama-lf/transaction-aggregation-decisioning-processor
Purpose: Final aggregation and decision-making for transactions.
Key Functions:
Receives typology results
Aggregates all typologies for a transaction
Creates final evaluation report
Stores evaluation results in PostgreSQL
Can send alerts to CMS (Case Management System) via NATS

Flow: Typology Processor → TADP → (optionally) CMS/Alert Service

7. event-flow (ef / EFRuP)
URL: https://github.com/tazama-lf/event-flow
Purpose: Specialized rule processor for event flow control (blocking/overriding transactions based on conditions).
Key Functions:
Receives messages from Event Director (like regular rules)
Checks conditions set via admin-service (entity/account blocks/overrides)
Returns special rule results: "block", "override", or "none"
Part of every typology to enable dynamic transaction control

Flow: Event Director → Event Flow → Typology Processor

8. relay-service
URL: https://github.com/tazama-lf/relay-service
Purpose: Bridge/adapter service for forwarding NATS messages to external systems.
Key Functions:
Monitors NATS subjects
Relays messages to external destinations:
- REST API
- RabbitMQ
- Kafka
- Another NATS server



Plugin-based architecture for extensibility
Supports JSON and Protobuf message formats




So when building from source, we don't have the nats-relay-plugin package (because it's private). But we actually CAN build from source if we manually install the plugin first!

Let me show you:


npm list @tazama-lf/nats-relay-plugin 2>&1
message-relay-service@3.0.0 /Users/62509/Documents/BNI/solar/fraud/start/service
s/relay-service                                                                 
└── (empty)                                                                     
Right! So here's what's happening:

The REAL Answer:
Pre-built Docker Image (tazamaorg/relay-service-integration-nats:3.0.0):


Copy the plugin from the Docker image:
# Extract plugin from running container
cd /Users/62509/Documents/BNI/solar/fraud/start && mkdir -p services/relay-service/node_modules/@tazama-lf && docker cp tazama-relay-service:/app/node_modules/@tazama-lf/nats-relay-plugin services/relay-service/node_modules/@tazama-lf/ && ls -la services/relay-service/node_modules/@tazama-lf/

docker run --rm tazamaorg/relay-service-integration-nats:3.0.0 \
  tar -czf - -C /app/node_modules/@tazama-lf nats-relay-plugin | \
  tar -xzf - -C services/relay-service/node_modules/@tazama-lf/



Step 2: Update .dockerignore to allow the plugin:
node_modules
!node_modules/@tazama-lf/nats-relay-plugin



Then rebuild your local image:
docker-compose build relay-service
docker-compose up -d relay-service



```
┌─────────────────────────────────────────────────────────────────┐
│                        TAZAMA PLATFORM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐   │
│  │     TMS      │ ───▶ │    Event     │ ───▶ │   Rule       │   │
│  │  (Gateway)   │      │   Director   │      │  Executors   │   │
│  └──────────────┘      └──────────────┘      └──────────────┘   │
│         │                     │                      │          │
│         │                     │                      ▼          │
│         │                     │              ┌──────────────┐   │
│         │                     │              │  Rule 903    │   │
│         │                     │              │  Rule 901    │   │
│         │                     │              │  Rule 902    │   │
│         │                     │              └──────────────┘   │
│         │                     │                      │          │
│         │                     ▼                      ▼          │
│         │              ┌──────────────┐      ┌──────────────┐   │
│         │              │  Typology    │ ◀─── │     NATS     │   │
│         │              │  Processor   │      │  (Message    │   │
│         │              └──────────────┘      │   Bus)       │   │
│         │                     │              └──────────────┘   │
│         │                     ▼                                 │
│         │              ┌──────────────┐                         │
│         └────────────▶ │   Database   │ ◀──────────────────     │
│                        │  PostgreSQL  │                         │
│                        └──────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```


### Rules Deployed
- Rule 006 (Structuring)
- Rule 018 (High Value Transfer)
- Rule 901 (Debtor Velocity)
- Rule 902 (Creditor Velocity)

```
1. Transaction masuk → TMS Service (port 3000)
   └─ POST /v1/evaluate/iso20022/pacs.008.001.10

2. TMS → NATS → Event Director
   └─ Event Director baca network_map dari database
   └─ Tentukan rule mana yang harus jalan

3. Event Director → NATS → Rule Processors (parallel)
   ├─ rule-901 (Debtor Velocity)
   ├─ rule-006 (Structuring) 
   ├─ rule-018 (High Value)
   └─ rule-902 (Creditor Velocity)
   
4. Setiap Rule → kirim hasil ke Typology Processor via NATS
   └─ Typology mengumpulkan hasil dari semua rules
   └─ Hitung score berdasarkan threshold

5. Typology → TADP (Transaction Aggregation and Decisioning)
   └─ Final decision: ALERT atau PASS

6. TADP → Relay Service → External System
   └─ Kirim notifikasi jika fraud detected

7. Hasil disimpan di evaluation database
```


Opsi 1: Build Custom Rule Service (Recommended)
Setiap rule adalah microservice terpisah yang:

Subscribe ke NATS subject (contoh: rule-903@1.0.0)
Terima transaction data dari Event Director
Jalankan logic fraud detection
Kirim hasil (score 0-100) ke Typology Processor


Contoh struktur rule baru:
// rule-903 - Unusual Time Pattern
class Rule903Processor {
  async evaluate(transaction) {
    // Logic: Transaksi jam 2-4 pagi = suspicious
    const hour = new Date(transaction.CreDtTm).getHours();
    
    if (hour >= 2 && hour <= 4) {
      return { 
        score: 75,  // High suspicion
        reason: "Transaction at unusual hour"
      };
    }
    return { score: 0 };
  }
}

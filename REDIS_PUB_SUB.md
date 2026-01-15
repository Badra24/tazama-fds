# Redis Pub/Sub for Hot Reload in Tazama FDS

This document explains the Redis Pub/Sub mechanism used for configuration hot reloading in Tazama FDS, including the **architectural reasoning** behind why each service subscribes to the reload channel.

---

## Overview

The Tazama Fraud Detection System (FDS) uses **Redis Pub/Sub** to enable **zero-downtime configuration updates**. When an administrator changes a rule, typology, or network map via the Admin UI, all affected services receive a signal to reload their configurations **without requiring a restart**.

---

## Architecture Context: How Rules are Activated/Deactivated

### Network Map as the Source of Truth

In Tazama, **rule activation is controlled by the Network Map**, not by a `disabled` field in the rule configuration.

- The `network_map` table contains a JSON structure that defines which Rules feed into which Typologies.
- When a rule is **disabled**, it is **removed** from the Network Map's `messages[].typologies[].rules[]` array.
- When a rule is **enabled**, it is **added back** to the array.

```
Network Map Structure:
{
  "messages": [
    {
      "typologies": [
        {
          "id": "typology-processor@1.0.0",
          "cfg": "1.0.0",
          "rules": [
            { "id": "901@1.0.0", "cfg": "1.0.0" },  // Active
            { "id": "902@1.0.0", "cfg": "1.0.0" }   // Active
            // Rule 903 is DISABLED (not in this array)
          ]
        }
      ]
    }
  ]
}
```

This design means:
1. `event-director` must reload to know which rules to route transactions to.
2. `typology-processor` must reload to know which rules it should expect results from.
3. `rule-executer` aligns with the architecture even though it fetches config per-transaction.

---

## Why Redis Pub/Sub?

### The Problem Without Hot Reload

Without a hot reload mechanism:
1. **Configuration Staleness**: Services cache configurations in memory for performance. Changes in the database are not reflected until restart.
2. **Manual Restarts Required**: Every configuration change requires `docker restart` for affected containers.
3. **Downtime Risk**: In a 24/7 fraud detection system, even brief downtime can allow fraudulent transactions to pass unchecked.
4. **Operational Overhead**: Teams must coordinate restarts, increasing deployment complexity.

### The Solution: Redis Pub/Sub

Redis Pub/Sub provides:
- **Instant Notification**: Changes propagate in milliseconds.
- **Decoupled Architecture**: Services don't need direct connections to each other.
- **Scalability**: Multiple instances of the same service all receive the signal.
- **Simplicity**: No complex orchestration or service mesh required.

---

## Services That Subscribe

### 1. `event-director`

**Role**: Routes incoming transactions to the appropriate rules based on the Network Map.

**Why It Needs Hot Reload**:
- Caches the Network Map to quickly determine which rules apply to each transaction.
- Without hot reload, disabled rules would still receive transactions until restart.
- **Critical for rule enable/disable** - this is the entry point that decides which rules get called.

**Reload Action**:
```
[Hot-Reload] Received reload signal
[Hot-Reload] Network configurations reloaded successfully
```

---

### 2. `typology-processor`

**Role**: Aggregates results from multiple rules to calculate a typology score.

**Why It Needs Hot Reload**:
- Caches typology configurations including which rules contribute to each typology.
- If a rule is disabled, the typology must stop waiting for results from that rule.
- Without hot reload, typologies might timeout waiting for results from disabled rules.

**Reload Action**:
```
[Hot-Reload] Received reload signal
[Hot-Reload] Typology configurations reloaded successfully
```

---

### 3. `rule-executer` (rule-901, rule-902, rule-903, etc.)

**Role**: Executes individual fraud detection rules on transactions.

**Why It Needs Hot Reload**:
- While rule-executers fetch parameters per-transaction, they may cache certain configurations.
- Aligns with the architectural pattern - all processors should respond to control plane signals.
- Future-proofs for scenarios where rule-level caching is introduced.
- Enables logging/monitoring of configuration changes across all services.

**Reload Action**:
```
[Hot-Reload] Received reload signal
// (Future: Could clear local caches or refresh rule parameters)
```

---

## Technical Implementation

### Publisher: `admin-service`

The Admin Service publishes to Redis when any configuration is created, updated, or deleted.

**Location**: `admin-service/src/services/redis.service.ts`

```typescript
export async function publishConfigReload(): Promise<void> {
  const redis = new Redis({ host: REDIS_HOST, port: REDIS_PORT });
  await redis.publish('config:reload', `Configuration updated at ${new Date().toISOString()}`);
  await redis.quit();
}
```

### Subscribers: All Processors

Each processor subscribes during startup:

```typescript
function subscribeToConfigReload(): void {
  const Redis = require('ioredis');
  const subscriber = new Redis({ host: redisHost, port: redisPort });

  subscriber.subscribe('config:reload', (err) => {
    if (err) { /* handle error */ }
    console.log('[Hot-Reload] Subscribed to config:reload channel');
  });

  subscriber.on('message', async (channel, message) => {
    if (channel === 'config:reload') {
      console.log(`[Hot-Reload] Received reload signal: ${message}`);
      await reloadConfigurations(); // Service-specific reload logic
    }
  });
}
```

---

## Workflow

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Admin UI   │──────▶│  Admin Service  │──────▶│     Redis       │
│             │ HTTP  │  (Publisher)    │ PUB   │   Pub/Sub       │
└─────────────┘       └─────────────────┘       └────────┬────────┘
                                                         │ NOTIFY
           ┌─────────────────────────────────────────────┼─────────────────────────────────┐
           │                                             │                                 │
           ▼                                             ▼                                 ▼
┌─────────────────┐                      ┌───────────────────────┐           ┌─────────────────┐
│ event-director  │                      │ typology-processor    │           │ rule-executer   │
│ (Subscriber)    │                      │ (Subscriber)          │           │ (Subscriber)    │
│                 │                      │                       │           │                 │
│ Reloads:        │                      │ Reloads:              │           │ Reloads:        │
│ - Network Map   │                      │ - Typology Configs    │           │ - (Future)      │
└─────────────────┘                      └───────────────────────┘           └─────────────────┘
```

---

## Analogi Grup Chat (Simplified Explanation)

Bayangkan sistem ini seperti **Grup WhatsApp "Info Update FDS"**:

1. **Redis Pub/Sub** = Grup Chat
2. **Admin Service** = Admin yang kirim pesan
3. **Processors** = Anggota grup

**Alurnya:**
1. Semua processor **join grup** saat startup (Subscribe).
2. User mengubah aturan via Admin UI.
3. Admin Service kirim pesan: *"Ada update config!"* (Publish).
4. Semua processor langsung dengar notifikasi ("Ting! 🔔").
5. Masing-masing processor **baca ulang konfigurasi** dari database.
6. Sistem update **tanpa restart**.

---

## Relay Service Refactoring (Additional Context)

The `relay-service` has been refactored to support multiple transport protocols:

| Service | Protocol | Plugin | Use Case |
|---------|----------|--------|----------|
| `relay-service` | NATS | `@tazama-lf/nats-relay-plugin` | Internal messaging |
| `relay-service-kafka` | Kafka | `@tazama-lf/kafka-relay-plugin` | Event streaming |
| `relay-service-rest` | HTTP | `@tazama-lf/rest-relay-plugin` | Webhook callbacks |

---

## Summary

| Service | Subscribes? | Reload Action | Criticality |
|---------|-------------|---------------|-------------|
| `event-director` | ✅ | Reload Network Map | **High** - Controls routing |
| `typology-processor` | ✅ | Reload Typology Configs | **High** - Aggregates rules |
| `rule-executer` | ✅ | Log signal (future: clear cache) | **Medium** - Alignment |
| `admin-service` | ❌ | Publisher only | N/A |
| `relay-service` | ❌ | Not applicable | N/A |


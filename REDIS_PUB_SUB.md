# Redis Pub/Sub for Hot Reload and Relay Service Refactoring

This document outlines the Redis Pub/Sub mechanism used for hot reloading configurations in the Tazama FDS, and the refactoring done to support multi-transport relay services.

## Hot Reload Mechanism

The system uses Redis Pub/Sub to broadcast configuration updates to all interested services without requiring a restart.

### Simplified Explanation (Analogi Grup Chat)

Bayangkan sistem ini seperti **Grup Chat**:

1.  **Redis Pub/Sub** adalah **Grup Chat "Info Penting"**.
2.  **Admin Service** adalah **Admin Grup**.
3.  **Processors** (`typology-processor`, `event-director`, dll) adalah **Anggota Grup**.
4.  **Subscribe** artinya **Join Grup**.

**Alurnya:**
1.  Processor **Join Grup** (Subscribe). *"Kalau ada update, kasih tau ya!"*
2.  User mengubah aturan di Admin UI.
3.  **Admin Service** mengirim pesan ke grup: *"Eh ada aturan baru nih!"* (Publish).
4.  Processor mendengar notifikasi ("Ting! 🔔").
5.  Processor langsung **baca ulang buku catatan** (Database) untuk mengambil aturan terbaru.
6.  Sistem jadi update **tanpa perlu di-restart**.

---

### Technical Implementation

#### Refactoring Decision

We introduced a shared `redis.service.ts` in the Admin Service to handle publishing commands.

**Why Refactor?**
1.  **Code Duplication**: Previously, the logic to connect/publish/disconnect was duplicated or only existed in `network.map.repository.ts`.
2.  **Consistency**: Hot reload must trigger on **Create**, **Update**, and **Delete** for **ALL** configuration types (Network Map, Rules, Typologies).
3.  **Clean Code**: Extracting the logic into a shared service makes the repository files cleaner and easier to maintain.

#### Channels

- **`config:reload`**: Published when any configuration change occurs.
  - **Payload**: String timestamp (e.g., `Configuration updated at ...`)
  - **Subscribers**: `rule-executer`, `typology-processor`, `event-director`

### Workflow

1.  **Configuration Update**: Administrator updates a Network Map, Rule, or Typology.
2.  **Notification**: The Admin Service (via `redis.service.ts`) publishes to the `config:reload` channel.
3.  **Reload**: Consuming services receive the signal and re-fetch active configurations from the database.

## Relay Service Refactoring

The `relay-service` has been refactored to support multiple transport protocols via a plugin-like architecture.

### Supported Transports

1.  **NATS** (`relay-service` / `relay-service-nats`)
    - Uses `@tazama-lf/nats-relay-plugin`.
    - Relays FDS results back to NATS subjects.

2.  **Kafka** (`relay-service-kafka`)
    - Uses `@tazama-lf/kafka-relay-plugin`.
    - Relays FDS results to a Kafka topic (e.g., `tazama.evaluation.result`).

3.  **REST** (`relay-service-rest`)
    - Uses `@tazama-lf/rest-relay-plugin`.
    - Pushes FDS results via HTTP POST to a webhook.

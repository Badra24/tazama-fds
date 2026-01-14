# NATS Relay Plugin

A TypeScript plugin for relaying messages to NATS, a simple, secure, and high-performance open source messaging system.

## Overview

The NATS Relay Plugin is a transport plugin that enables applications to easily connect to and publish messages to a NATS server. It wraps the underlying NATS client functionality and provides a simple interface for initialization and message relaying. The plugin integrates with application performance monitoring (APM) to track transactions and spans, making it easy to monitor and troubleshoot message publishing.

## Features

- Connect to NATS servers with configurable connection settings
- Support for TLS connections with certificate authority
- Publish various data types (binary, string, object) to configurable NATS subjects
- Automatic data type conversion for simple integration
- APM integration for performance monitoring and tracing
- Comprehensive logging for debugging and operational visibility
- Simple API with just two methods: `init()` and `relay()`
- Written in TypeScript with full type safety
- Fully tested with Jest

## Core Components

- **NatsRelayPlugin Class**: Main implementation that handles connection and message relaying
- **Configuration Module**: Environment-based configuration system

## Installation

```bash
npm install @tazama-lf/nats-relay-plugin
```

## Configuration

The plugin uses environment variables for configuration. Create a `.env` file in the root directory with the following variables:

```
DESTINATION_TRANSPORT_URL=tls://localhost:4223
PRODUCER_STREAM=example.subject
NATS_TLS_CA=/path/to/ca.pem
```

### Configuration Options

| Environment Variable      | Description                              | Default Value                    |
| ------------------------- | ---------------------------------------- | -------------------------------- |
| DESTINATION_TRANSPORT_URL | The URL of the NATS server to connect to | tls://localhost:4223             |
| PRODUCER_STREAM           | The subject to publish messages to       | example.subject                  |
| NATS_TLS_CA               | Path to the Certificate Authority file   | (required for TLS in production) |

## Usage

### Basic Usage

```typescript
import NatsRelayPlugin from '@tazama-lf/nats-relay-plugin';
import { LoggerService, Apm } from '@tazama-lf/frms-coe-lib';

// Create logger and APM instances
const loggerService = new LoggerService();
const apm = new Apm();

// Create plugin instance
const natsRelayPlugin = new NatsRelayPlugin();

// Initialize the plugin (connects to NATS server)
await natsRelayPlugin.init(loggerService, apm);

// Create some data to send (supports various formats)
const stringData = 'Hello, NATS!';
const binaryData = new TextEncoder().encode('Hello, NATS!');
const objectData = { message: 'Hello, NATS!', timestamp: Date.now() };

// Relay the data to NATS (each format is handled appropriately)
await natsRelayPlugin.relay(stringData);
await natsRelayPlugin.relay(binaryData);
await natsRelayPlugin.relay(objectData); // Objects need to be cast to any
```

## API Reference

### `NatsRelayPlugin` Class

The main class that implements the `ITransportPlugin` interface.

#### Methods

##### `init(loggerService, apm)`

Must accept `loggerService` and `apm` as parameter.
Initializes the connection to the NATS server.

```typescript
async init(loggerService?: LoggerService, apm?: Apm): Promise<void>
```

- **Parameters**:
  - `loggerService`: Service instance for handling application logging and monitoring operations
  - `apm`: Application Performance Monitoring service for tracking metrics, errors, and performance data
- **Returns**: A Promise that resolves when the connection is established
- **Functionality**:
  - Establishes connection to NATS server using the configured server URL
  - Sets up TLS with the provided CA certificate (only in non-dev environments when NATS_TLS_CA is provided)
  - Logs success or failure of connection attempt
  - Handles connection errors gracefully

##### `relay(data)`

Relays (publishes) data to the configured NATS subject.

```typescript
async relay(data: Uint8Array | string): Promise<void>
```

- **Parameters**:
  - `data`: The data to relay to NATS. Can be a Uint8Array, string, or any object that can be converted to JSON.
- **Returns**: A Promise that resolves when the operation completes.
- **Throws**: May throw errors if the NATS connection fails. These are caught internally and logged, but do not cause the Promise to reject.
- **Functionality**:
  - Creates an APM transaction for monitoring
  - Creates a span to track the relay operation
  - Converts the input data to the appropriate format:
    - Buffers are sent as-is
    - Strings are sent as-is
    - Objects are JSON-serialized
  - Publishes the data to the configured NATS subject
  - Logs the operation and any errors
  - Ends the APM transaction

### Configuration Module

The `config.ts` module loads configuration from environment variables.

- **Functionality**:
  - Loads the .env file from the project root
  - Provides server URL and subject name with defaults
  - Exports a typed configuration object

### Interfaces

#### `ITransportPlugin`

Import `ITransportPlugin` from `@tazama-lf/frms-coe-lib/lib/interfaces/relay-service/ITransportPlugin`.

```typescript
export interface ITransportPlugin {
  init: (loggerService?: LoggerService, apm?: Apm) => Promise<void>;
  relay: (data: Uint8Array | string) => Promise<void>;
}
```

Used to enforce the required structure for compatability with the `relay-service`

#### `Configuration`

The configuration is handled through the `@tazama-lf/frms-coe-lib` processor config system with additional environment variables.

```typescript
export interface ExtendedConfig {
  DESTINATION_TRANSPORT_URL: string;
  PRODUCER_STREAM: string;
  NATS_TLS_CA?: string;
}

export type Configuration = ProcessorConfig & ExtendedConfig;
```

## Project Structure

```
nats-relay-plugin/
├── dist/                   # Compiled JavaScript output
├── node_modules/           # Dependencies
├── src/
│   ├── config.ts           # Configuration module
│   ├── index.ts            # Main entry point
│   └── service/
│       └── natsRelayPlugin.ts   # Main implementation
├── __tests__/
│   └── natsRelayPlugin.test.ts  # Tests for the plugin
├── .env                    # Environment variables (create this)
├── package.json            # Project metadata and dependencies
├── tsconfig.json           # TypeScript configuration
├── jest.config.ts          # Jest configuration
└── README.md               # This file
```

## Development

### Prerequisites

- Node.js (>=14.x)
- npm or yarn
- A running NATS server for testing
- TLS certificate for secure connections

### Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file with your configuration, including the path to your CA certificate file
4. Build the project:
   ```bash
   npm run build
   ```

### Available Scripts

- `npm run clean` - Clean build artifacts
- `npm run build` - Build the TypeScript code
- `npm test` - Run the test suite
- `npm run fix:eslint` - Fix ESLint issues automatically
- `npm run fix:prettier` - Fix Prettier issues automatically
- `npm run lint` - Lint the codebase (ESLint and Prettier)
- `npm run lint:eslint` - Run ESLint only
- `npm run lint:prettier` - Run Prettier check only
- `npm run prepare` - Prepare husky hooks

## Testing

The plugin includes comprehensive unit tests using Jest. The tests cover connection initialization, successful message relaying, and error handling scenarios. Tests include:

- Connection establishment with and without TLS
- Data relay for different formats (string, Buffer, objects)
- Error handling for connection failures and relay errors
- APM transaction and span creation

Mocks are used for NATS connections, logger service, APM, and file system to isolate the testing of the plugin's functionality.

To run the tests:

```bash
npm test
```

## License

SPDX-License-Identifier: Apache-2.0

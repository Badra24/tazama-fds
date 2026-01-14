// SPDX-License-Identifier: Apache-2.0
import type { LoggerService } from '@tazama-lf/frms-coe-lib';
import { validateProcessorConfig } from '@tazama-lf/frms-coe-lib/lib/config/processor.config';
import type { ITransportPlugin } from '@tazama-lf/frms-coe-lib/lib/interfaces/relay-service/ITransportPlugin';
import type { Apm } from '@tazama-lf/frms-coe-lib/lib/services/apm';
import { connect, type NatsConnection } from 'nats';
import fs from 'node:fs';
import * as util from 'node:util';
import { additionalEnvironmentVariables, type Configuration } from '../config';

export default class NatsRelayPlugin implements ITransportPlugin {
  private natsConnection?: NatsConnection;
  private loggerService?: LoggerService;
  private apm?: Apm;
  private readonly configuration: Configuration;

  constructor() {
    this.configuration = validateProcessorConfig(additionalEnvironmentVariables) as Configuration;
  }

  async init(loggerService?: LoggerService, apm?: Apm): Promise<void> {
    this.loggerService = loggerService;
    this.apm = apm;
    try {
      this.loggerService?.log(`Initializing NATS connection: ${this.configuration.DESTINATION_TRANSPORT_URL}`, NatsRelayPlugin.name);
      if (this.configuration.nodeEnv !== 'dev' && this.configuration.NATS_TLS_CA) {
        const tlsOptions = {
          ca: fs.readFileSync(this.configuration.NATS_TLS_CA, 'utf-8'),
        };
        this.natsConnection = await connect({
          servers: this.configuration.DESTINATION_TRANSPORT_URL,
          tls: tlsOptions,
        });
      } else {
        this.natsConnection = await connect({
          servers: this.configuration.DESTINATION_TRANSPORT_URL,
        });
      }
      this.loggerService?.log('NATS connection established', NatsRelayPlugin.name);
    } catch (error) {
      this.loggerService?.error(`Error connecting to NATS: ${util.inspect(error)}`, NatsRelayPlugin.name);
      throw error as Error;
    }
  }

  /**
   * Relays data to a NATS stream.
   *
   * This method publishes the provided data to the configured NATS producer stream.
   * It handles different input formats (Uint8Array, string, or other objects),
   * creates APM transactions and spans for monitoring, and logs the operation.
   *
   * @param data - The data to relay to NATS. Can be a Uint8Array, string, or any object
   *               that can be converted to JSON.
   * @returns A Promise that resolves when the operation completes.
   * @throws May throw errors if the NATS connection fails. These are caught internally
   *         and logged, but do not cause the Promise to reject.
   */
  async relay(data: Uint8Array | string): Promise<void> {
    let apmTransaction = null;
    try {
      apmTransaction = this.apm?.startTransaction(NatsRelayPlugin.name);
      const span = this.apm?.startSpan('relay');
      this.loggerService?.log('Relaying data to NATS', NatsRelayPlugin.name);

      let payload: Uint8Array | string | undefined;
      if (Buffer.isBuffer(data)) {
        payload = data;
      } else if (typeof data === 'string') {
        payload = data;
      } else {
        payload = JSON.stringify(data);
      }

      this.natsConnection?.publish(this.configuration.PRODUCER_STREAM, payload);

      span?.end();
    } catch (error) {
      this.loggerService?.error(`Error relaying data to NATS: ${util.inspect(error)}`, NatsRelayPlugin.name);
      await Promise.reject(error as Error);
    } finally {
      apmTransaction?.end();
    }
  }
}

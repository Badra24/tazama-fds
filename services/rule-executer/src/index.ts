// SPDX-License-Identifier: Apache-2.0
import './apm';

import { LoggerService, type DatabaseManagerInstance } from '@tazama-lf/frms-coe-lib';
import { Database } from '@tazama-lf/frms-coe-lib/lib/config/database.config';
import { validateProcessorConfig } from '@tazama-lf/frms-coe-lib/lib/config/processor.config';
import { Cache } from '@tazama-lf/frms-coe-lib/lib/config/redis.config';
import { CreateStorageManager } from '@tazama-lf/frms-coe-lib/lib/services/dbManager';
import { StartupFactory, type IStartupService } from '@tazama-lf/frms-coe-startup-lib';
import cluster from 'node:cluster';
import os from 'node:os';
import * as util from 'node:util';
import { setTimeout } from 'node:timers/promises';
import { additionalEnvironmentVariables, type Configuration } from './config';
import { execute } from './controllers/execute';


let configuration = validateProcessorConfig(additionalEnvironmentVariables) as Configuration;

export const loggerService: LoggerService = new LoggerService(configuration);
export let server: IStartupService;

let databaseManager: DatabaseManagerInstance<Configuration>;
const logContext = 'startup';

const runServer = async (): Promise<void> => {
  server = new StartupFactory();
  if (configuration.nodeEnv !== 'test') {
    let isConnected = false;
    /* eslint-disable no-await-in-loop -- retry logic */
    for (let retryCount = 0; retryCount < 10; retryCount += 1) {
      loggerService.log('Connecting to nats server...', logContext, configuration.functionName);
      if (
        await server.init(
          execute,
          loggerService,
          [`sub-rule-${configuration.RULE_NAME}@${configuration.RULE_VERSION}`],
          `pub-rule-${configuration.RULE_NAME}@${configuration.RULE_VERSION}`,
        )
      ) {
        loggerService.log('Connected to nats', logContext, configuration.functionName);
        isConnected = true;
        break;
      } else {
        loggerService.warn(`Unable to connect, retry count: ${retryCount}`, logContext, configuration.functionName);
        await setTimeout(5000);
      }
    }
    /* eslint-enable no-await-in-loop */

    if (!isConnected) {
      throw new Error('Unable to connect to nats after 10 retries');
    }
  }
};
const numCPUs = os.cpus().length > configuration.maxCPU ? configuration.maxCPU + 1 : os.cpus().length + 1;

export const initializeDB = async (): Promise<void> => {
  const auth = configuration.nodeEnv === 'production';
  const { config, db } = await CreateStorageManager<Configuration>(
    [Database.CONFIGURATION, Database.EVENT_HISTORY, Database.RAW_HISTORY, Cache.LOCAL],
    auth,
  );
  databaseManager = db;
  configuration = { ...configuration, ...config };
  loggerService.log(util.inspect(databaseManager.isReadyCheck()), logContext, configuration.functionName);
};

process.on('uncaughtException', (err) => {
  loggerService.error(`process on uncaughtException error: ${util.inspect(err)}`, logContext, configuration.functionName);
});

process.on('unhandledRejection', (err) => {
  loggerService.error(`process on unhandledRejection error: ${util.inspect(err)}`, logContext, configuration.functionName);
});

if (cluster.isPrimary && configuration.maxCPU !== 1) {
  loggerService.log(`Primary ${process.pid} is running`);

  // Fork workers.
  for (let i = 1; i < numCPUs; i += 1) {
    cluster.fork();
  }

  cluster.on('exit', (worker, code, signal) => {
    loggerService.log(`worker ${Number(worker.process.pid)} died, starting another worker`);
    cluster.fork();
  });
} else if (process.env.NODE_ENV !== 'test') {
  (async () => {
    try {
      await initializeDB();
      await runServer();
      subscribeToConfigReload();
    } catch (err) {
      loggerService.error('Error while starting services', util.inspect(err), logContext, configuration.functionName);
      process.exit(1);
    }
  })();
}

/**
 * Subscribe to Redis Pub/Sub channel for configuration reload signals.
 * When admin-service publishes to 'config:reload', this service essentially clears any local cache if applicable
 * or simply acknowledges the update.
 * Note: Since rule-executer fetches config per transaction via databaseManager,
 * ensuring databaseManager's cache is consistent is key.
 * For now, we follow the pattern of other services to listen to the channel.
 */
/**
 * Subscribe to Redis Pub/Sub channel for configuration reload signals.
 * When admin-service publishes to 'config:reload', this service essentially clears any local cache if applicable
 * or simply acknowledges the update.
 * Note: Since rule-executer fetches config per transaction via databaseManager,
 * ensuring databaseManager's cache is consistent is key.
 * For now, we follow the pattern of other services to listen to the channel.
 */
function subscribeToConfigReload(): void {
  const Redis = require('ioredis');
  const redisConfig = configuration.redisConfig;
  const redisHost = redisConfig?.servers?.[0]?.host || 'tazama-valkey';
  const redisPort = redisConfig?.servers?.[0]?.port || 6379;

  const subscriber = new Redis({ host: redisHost, port: redisPort });

  subscriber.subscribe('config:reload', (err: Error | null) => {
    if (err) {
      loggerService.error(`[Hot-Reload] Failed to subscribe to config:reload channel: ${err.message}`, logContext, configuration.functionName);
      return;
    }
    loggerService.log('[Hot-Reload] Subscribed to config:reload channel', logContext, configuration.functionName);
  });

  subscriber.on('message', async (channel: string, message: string) => {
    if (channel === 'config:reload') {
      loggerService.log(`[Hot-Reload] Received reload signal: ${message}`, logContext, configuration.functionName);
      // In a more advanced implementation, we would clear specific caches here.
      // For now, logging confirms connectivity to the control plane.
      // If databaseManager has an internal cache that needs clearing, it should be done here.
      // Assuming databaseManager.deleteKey or similar might be needed if it caches permanently.
      // But based on current visibility, we are just aligning with the architecture.
    }
  });
};

export { configuration, databaseManager, runServer };

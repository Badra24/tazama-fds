// SPDX-License-Identifier: Apache-2.0
import './apm';
import { LoggerService, type DatabaseManagerInstance } from '@tazama-lf/frms-coe-lib';
import { validateProcessorConfig } from '@tazama-lf/frms-coe-lib/lib/config/';
import { StartupFactory, type IStartupService } from '@tazama-lf/frms-coe-startup-lib';
import NodeCache from 'node-cache';
import cluster from 'node:cluster';
import os from 'node:os';
import * as util from 'node:util';
import { setTimeout } from 'node:timers/promises';
import { additionalEnvironmentVariables, type Configuration } from './config';
import { handleTransaction, loadAllNetworkConfigurations } from './services/logic.service';
import { Singleton } from './services/services';

let configuration = validateProcessorConfig(additionalEnvironmentVariables) as Configuration;

export const loggerService: LoggerService = new LoggerService(configuration);

export const nodeCache = new NodeCache();
export let server: IStartupService;

export const runServer = async (): Promise<void> => {
  server = new StartupFactory();
  if (configuration.nodeEnv !== 'test') {
    let isConnected = false;
    for (let retryCount = 0; retryCount < 10; retryCount++) {
      loggerService.log('Connecting to nats server...');
      if (!(await server.init(handleTransaction))) {
        await setTimeout(5000);
      } else {
        loggerService.log('Connected to nats');
        isConnected = true;
        break;
      }
    }
    if (!isConnected) {
      throw new Error('Unable to connect to nats after 10 retries');
    }
  }
};

process.on('uncaughtException', (err) => {
  loggerService.error(`process on uncaughtException error: ${util.inspect(err)}`);
});

process.on('unhandledRejection', (err) => {
  loggerService.error(`process on unhandledRejection error: ${util.inspect(err)}}`);
});

const numCPUs = os.cpus().length > configuration.maxCPU ? configuration.maxCPU + 1 : os.cpus().length + 1;

let databaseManager: DatabaseManagerInstance<Configuration>;

export const dbInit = async (): Promise<void> => {
  const { config, db: manager } = await Singleton.getDatabaseManager(configuration);
  loggerService.log(manager.isReadyCheck() as string);
  databaseManager = manager;
  configuration = { ...configuration, ...config };
};

if (cluster.isPrimary && configuration.maxCPU !== 1) {
  loggerService.log(`Primary ${process.pid} is running`);

  // Fork workers
  for (let i = 1; i < numCPUs; i++) {
    cluster.fork();
  }

  cluster.on('exit', (worker, code, signal) => {
    loggerService.log(`worker ${Number(worker.process.pid)} died, starting another worker`);
    cluster.fork();
  });
} else {
  // Workers can share any TCP connection
  // In this case it is an HTTP server
  (async () => {
    try {
      if (configuration.nodeEnv !== 'test') {
        await runServer();
        await dbInit();
        // Load all tenant network configurations at startup
        await loadAllNetworkConfigurations();
        // Subscribe to Redis for hot-reload
        subscribeToConfigReload();
      }
    } catch (err) {
      loggerService.error(`Error while starting NATS server on Worker ${process.pid}`, util.inspect(err));
      process.exit(1);
    }
  })();
  loggerService.log(`Worker ${process.pid} started`);
}

/**
 * Subscribe to Redis Pub/Sub channel for configuration reload signals.
 */
function subscribeToConfigReload(): void {
  const Redis = require('ioredis');
  const redisConfig = (configuration as any).redisConfig;
  const redisHost = redisConfig?.servers?.[0]?.host || 'tazama-valkey';
  const redisPort = redisConfig?.servers?.[0]?.port || 6379;

  const subscriber = new Redis({ host: redisHost, port: redisPort });

  subscriber.subscribe('config:reload', (err: Error | null) => {
    if (err) {
      loggerService.error(`[Hot-Reload] Failed to subscribe: ${err.message}`);
      return;
    }
    loggerService.log('[Hot-Reload] Subscribed to config:reload channel');
  });

  subscriber.on('message', async (channel: string, message: string) => {
    if (channel === 'config:reload') {
      loggerService.log(`[Hot-Reload] Received reload signal: ${message}`);
      try {
        await loadAllNetworkConfigurations();
        loggerService.log('[Hot-Reload] Network configurations reloaded successfully');
      } catch (error) {
        loggerService.error(`[Hot-Reload] Reload failed: ${(error as Error).message}`);
      }
    }
  });
}

export { configuration, databaseManager };

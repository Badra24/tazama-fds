// SPDX-License-Identifier: Apache-2.0
import { loggerService } from '..';

/**
 * Publish configuration reload signal to Redis Pub/Sub channel.
 * All processors subscribed to 'config:reload' will reload their configurations.
 */
export async function publishReloadSignal(): Promise<void> {
    try {
        const Redis = require('ioredis');
        // Get Redis config from environment (same as processors)
        const redisServers = process.env.REDIS_SERVERS ? JSON.parse(process.env.REDIS_SERVERS) : [{ host: 'tazama-valkey', port: 6379 }];
        const redisHost = redisServers[0]?.host || 'tazama-valkey';
        const redisPort = redisServers[0]?.port || 6379;

        const publisher = new Redis({ host: redisHost, port: redisPort });
        await publisher.publish('config:reload', `Configuration updated at ${new Date().toISOString()}`);
        await publisher.quit();

        loggerService.log('[Hot-Reload] Published config:reload signal to Redis');
    } catch (error) {
        loggerService.error(`[Hot-Reload] Failed to publish reload signal: ${(error as Error).message}`);
    }
}

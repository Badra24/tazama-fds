// SPDX-License-Identifier: Apache-2.0
import { connect } from 'nats';
import NatsRelayPlugin from '../src/service/natsRelayPlugin';
import { LoggerService } from '@tazama-lf/frms-coe-lib';
import fs from 'node:fs';
import { validateProcessorConfig } from '@tazama-lf/frms-coe-lib/lib/config/processor.config';
import * as util from 'node:util';

// Mock dependencies
jest.mock('nats');
jest.mock('node:fs');
jest.mock('@tazama-lf/frms-coe-lib/lib/config/processor.config', () => ({
  validateProcessorConfig: jest.fn(),
}));

describe('NatsRelayPlugin', () => {
  let natsRelayPlugin: NatsRelayPlugin;
  let mockLoggerService: jest.Mocked<LoggerService>;
  let mockNatsConnection: any;
  let mockApm: any;

  beforeEach(() => {
    jest.clearAllMocks();

    (validateProcessorConfig as jest.Mock).mockReturnValue({
      nodeEnv: 'dev',
      DESTINATION_TRANSPORT_URL: 'nats://localhost:4222',
      PRODUCER_STREAM: 'test.subject',
      NATS_TLS_CA: '/path/to/ca.pem',
    });

    (fs.readFileSync as jest.Mock).mockReturnValue('-----BEGIN CERTIFICATE-----\nMockCertificateContent\n-----END CERTIFICATE-----');

    mockLoggerService = {
      log: jest.fn(),
      error: jest.fn(),
    } as unknown as jest.Mocked<LoggerService>;

    mockNatsConnection = {
      publish: jest.fn(),
      info: undefined,
    };

    mockApm = {
      startSpan: jest.fn().mockReturnValue({ end: jest.fn() }),
      startTransaction: jest.fn().mockReturnValue({ end: jest.fn() }),
      captureError: jest.fn(),
    };

    (connect as jest.Mock).mockResolvedValue(mockNatsConnection);

    natsRelayPlugin = new NatsRelayPlugin();
  });

  describe('init', () => {
    it('should establish a NATS connection successfully without TLS in dev environment', async () => {
      await natsRelayPlugin.init(mockLoggerService, mockApm);
      expect(connect).toHaveBeenCalledWith({
        servers: 'nats://localhost:4222',
      });
      expect(mockLoggerService.log).toHaveBeenCalledWith('NATS connection established', 'NatsRelayPlugin');
    });

    it('should establish a NATS connection with TLS in production environment', async () => {
      (validateProcessorConfig as jest.Mock).mockReturnValueOnce({
        nodeEnv: 'production',
        DESTINATION_TRANSPORT_URL: 'tls://localhost:4223',
        PRODUCER_STREAM: 'test.subject',
        NATS_TLS_CA: '/path/to/ca.pem',
      });
      (fs.readFileSync as jest.Mock).mockReturnValueOnce('-----BEGIN CERTIFICATE-----\nMockCertificateContent\n-----END CERTIFICATE-----');

      const prodNatsRelayPlugin = new NatsRelayPlugin();
      await prodNatsRelayPlugin.init(mockLoggerService, mockApm);

      expect(connect).toHaveBeenCalledWith({
        servers: 'tls://localhost:4223',
        tls: {
          ca: '-----BEGIN CERTIFICATE-----\nMockCertificateContent\n-----END CERTIFICATE-----',
        },
      });
      expect(mockLoggerService.log).toHaveBeenCalledWith('NATS connection established', 'NatsRelayPlugin');
    });

    it('should handle connection error', async () => {
      const error = new Error('Connection failed');
      (connect as jest.Mock).mockRejectedValueOnce(error);

      await expect(natsRelayPlugin.init(mockLoggerService, mockApm)).rejects.toThrow('Connection failed');

      expect(connect).toHaveBeenCalledWith({
        servers: 'nats://localhost:4222',
      });
      expect(mockLoggerService.error).toHaveBeenCalledWith(`Error connecting to NATS: ${util.inspect(error)}`, 'NatsRelayPlugin');
    });
  });

  describe('relay', () => {
    beforeEach(async () => {
      await natsRelayPlugin.init(mockLoggerService, mockApm);
      mockNatsConnection.publish.mockClear();
    });

    it('should relay object data to NATS successfully (converts to JSON string)', async () => {
      const testData = { message: 'test' };

      await natsRelayPlugin.relay(testData as any);

      expect(mockLoggerService.log).toHaveBeenCalledWith('Relaying data to NATS', 'NatsRelayPlugin');
      expect(mockNatsConnection.publish).toHaveBeenCalledWith('test.subject', JSON.stringify(testData));
    });

    it('should relay string data to NATS successfully', async () => {
      const stringData = 'test message';

      await natsRelayPlugin.relay(stringData);

      expect(mockLoggerService.log).toHaveBeenCalledWith('Relaying data to NATS', 'NatsRelayPlugin');
      expect(mockNatsConnection.publish).toHaveBeenCalledWith('test.subject', stringData);
    });

    it('should relay buffer data to NATS successfully', async () => {
      const bufferData = Buffer.from('test message');

      await natsRelayPlugin.relay(bufferData);

      expect(mockLoggerService.log).toHaveBeenCalledWith('Relaying data to NATS', 'NatsRelayPlugin');
      expect(mockNatsConnection.publish).toHaveBeenCalledWith('test.subject', bufferData);
    });

    it('should handle relay error', async () => {
      const error = new Error('Publish failed');
      mockNatsConnection.publish.mockImplementationOnce(() => {
        throw error;
      });
      mockNatsConnection.info = { server_id: 'test-server', server_name: 'test' };

      const testData = 'test message';

      await expect(natsRelayPlugin.relay(testData)).rejects.toThrow('Publish failed');

      expect(mockLoggerService.error).toHaveBeenCalledWith(`Error relaying data to NATS: ${util.inspect(error)}`, 'NatsRelayPlugin');
    });
  });
});

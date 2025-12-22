/**
 * Vastar Connector SDK for TypeScript/Node.js
 *
 * A powerful SDK for building connectors that communicate with the Vastar
 * Connector Runtime via IPC (Inter-Process Communication).
 *
 * @packageDocumentation
 */

export { RuntimeClient } from './runtime-client';
export { ConnectorException } from './errors';
export {
  HTTPResponseHelper,
  RetryHelper,
  SSEParser,
  sleep,
} from './utils';

export * from './types';

// Re-export FlatBuffers protocol types for advanced users
export { ExecuteRequest } from './protocol/vastar/connector/ipc/execute-request';
export { ExecuteResponse } from './protocol/vastar/connector/ipc/execute-response';
export { ErrorClass as ProtocolErrorClass } from './protocol/vastar/connector/ipc/error-class';
export { MessageType as ProtocolMessageType } from './protocol/vastar/connector/ipc/message-type';



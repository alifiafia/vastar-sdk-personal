/**
 * Error classification for connector operations
 */
export enum ErrorClass {
  Success = 0,
  Transient = 1,
  Permanent = 2,
  RateLimited = 3,
  Timeout = 4,
  InvalidRequest = 5,
}

/**
 * HTTP request configuration
 */
export interface HTTPRequestConfig {
  method: string;
  url: string;
  headers?: Record<string, string>;
  body?: string | Buffer;
  timeoutMs?: number;
  tenantId?: string;
  workspaceId?: string;
  traceId?: string;
}

/**
 * HTTP response data
 */
export interface HTTPResponse {
  requestId: number;
  statusCode: number;
  headers: Record<string, string>;
  body: Buffer;
  durationUs: number;
  errorClass: ErrorClass;
  errorMessage?: string;
}

/**
 * Runtime client configuration
 */
export interface RuntimeClientConfig {
  tenantId?: string;
  workspaceId?: string;
  timeoutMs?: number;
  socketPath?: string;
  useTcp?: boolean;
  tcpHost?: string;
  tcpPort?: number;
}

/**
 * Connection options
 */
export interface ConnectionOptions {
  socketPath: string;
  timeout: number;
}

/**
 * Frame message types
 */
export enum MessageType {
  ExecuteRequest = 0x00,
  ExecuteResponse = 0x01,
}

/**
 * Protocol constants
 */
export const PROTOCOL_CONSTANTS = {
  FRAME_LENGTH_SIZE: 4,
  MESSAGE_TYPE_SIZE: 1,
  MAX_PAYLOAD_SIZE: 10 * 1024 * 1024, // 10MB
  DEFAULT_TIMEOUT_MS: 60000, // 60 seconds
  DEFAULT_SOCKET_PATH: '/tmp/vastar-connector-runtime.sock',
  DEFAULT_TCP_HOST: '127.0.0.1',
  DEFAULT_TCP_PORT: 5000,
} as const;


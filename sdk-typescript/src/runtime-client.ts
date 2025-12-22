import * as net from 'net';
import * as flatbuffers from 'flatbuffers';
import {
  RuntimeClientConfig,
  HTTPRequestConfig,
  HTTPResponse,
  ErrorClass,
  MessageType,
  PROTOCOL_CONSTANTS,
} from './types';
import { ConnectorException } from './errors';
import { ExecuteRequest } from './protocol/vastar/connector/ipc/execute-request';
import { ExecuteResponse } from './protocol/vastar/connector/ipc/execute-response';

/**
 * RuntimeClient provides IPC communication with Vastar Connector Runtime
 *
 * Features:
 * - Unix Domain Socket support (Linux/macOS) for optimal performance
 * - TCP fallback for Windows or network scenarios
 * - FlatBuffers protocol for efficient serialization
 * - HTTP connector with SSE streaming support
 * - Type-safe APIs with TypeScript
 * - Automatic connection pooling via runtime
 * - Circuit breaker and retry mechanisms (runtime-level)
 *
 * @example
 * ```typescript
 * const client = new RuntimeClient({
 *   tenantId: 'my-tenant',
 *   timeoutMs: 60000
 * });
 *
 * const response = await client.executeHTTP({
 *   method: 'GET',
 *   url: 'https://api.example.com/data'
 * });
 *
 * console.log('Status:', response.statusCode);
 * console.log('Body:', response.body.toString());
 *
 * await client.close();
 * ```
 */
export class RuntimeClient {
  private socket: net.Socket | null = null;
  private readonly config: Required<RuntimeClientConfig>;
  private requestIdSeq: number;
  private pendingRequests: Map<number, PendingRequest> = new Map();

  constructor(config: RuntimeClientConfig = {}) {
    this.config = {
      tenantId: config.tenantId || 'default',
      workspaceId: config.workspaceId || '',
      timeoutMs: config.timeoutMs || PROTOCOL_CONSTANTS.DEFAULT_TIMEOUT_MS,
      socketPath:
        config.socketPath ||
        process.env.VASTAR_SOCKET_PATH ||
        PROTOCOL_CONSTANTS.DEFAULT_SOCKET_PATH,
      useTcp: config.useTcp || process.env.VASTAR_USE_TCP === 'true' || false,
      tcpHost:
        config.tcpHost ||
        process.env.VASTAR_TCP_HOST ||
        PROTOCOL_CONSTANTS.DEFAULT_TCP_HOST,
      tcpPort:
        config.tcpPort ||
        parseInt(process.env.VASTAR_TCP_PORT || String(PROTOCOL_CONSTANTS.DEFAULT_TCP_PORT)),
    };

    this.requestIdSeq = Date.now();
  }

  /**
   * Connect to Vastar Runtime
   */
  async connect(): Promise<void> {
    if (this.socket) {
      return; // Already connected
    }

    return new Promise((resolve, reject) => {
      this.socket = new net.Socket();

      // Setup event handlers
      this.socket.on('data', (data) => this.handleData(data));
      this.socket.on('error', (err) => this.handleError(err));
      this.socket.on('close', () => this.handleClose());

      if (this.config.useTcp) {
        // Connect via TCP
        this.socket.connect(this.config.tcpPort, this.config.tcpHost, () => {
          console.log(`🔌 Connected via TCP: ${this.config.tcpHost}:${this.config.tcpPort}`);
          resolve();
        });
      } else {
        // Connect via Unix Socket
        this.socket.connect(this.config.socketPath, () => {
          console.log(`🐧 Connected via Unix Socket: ${this.config.socketPath}`);
          resolve();
        });
      }

      // Connection timeout
      const timeout = setTimeout(() => {
        this.socket?.destroy();
        reject(new Error('Connection timeout'));
      }, this.config.timeoutMs);

      this.socket.once('connect', () => clearTimeout(timeout));
      this.socket.once('error', () => clearTimeout(timeout));
    });
  }

  /**
   * Execute HTTP request through runtime
   */
  async executeHTTP(request: HTTPRequestConfig): Promise<HTTPResponse> {
    if (!this.socket) {
      await this.connect();
    }

    const requestId = ++this.requestIdSeq;
    const tenantId = request.tenantId || this.config.tenantId;
    const workspaceId = request.workspaceId || this.config.workspaceId;
    const timeoutMs = request.timeoutMs || this.config.timeoutMs;
    const deadlineMs = Date.now() + timeoutMs;

    // Build HTTP payload (connector-specific data)
    const httpPayload: Record<string, unknown> = {
      method: request.method,
      url: request.url,
    };

    if (request.headers) {
      httpPayload.headers = request.headers;
    }

    if (request.body) {
      httpPayload.body =
        typeof request.body === 'string'
          ? request.body
          : request.body.toString('utf-8');
    }

    const payloadJSON = JSON.stringify(httpPayload);
    const payloadBytes = Buffer.from(payloadJSON, 'utf-8');

    // Build FlatBuffers ExecuteRequest
    const builder = new flatbuffers.Builder(4096);

    // Create strings first (CRITICAL: must be before startExecuteRequest)
    const tenantIdOffset = builder.createString(tenantId);
    const connectorNameOffset = builder.createString('http');
    const operationOffset = builder.createString('request');
    const payloadOffset = ExecuteRequest.createPayloadVector(
      builder,
      payloadBytes
    );

    let workspaceIdOffset = 0;
    if (workspaceId) {
      workspaceIdOffset = builder.createString(workspaceId);
    }

    let traceIdOffset = 0;
    if (request.traceId) {
      traceIdOffset = builder.createString(request.traceId);
    }

    // Build table
    ExecuteRequest.startExecuteRequest(builder);
    ExecuteRequest.addRequestId(builder, BigInt(requestId));
    ExecuteRequest.addTenantId(builder, tenantIdOffset);
    if (workspaceIdOffset > 0) {
      ExecuteRequest.addWorkspaceId(builder, workspaceIdOffset);
    }
    if (traceIdOffset > 0) {
      ExecuteRequest.addTraceId(builder, traceIdOffset);
    }
    ExecuteRequest.addConnectorName(builder, connectorNameOffset);
    ExecuteRequest.addOperation(builder, operationOffset);
    ExecuteRequest.addDeadlineAtMs(builder, BigInt(deadlineMs));
    ExecuteRequest.addPayload(builder, payloadOffset);

    const requestOffset = ExecuteRequest.endExecuteRequest(builder);
    builder.finish(requestOffset);

    // Get FlatBuffers bytes
    const requestBytes = builder.asUint8Array();

    // Send frame
    await this.sendFrame(MessageType.ExecuteRequest, Buffer.from(requestBytes));

    // Wait for response
    return this.waitForResponse(requestId, timeoutMs);
  }

  /**
   * Send frame to runtime
   */
  private async sendFrame(messageType: MessageType, payload: Buffer): Promise<void> {
    if (!this.socket) {
      throw new Error('Not connected to runtime');
    }

    const totalLen = PROTOCOL_CONSTANTS.MESSAGE_TYPE_SIZE + payload.length;

    // Frame: [length:4][type:1][payload:N]
    const frame = Buffer.allocUnsafe(PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE + totalLen);
    let offset = 0;

    // Write length (big-endian)
    frame.writeUInt32BE(totalLen, offset);
    offset += PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE;

    // Write message type
    frame.writeUInt8(messageType, offset);
    offset += PROTOCOL_CONSTANTS.MESSAGE_TYPE_SIZE;

    // Write payload
    payload.copy(frame, offset);

    // Send frame
    return new Promise((resolve, reject) => {
      if (!this.socket) {
        reject(new Error('Socket closed'));
        return;
      }

      this.socket.write(frame, (err) => {
        if (err) {
          reject(err);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Handle incoming data from socket
   */
  private receiveBuffer: Buffer = Buffer.alloc(0);

  private handleData(data: Buffer): void {
    this.receiveBuffer = Buffer.concat([this.receiveBuffer, data]);

    while (this.receiveBuffer.length >= PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE) {
      // Read frame length
      const frameLength = this.receiveBuffer.readUInt32BE(0);

      if (frameLength > PROTOCOL_CONSTANTS.MAX_PAYLOAD_SIZE) {
        this.handleError(new Error(`Invalid frame length: ${frameLength}`));
        return;
      }

      const totalFrameSize = PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE + frameLength;

      if (this.receiveBuffer.length < totalFrameSize) {
        // Wait for more data
        return;
      }

      // Extract frame
      const frameData = this.receiveBuffer.slice(
        PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE,
        totalFrameSize
      );
      this.receiveBuffer = this.receiveBuffer.slice(totalFrameSize);

      // Process frame
      this.processFrame(frameData);
    }
  }

  /**
   * Process received frame
   */
  private processFrame(frameData: Buffer): void {
    const messageType = frameData.readUInt8(0);
    const payload = frameData.slice(PROTOCOL_CONSTANTS.MESSAGE_TYPE_SIZE);

    if (messageType !== MessageType.ExecuteResponse) {
      console.error(`Unexpected message type: ${messageType}`);
      return;
    }

    // Parse ExecuteResponse
    const buf = new flatbuffers.ByteBuffer(payload);
    const response = ExecuteResponse.getRootAsExecuteResponse(buf);

    const requestId = Number(response.requestId());
    const pending = this.pendingRequests.get(requestId);

    if (!pending) {
      console.warn(`No pending request for ID: ${requestId}`);
      return;
    }

    this.pendingRequests.delete(requestId);
    clearTimeout(pending.timeout);

    const errorClass = response.errorClass();

    if (errorClass !== ErrorClass.Success) {
      const errorMessage = response.errorMessage() || 'Unknown error';
      pending.reject(new ConnectorException(errorMessage, errorClass, requestId));
      return;
    }

    // Parse response payload
    const responsePayload = response.payloadArray();
    if (!responsePayload) {
      pending.reject(
        new ConnectorException('Empty response payload', ErrorClass.Permanent, requestId)
      );
      return;
    }

    const payloadBuffer = Buffer.from(responsePayload);
    const payloadJSON = payloadBuffer.toString('utf-8');

    try {
      const httpResponse = JSON.parse(payloadJSON);

      pending.resolve({
        requestId,
        statusCode: httpResponse.status_code || httpResponse.statusCode || 0,
        headers: httpResponse.headers || {},
        body: httpResponse.body
          ? Buffer.from(httpResponse.body, 'utf-8')
          : Buffer.alloc(0),
        durationUs: Number(response.durationUs() || BigInt(0)),
        errorClass: ErrorClass.Success,
      });
    } catch (err) {
      pending.reject(
        new ConnectorException(
          `Failed to parse response: ${err}`,
          ErrorClass.Permanent,
          requestId
        )
      );
    }
  }

  /**
   * Wait for response from runtime
   */
  private waitForResponse(requestId: number, timeoutMs: number): Promise<HTTPResponse> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(
          new ConnectorException('Request timeout', ErrorClass.Timeout, requestId)
        );
      }, timeoutMs);

      this.pendingRequests.set(requestId, { resolve, reject, timeout });
    });
  }

  /**
   * Handle socket error
   */
  private handleError(err: Error): void {
    console.error('Socket error:', err);

    // Reject all pending requests
    Array.from(this.pendingRequests.entries()).forEach(([requestId, pending]) => {
      clearTimeout(pending.timeout);
      pending.reject(new ConnectorException(err.message, ErrorClass.Transient, requestId));
    });

    this.pendingRequests.clear();
  }

  /**
   * Handle socket close
   */
  private handleClose(): void {
    console.log('Connection closed');
    this.socket = null;

    // Reject all pending requests
    Array.from(this.pendingRequests.entries()).forEach(([requestId, pending]) => {
      clearTimeout(pending.timeout);
      pending.reject(
        new ConnectorException('Connection closed', ErrorClass.Transient, requestId)
      );
    });

    this.pendingRequests.clear();
  }

  /**
   * Close connection to runtime
   */
  async close(): Promise<void> {
    if (this.socket) {
      return new Promise((resolve) => {
        this.socket!.end(() => {
          console.log('✅ Connection closed');
          this.socket = null;
          resolve();
        });
      });
    }
  }
}

interface PendingRequest {
  resolve: (response: HTTPResponse) => void;
  reject: (err: Error) => void;
  timeout: NodeJS.Timeout;
}


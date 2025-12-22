"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.RuntimeClient = void 0;
const net = __importStar(require("net"));
const flatbuffers = __importStar(require("flatbuffers"));
const types_1 = require("./types");
const errors_1 = require("./errors");
const execute_request_1 = require("./protocol/vastar/connector/ipc/execute-request");
const execute_response_1 = require("./protocol/vastar/connector/ipc/execute-response");
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
class RuntimeClient {
    constructor(config = {}) {
        this.socket = null;
        this.pendingRequests = new Map();
        /**
         * Handle incoming data from socket
         */
        this.receiveBuffer = Buffer.alloc(0);
        this.config = {
            tenantId: config.tenantId || 'default',
            workspaceId: config.workspaceId || '',
            timeoutMs: config.timeoutMs || types_1.PROTOCOL_CONSTANTS.DEFAULT_TIMEOUT_MS,
            socketPath: config.socketPath ||
                process.env.VASTAR_SOCKET_PATH ||
                types_1.PROTOCOL_CONSTANTS.DEFAULT_SOCKET_PATH,
            useTcp: config.useTcp || process.env.VASTAR_USE_TCP === 'true' || false,
            tcpHost: config.tcpHost ||
                process.env.VASTAR_TCP_HOST ||
                types_1.PROTOCOL_CONSTANTS.DEFAULT_TCP_HOST,
            tcpPort: config.tcpPort ||
                parseInt(process.env.VASTAR_TCP_PORT || String(types_1.PROTOCOL_CONSTANTS.DEFAULT_TCP_PORT)),
        };
        this.requestIdSeq = Date.now();
    }
    /**
     * Connect to Vastar Runtime
     */
    async connect() {
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
            }
            else {
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
    async executeHTTP(request) {
        if (!this.socket) {
            await this.connect();
        }
        const requestId = ++this.requestIdSeq;
        const tenantId = request.tenantId || this.config.tenantId;
        const workspaceId = request.workspaceId || this.config.workspaceId;
        const timeoutMs = request.timeoutMs || this.config.timeoutMs;
        const deadlineMs = Date.now() + timeoutMs;
        // Build HTTP payload (connector-specific data)
        const httpPayload = {
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
        const payloadOffset = execute_request_1.ExecuteRequest.createPayloadVector(builder, payloadBytes);
        let workspaceIdOffset = 0;
        if (workspaceId) {
            workspaceIdOffset = builder.createString(workspaceId);
        }
        let traceIdOffset = 0;
        if (request.traceId) {
            traceIdOffset = builder.createString(request.traceId);
        }
        // Build table
        execute_request_1.ExecuteRequest.startExecuteRequest(builder);
        execute_request_1.ExecuteRequest.addRequestId(builder, BigInt(requestId));
        execute_request_1.ExecuteRequest.addTenantId(builder, tenantIdOffset);
        if (workspaceIdOffset > 0) {
            execute_request_1.ExecuteRequest.addWorkspaceId(builder, workspaceIdOffset);
        }
        if (traceIdOffset > 0) {
            execute_request_1.ExecuteRequest.addTraceId(builder, traceIdOffset);
        }
        execute_request_1.ExecuteRequest.addConnectorName(builder, connectorNameOffset);
        execute_request_1.ExecuteRequest.addOperation(builder, operationOffset);
        execute_request_1.ExecuteRequest.addDeadlineAtMs(builder, BigInt(deadlineMs));
        execute_request_1.ExecuteRequest.addPayload(builder, payloadOffset);
        const requestOffset = execute_request_1.ExecuteRequest.endExecuteRequest(builder);
        builder.finish(requestOffset);
        // Get FlatBuffers bytes
        const requestBytes = builder.asUint8Array();
        // Send frame
        await this.sendFrame(types_1.MessageType.ExecuteRequest, Buffer.from(requestBytes));
        // Wait for response
        return this.waitForResponse(requestId, timeoutMs);
    }
    /**
     * Send frame to runtime
     */
    async sendFrame(messageType, payload) {
        if (!this.socket) {
            throw new Error('Not connected to runtime');
        }
        const totalLen = types_1.PROTOCOL_CONSTANTS.MESSAGE_TYPE_SIZE + payload.length;
        // Frame: [length:4][type:1][payload:N]
        const frame = Buffer.allocUnsafe(types_1.PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE + totalLen);
        let offset = 0;
        // Write length (big-endian)
        frame.writeUInt32BE(totalLen, offset);
        offset += types_1.PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE;
        // Write message type
        frame.writeUInt8(messageType, offset);
        offset += types_1.PROTOCOL_CONSTANTS.MESSAGE_TYPE_SIZE;
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
                }
                else {
                    resolve();
                }
            });
        });
    }
    handleData(data) {
        this.receiveBuffer = Buffer.concat([this.receiveBuffer, data]);
        while (this.receiveBuffer.length >= types_1.PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE) {
            // Read frame length
            const frameLength = this.receiveBuffer.readUInt32BE(0);
            if (frameLength > types_1.PROTOCOL_CONSTANTS.MAX_PAYLOAD_SIZE) {
                this.handleError(new Error(`Invalid frame length: ${frameLength}`));
                return;
            }
            const totalFrameSize = types_1.PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE + frameLength;
            if (this.receiveBuffer.length < totalFrameSize) {
                // Wait for more data
                return;
            }
            // Extract frame
            const frameData = this.receiveBuffer.slice(types_1.PROTOCOL_CONSTANTS.FRAME_LENGTH_SIZE, totalFrameSize);
            this.receiveBuffer = this.receiveBuffer.slice(totalFrameSize);
            // Process frame
            this.processFrame(frameData);
        }
    }
    /**
     * Process received frame
     */
    processFrame(frameData) {
        const messageType = frameData.readUInt8(0);
        const payload = frameData.slice(types_1.PROTOCOL_CONSTANTS.MESSAGE_TYPE_SIZE);
        if (messageType !== types_1.MessageType.ExecuteResponse) {
            console.error(`Unexpected message type: ${messageType}`);
            return;
        }
        // Parse ExecuteResponse
        const buf = new flatbuffers.ByteBuffer(payload);
        const response = execute_response_1.ExecuteResponse.getRootAsExecuteResponse(buf);
        const requestId = Number(response.requestId());
        const pending = this.pendingRequests.get(requestId);
        if (!pending) {
            console.warn(`No pending request for ID: ${requestId}`);
            return;
        }
        this.pendingRequests.delete(requestId);
        clearTimeout(pending.timeout);
        const errorClass = response.errorClass();
        if (errorClass !== types_1.ErrorClass.Success) {
            const errorMessage = response.errorMessage() || 'Unknown error';
            pending.reject(new errors_1.ConnectorException(errorMessage, errorClass, requestId));
            return;
        }
        // Parse response payload
        const responsePayload = response.payloadArray();
        if (!responsePayload) {
            pending.reject(new errors_1.ConnectorException('Empty response payload', types_1.ErrorClass.Permanent, requestId));
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
                errorClass: types_1.ErrorClass.Success,
            });
        }
        catch (err) {
            pending.reject(new errors_1.ConnectorException(`Failed to parse response: ${err}`, types_1.ErrorClass.Permanent, requestId));
        }
    }
    /**
     * Wait for response from runtime
     */
    waitForResponse(requestId, timeoutMs) {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                this.pendingRequests.delete(requestId);
                reject(new errors_1.ConnectorException('Request timeout', types_1.ErrorClass.Timeout, requestId));
            }, timeoutMs);
            this.pendingRequests.set(requestId, { resolve, reject, timeout });
        });
    }
    /**
     * Handle socket error
     */
    handleError(err) {
        console.error('Socket error:', err);
        // Reject all pending requests
        Array.from(this.pendingRequests.entries()).forEach(([requestId, pending]) => {
            clearTimeout(pending.timeout);
            pending.reject(new errors_1.ConnectorException(err.message, types_1.ErrorClass.Transient, requestId));
        });
        this.pendingRequests.clear();
    }
    /**
     * Handle socket close
     */
    handleClose() {
        console.log('Connection closed');
        this.socket = null;
        // Reject all pending requests
        Array.from(this.pendingRequests.entries()).forEach(([requestId, pending]) => {
            clearTimeout(pending.timeout);
            pending.reject(new errors_1.ConnectorException('Connection closed', types_1.ErrorClass.Transient, requestId));
        });
        this.pendingRequests.clear();
    }
    /**
     * Close connection to runtime
     */
    async close() {
        if (this.socket) {
            return new Promise((resolve) => {
                this.socket.end(() => {
                    console.log('✅ Connection closed');
                    this.socket = null;
                    resolve();
                });
            });
        }
    }
}
exports.RuntimeClient = RuntimeClient;

"use strict";
/**
 * Vastar Connector SDK for TypeScript/Node.js
 *
 * A powerful SDK for building connectors that communicate with the Vastar
 * Connector Runtime via IPC (Inter-Process Communication).
 *
 * @packageDocumentation
 */
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
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProtocolMessageType = exports.ProtocolErrorClass = exports.ExecuteResponse = exports.ExecuteRequest = exports.sleep = exports.SSEParser = exports.RetryHelper = exports.HTTPResponseHelper = exports.ConnectorException = exports.RuntimeClient = void 0;
var runtime_client_1 = require("./runtime-client");
Object.defineProperty(exports, "RuntimeClient", { enumerable: true, get: function () { return runtime_client_1.RuntimeClient; } });
var errors_1 = require("./errors");
Object.defineProperty(exports, "ConnectorException", { enumerable: true, get: function () { return errors_1.ConnectorException; } });
var utils_1 = require("./utils");
Object.defineProperty(exports, "HTTPResponseHelper", { enumerable: true, get: function () { return utils_1.HTTPResponseHelper; } });
Object.defineProperty(exports, "RetryHelper", { enumerable: true, get: function () { return utils_1.RetryHelper; } });
Object.defineProperty(exports, "SSEParser", { enumerable: true, get: function () { return utils_1.SSEParser; } });
Object.defineProperty(exports, "sleep", { enumerable: true, get: function () { return utils_1.sleep; } });
__exportStar(require("./types"), exports);
// Re-export FlatBuffers protocol types for advanced users
var execute_request_1 = require("./protocol/vastar/connector/ipc/execute-request");
Object.defineProperty(exports, "ExecuteRequest", { enumerable: true, get: function () { return execute_request_1.ExecuteRequest; } });
var execute_response_1 = require("./protocol/vastar/connector/ipc/execute-response");
Object.defineProperty(exports, "ExecuteResponse", { enumerable: true, get: function () { return execute_response_1.ExecuteResponse; } });
var error_class_1 = require("./protocol/vastar/connector/ipc/error-class");
Object.defineProperty(exports, "ProtocolErrorClass", { enumerable: true, get: function () { return error_class_1.ErrorClass; } });
var message_type_1 = require("./protocol/vastar/connector/ipc/message-type");
Object.defineProperty(exports, "ProtocolMessageType", { enumerable: true, get: function () { return message_type_1.MessageType; } });

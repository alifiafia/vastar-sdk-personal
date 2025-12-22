"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PROTOCOL_CONSTANTS = exports.MessageType = exports.ErrorClass = void 0;
/**
 * Error classification for connector operations
 */
var ErrorClass;
(function (ErrorClass) {
    ErrorClass[ErrorClass["Success"] = 0] = "Success";
    ErrorClass[ErrorClass["Transient"] = 1] = "Transient";
    ErrorClass[ErrorClass["Permanent"] = 2] = "Permanent";
    ErrorClass[ErrorClass["RateLimited"] = 3] = "RateLimited";
    ErrorClass[ErrorClass["Timeout"] = 4] = "Timeout";
    ErrorClass[ErrorClass["InvalidRequest"] = 5] = "InvalidRequest";
})(ErrorClass || (exports.ErrorClass = ErrorClass = {}));
/**
 * Frame message types
 */
var MessageType;
(function (MessageType) {
    MessageType[MessageType["ExecuteRequest"] = 0] = "ExecuteRequest";
    MessageType[MessageType["ExecuteResponse"] = 1] = "ExecuteResponse";
})(MessageType || (exports.MessageType = MessageType = {}));
/**
 * Protocol constants
 */
exports.PROTOCOL_CONSTANTS = {
    FRAME_LENGTH_SIZE: 4,
    MESSAGE_TYPE_SIZE: 1,
    MAX_PAYLOAD_SIZE: 10 * 1024 * 1024, // 10MB
    DEFAULT_TIMEOUT_MS: 60000, // 60 seconds
    DEFAULT_SOCKET_PATH: '/tmp/vastar-connector-runtime.sock',
    DEFAULT_TCP_HOST: '127.0.0.1',
    DEFAULT_TCP_PORT: 5000,
};

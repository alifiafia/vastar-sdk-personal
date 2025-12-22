"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConnectorException = void 0;
const types_1 = require("./types");
/**
 * Exception thrown by connector operations
 */
class ConnectorException extends Error {
    constructor(message, errorClass, requestId) {
        super(message);
        this.name = 'ConnectorException';
        this.errorClass = errorClass;
        this.requestId = requestId;
        // Maintains proper stack trace for where error was thrown (only available on V8)
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, ConnectorException);
        }
    }
    /**
     * Check if error is retryable
     */
    isRetryable() {
        return (this.errorClass === types_1.ErrorClass.Transient ||
            this.errorClass === types_1.ErrorClass.RateLimited ||
            this.errorClass === types_1.ErrorClass.Timeout);
    }
    /**
     * Get error class name
     */
    getErrorClassName() {
        return types_1.ErrorClass[this.errorClass];
    }
    /**
     * Convert to JSON
     */
    toJSON() {
        return {
            name: this.name,
            message: this.message,
            errorClass: this.getErrorClassName(),
            requestId: this.requestId,
            stack: this.stack,
        };
    }
}
exports.ConnectorException = ConnectorException;

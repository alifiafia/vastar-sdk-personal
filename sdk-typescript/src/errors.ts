import { ErrorClass } from './types';

/**
 * Exception thrown by connector operations
 */
export class ConnectorException extends Error {
  public readonly requestId: number;
  public readonly errorClass: ErrorClass;

  constructor(message: string, errorClass: ErrorClass, requestId: number) {
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
  isRetryable(): boolean {
    return (
      this.errorClass === ErrorClass.Transient ||
      this.errorClass === ErrorClass.RateLimited ||
      this.errorClass === ErrorClass.Timeout
    );
  }

  /**
   * Get error class name
   */
  getErrorClassName(): string {
    return ErrorClass[this.errorClass];
  }

  /**
   * Convert to JSON
   */
  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      errorClass: this.getErrorClassName(),
      requestId: this.requestId,
      stack: this.stack,
    };
  }
}


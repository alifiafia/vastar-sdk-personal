import { HTTPResponse } from './types';

/**
 * HTTP Response utilities
 */
export class HTTPResponseHelper {
  /**
   * Check if response is 2xx
   */
  static is2xx(response: HTTPResponse): boolean {
    return response.statusCode >= 200 && response.statusCode < 300;
  }

  /**
   * Check if response is 3xx
   */
  static is3xx(response: HTTPResponse): boolean {
    return response.statusCode >= 300 && response.statusCode < 400;
  }

  /**
   * Check if response is 4xx
   */
  static is4xx(response: HTTPResponse): boolean {
    return response.statusCode >= 400 && response.statusCode < 500;
  }

  /**
   * Check if response is 5xx
   */
  static is5xx(response: HTTPResponse): boolean {
    return response.statusCode >= 500 && response.statusCode < 600;
  }

  /**
   * Get response body as string
   */
  static getBodyAsString(response: HTTPResponse): string {
    return response.body.toString('utf-8');
  }

  /**
   * Get response body as JSON
   */
  static getBodyAsJSON<T = unknown>(response: HTTPResponse): T {
    const str = this.getBodyAsString(response);
    return JSON.parse(str) as T;
  }

  /**
   * Get header value (case-insensitive)
   */
  static getHeader(response: HTTPResponse, name: string): string | undefined {
    const lowerName = name.toLowerCase();
    for (const [key, value] of Object.entries(response.headers)) {
      if (key.toLowerCase() === lowerName) {
        return value;
      }
    }
    return undefined;
  }
}

/**
 * Retry utility with exponential backoff
 */
export class RetryHelper {
  /**
   * Execute function with retry logic
   */
  static async withRetry<T>(
    fn: () => Promise<T>,
    options: {
      maxRetries?: number;
      initialBackoffMs?: number;
      maxBackoffMs?: number;
      retryableErrors?: string[];
    } = {}
  ): Promise<T> {
    const {
      maxRetries = 3,
      initialBackoffMs = 1000,
      maxBackoffMs = 30000,
      retryableErrors = ['Transient', 'RateLimited', 'Timeout'],
    } = options;

    let lastError: Error | null = null;
    let backoffMs = initialBackoffMs;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (err) {
        lastError = err as Error;

        // Check if error is retryable
        const errorStr = (err as Error).toString();
        const isRetryable = retryableErrors.some((errorType) =>
          errorStr.includes(errorType)
        );

        if (!isRetryable || attempt === maxRetries) {
          throw err;
        }

        // Wait before retry
        console.log(
          `Retry attempt ${attempt + 1}/${maxRetries} after ${backoffMs}ms`
        );
        await sleep(backoffMs);

        // Exponential backoff
        backoffMs = Math.min(backoffMs * 2, maxBackoffMs);
      }
    }

    throw lastError;
  }
}

/**
 * Sleep utility
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * SSE Stream parser for OpenAI-compatible APIs
 */
export class SSEParser {
  /**
   * Parse SSE stream and extract content
   */
  static parseStream(sseData: string): string {
    const chunks = sseData.split('\n\n');
    let fullContent = '';

    for (const chunk of chunks) {
      if (!chunk.startsWith('data: ')) {
        continue;
      }

      const content = this.parseChunk(chunk);
      if (content) {
        fullContent += content;
      }
    }

    return fullContent;
  }

  /**
   * Parse single SSE chunk
   */
  static parseChunk(sseChunk: string): string | null {
    const json = sseChunk.substring(6); // Remove "data: " prefix

    if (json.trim() === '[DONE]') {
      return null;
    }

    try {
      const data = JSON.parse(json);
      const choices = data.choices;

      if (choices && choices.length > 0) {
        const delta = choices[0].delta;
        if (delta && delta.content) {
          return delta.content;
        }
      }
    } catch (err) {
      // Ignore parse errors
    }

    return null;
  }

  /**
   * Parse SSE stream as async generator
   */
  static async *parseStreamAsync(
    sseData: string
  ): AsyncGenerator<string, void, unknown> {
    const chunks = sseData.split('\n\n');

    for (const chunk of chunks) {
      if (!chunk.startsWith('data: ')) {
        continue;
      }

      const content = this.parseChunk(chunk);
      if (content) {
        yield content;
      }
    }
  }
}


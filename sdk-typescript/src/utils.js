"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SSEParser = exports.RetryHelper = exports.HTTPResponseHelper = void 0;
exports.sleep = sleep;
/**
 * HTTP Response utilities
 */
class HTTPResponseHelper {
    /**
     * Check if response is 2xx
     */
    static is2xx(response) {
        return response.statusCode >= 200 && response.statusCode < 300;
    }
    /**
     * Check if response is 3xx
     */
    static is3xx(response) {
        return response.statusCode >= 300 && response.statusCode < 400;
    }
    /**
     * Check if response is 4xx
     */
    static is4xx(response) {
        return response.statusCode >= 400 && response.statusCode < 500;
    }
    /**
     * Check if response is 5xx
     */
    static is5xx(response) {
        return response.statusCode >= 500 && response.statusCode < 600;
    }
    /**
     * Get response body as string
     */
    static getBodyAsString(response) {
        return response.body.toString('utf-8');
    }
    /**
     * Get response body as JSON
     */
    static getBodyAsJSON(response) {
        const str = this.getBodyAsString(response);
        return JSON.parse(str);
    }
    /**
     * Get header value (case-insensitive)
     */
    static getHeader(response, name) {
        const lowerName = name.toLowerCase();
        for (const [key, value] of Object.entries(response.headers)) {
            if (key.toLowerCase() === lowerName) {
                return value;
            }
        }
        return undefined;
    }
}
exports.HTTPResponseHelper = HTTPResponseHelper;
/**
 * Retry utility with exponential backoff
 */
class RetryHelper {
    /**
     * Execute function with retry logic
     */
    static async withRetry(fn, options = {}) {
        const { maxRetries = 3, initialBackoffMs = 1000, maxBackoffMs = 30000, retryableErrors = ['Transient', 'RateLimited', 'Timeout'], } = options;
        let lastError = null;
        let backoffMs = initialBackoffMs;
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                return await fn();
            }
            catch (err) {
                lastError = err;
                // Check if error is retryable
                const errorStr = err.toString();
                const isRetryable = retryableErrors.some((errorType) => errorStr.includes(errorType));
                if (!isRetryable || attempt === maxRetries) {
                    throw err;
                }
                // Wait before retry
                console.log(`Retry attempt ${attempt + 1}/${maxRetries} after ${backoffMs}ms`);
                await sleep(backoffMs);
                // Exponential backoff
                backoffMs = Math.min(backoffMs * 2, maxBackoffMs);
            }
        }
        throw lastError;
    }
}
exports.RetryHelper = RetryHelper;
/**
 * Sleep utility
 */
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
/**
 * SSE Stream parser for OpenAI-compatible APIs
 */
class SSEParser {
    /**
     * Parse SSE stream and extract content
     */
    static parseStream(sseData) {
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
    static parseChunk(sseChunk) {
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
        }
        catch (err) {
            // Ignore parse errors
        }
        return null;
    }
    /**
     * Parse SSE stream as async generator
     */
    static async *parseStreamAsync(sseData) {
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
exports.SSEParser = SSEParser;

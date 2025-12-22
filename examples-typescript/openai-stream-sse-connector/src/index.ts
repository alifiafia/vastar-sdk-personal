import * as fs from 'fs';
import * as yaml from 'yaml';
import {
  RuntimeClient,
  HTTPResponseHelper,
  SSEParser,
  ConnectorException,
} from '../../../sdk-typescript/dist';

/**
 * Configuration interface
 */
interface Config {
  openai: {
    api_key: string;
    base_url: string;
    model: string;
    timeout_ms: number;
  };
  runtime: {
    tenant_id: string;
    workspace_id: string;
    timeout_ms: number;
  };
  simulator: {
    enabled: boolean;
    base_url: string;
  };
}

/**
 * OpenAI Stream SSE Connector
 */
class OpenAIStreamConnector {
  private client: RuntimeClient;
  private config: Config;

  constructor(configPath: string = 'config.yaml') {
    // Load configuration
    this.config = this.loadConfig(configPath);

    // Check for environment override
    if (process.env.USE_SIMULATOR === 'true') {
      this.config.simulator.enabled = true;
    } else if (process.env.USE_SIMULATOR === 'false') {
      this.config.simulator.enabled = false;
    }

    // Create runtime client
    this.client = new RuntimeClient({
      tenantId: this.config.runtime.tenant_id,
      workspaceId: this.config.runtime.workspace_id,
      timeoutMs: this.config.runtime.timeout_ms,
    });
  }

  /**
   * Load configuration from YAML file
   */
  private loadConfig(configPath: string): Config {
    const fileContent = fs.readFileSync(configPath, 'utf-8');
    const config = yaml.parse(fileContent) as Config;

    // Resolve environment variables
    config.openai.api_key = this.resolveEnvVar(config.openai.api_key);

    return config;
  }

  /**
   * Resolve environment variable
   */
  private resolveEnvVar(value: string): string {
    if (value.startsWith('${') && value.endsWith('}')) {
      const envVar = value.substring(2, value.length - 1);
      return process.env[envVar] || '';
    }
    return value;
  }

  /**
   * Get API key
   */
  private getApiKey(): string {
    return this.config.openai.api_key;
  }

  /**
   * Get base URL (simulator or real OpenAI)
   */
  private getBaseUrl(): string {
    return this.config.simulator.enabled
      ? this.config.simulator.base_url
      : this.config.openai.base_url;
  }

  /**
   * Connect to runtime
   */
  async connect(): Promise<void> {
    await this.client.connect();
  }

  /**
   * Test connection to OpenAI or simulator
   */
  async testConnection(): Promise<void> {
    console.log('📡 Testing connection...');
    console.log(`   URL: ${this.getBaseUrl()}/v1/chat/completions`);

    const payload = {
      model: this.config.openai.model,
      messages: [{ role: 'user', content: 'Test connection' }],
      stream: false,
      max_tokens: 10,
    };

    try {
      const response = await this.client.executeHTTP({
        method: 'POST',
        url: `${this.getBaseUrl()}/v1/chat/completions`,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getApiKey()}`,
        },
        body: JSON.stringify(payload),
        timeoutMs: 10000,
      });

      if (HTTPResponseHelper.is2xx(response)) {
        const bodyStr = HTTPResponseHelper.getBodyAsString(response);

        // Check if response is SSE format
        if (bodyStr.startsWith('data:')) {
          console.log('✅ Connection successful! (SSE stream detected)');
          console.log(`   Response preview: ${bodyStr.substring(0, 100)}...`);
        } else {
          // Regular JSON response
          const data = JSON.parse(bodyStr);
          console.log('✅ Connection successful!');
          console.log(`   Response: ${JSON.stringify(data).substring(0, 100)}...`);
        }
      } else {
        console.error('❌ Connection failed:', response.statusCode);
      }
    } catch (err) {
      console.error('❌ Connection error:', err);
      throw err;
    }
  }

  /**
   * Send streaming chat completion request
   */
  async streamingChatCompletion(userMessage: string): Promise<string> {
    const payload = {
      model: this.config.openai.model,
      messages: [{ role: 'user', content: userMessage }],
      stream: true,
    };

    const response = await this.client.executeHTTP({
      method: 'POST',
      url: `${this.getBaseUrl()}/v1/chat/completions`,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.getApiKey()}`,
      },
      body: JSON.stringify(payload),
      timeoutMs: this.config.openai.timeout_ms,
    });

    if (!HTTPResponseHelper.is2xx(response)) {
      throw new Error(
        `API error: ${response.statusCode} - ${HTTPResponseHelper.getBodyAsString(
          response
        )}`
      );
    }

    // Parse SSE stream
    const sseData = HTTPResponseHelper.getBodyAsString(response);
    return SSEParser.parseStream(sseData);
  }

  /**
   * Send non-streaming chat completion request
   */
  async chatCompletion(userMessage: string): Promise<string> {
    const payload = {
      model: this.config.openai.model,
      messages: [{ role: 'user', content: userMessage }],
      stream: false,
    };

    const response = await this.client.executeHTTP({
      method: 'POST',
      url: `${this.getBaseUrl()}/v1/chat/completions`,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.getApiKey()}`,
      },
      body: JSON.stringify(payload),
      timeoutMs: this.config.openai.timeout_ms,
    });

    if (!HTTPResponseHelper.is2xx(response)) {
      throw new Error(
        `API error: ${response.statusCode} - ${HTTPResponseHelper.getBodyAsString(
          response
        )}`
      );
    }

    // Check response format (SSE or JSON)
    const bodyStr = HTTPResponseHelper.getBodyAsString(response);

    if (bodyStr.startsWith('data:')) {
      // Simulator returns SSE even for non-streaming, parse it
      return SSEParser.parseStream(bodyStr);
    } else {
      // Regular JSON response (real OpenAI API)
      const data: any = JSON.parse(bodyStr);
      return data.choices[0].message.content;
    }
  }

  /**
   * Close connection
   */
  async close(): Promise<void> {
    await this.client.close();
  }
}

/**
 * Main demo function
 */
async function main() {
  console.log('🤖 OpenAI Stream SSE Connector Demo');
  console.log('═════════════════════════════════════════════════════');
  console.log('');

  const connector = new OpenAIStreamConnector();

  try {
    // Display mode
    const mode = connector['config'].simulator.enabled
      ? '🧪 Using RAI Simulator'
      : '🌐 Using Real OpenAI API';
    console.log(mode);
    console.log(`🔗 Base URL: ${connector['getBaseUrl']()}`);
    console.log('');

    // Connect
    await connector.connect();

    // Test connection
    await connector.testConnection();
    console.log('');

    // Example 1: Streaming chat completion
    console.log('Example 1: Streaming Chat Completion');
    console.log('─────────────────────────────────────────────────────────────');
    console.log('User: Explain quantum computing in simple terms.');
    console.log('AI: ');

    const streamResponse = await connector.streamingChatCompletion(
      'Explain quantum computing in simple terms.'
    );
    console.log(streamResponse);
    console.log('─────────────────────────────────────────────────────────────');
    console.log(`📊 Total response length: ${streamResponse.length} characters`);
    console.log('');

    // Example 2: Non-streaming chat completion
    console.log('Example 2: Non-Streaming Chat Completion');
    console.log('─────────────────────────────────────────────────────────────');
    console.log('User: What is the capital of France?');
    console.log('AI: ');

    const response = await connector.chatCompletion('What is the capital of France?');
    console.log(response);
    console.log('');

    // Example 3: Multiple sequential requests
    console.log('Example 3: Sequential Requests');
    console.log('─────────────────────────────────────────────────────────────');

    const questions = [
      'What is TypeScript?',
      'What is Node.js?',
      'What is async/await?',
    ];

    for (const question of questions) {
      console.log(`Q: ${question}`);
      const answer = await connector.chatCompletion(question);
      console.log(`A: ${answer.substring(0, 100)}...`);
      console.log('');
    }

    console.log('═════════════════════════════════════════════════════');
    console.log('✅ All examples completed successfully!');

  } catch (err) {
    if (err instanceof ConnectorException) {
      console.error('❌ Connector Error:', {
        requestId: err.requestId,
        errorClass: err.getErrorClassName(),
        message: err.message,
      });
    } else {
      console.error('❌ Error:', err);
    }
    process.exit(1);
  } finally {
    await connector.close();
  }
}

// Run main function
if (require.main === module) {
  main().catch((err) => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

export { OpenAIStreamConnector };


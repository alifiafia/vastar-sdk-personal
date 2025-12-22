package io.vastar.examples.openai;

import io.vastar.connector.sdk.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.yaml.snakeyaml.Yaml;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Map;

/**
 * OpenAI Stream SSE Connector Example
 *
 * Demonstrates streaming chat completions using Vastar Connector SDK.
 * Supports both RAI Simulator and real OpenAI API.
 */
public class OpenAIStreamConnector implements AutoCloseable {
    private static final Logger logger = LoggerFactory.getLogger(OpenAIStreamConnector.class);

    private final Config config;
    private final RuntimeClient client;

    public OpenAIStreamConnector(Config config) throws IOException {
        this.config = config;
        this.client = RuntimeClient.builder()
            .tenantId(config.runtime.tenantId)
            .workspaceId(config.runtime.workspaceId)
            .timeoutMs(config.getTimeoutMs())
            .build();
    }

    public static void main(String[] args) {
        logger.info("🤖 OpenAI Stream Connector Demo");
        logger.info("═════════════════════════════════════════════════════");

        try {
            // Load configuration
            Config config = loadConfig();

            // Check environment override
            String useRealOpenAI = System.getenv("USE_REAL_OPENAI");
            if (useRealOpenAI != null) {
                config.useRealOpenai = Boolean.parseBoolean(useRealOpenAI);
            }

            // Display configuration
            if (config.useRealOpenai) {
                logger.info("🌐 Using Real OpenAI API");
                logger.info("🔗 Base URL: {}", config.openai.baseUrl);
                String apiKey = config.openai.apiKey;
                if (apiKey != null && apiKey.length() > 10) {
                    logger.info("🔑 API Key: {}...{}",
                        apiKey.substring(0, 7),
                        apiKey.substring(apiKey.length() - 4));
                }
            } else {
                logger.info("🧪 Using RAI Simulator");
                logger.info("🔗 Base URL: {}", config.simulator.baseUrl);
            }

            logger.info("");

            try (OpenAIStreamConnector connector = new OpenAIStreamConnector(config)) {
                // Run examples
                connector.runExamples();
            }

            logger.info("");
            logger.info("═════════════════════════════════════════════════════");
            logger.info("✅ All examples completed successfully!");

        } catch (Exception e) {
            logger.error("❌ Error: {}", e.getMessage(), e);
            System.exit(1);
        }
    }

    private void runExamples() throws Exception {
        // Test connection first (only for simulator)
        if (!config.useRealOpenai) {
            testConnection();
        }

        // Example 1: Streaming Chat Completion
        example1_StreamingChatCompletion();

        // Example 2: Non-streaming Chat Completion
        example2_NonStreamingChatCompletion();

        // Example 3: Interactive Chat
        example3_InteractiveChat();
    }

    private void testConnection() throws Exception {
        logger.info("📡 Testing connection to OpenAI Simulator...");

        String url = config.getBaseUrl() + "/test_completion";
        logger.info("   URL: {}", url);

        // Add empty JSON body for POST request
        HTTPRequest request = HTTPRequest.builder()
            .method("POST")
            .url(url)
            .header("Content-Type", "application/json")
            .body("{}")
            .timeoutMs(10000)
            .tenantId(config.runtime.tenantId)
            .workspaceId(config.runtime.workspaceId)
            .build();

        logger.info("   Sending request via Vastar Runtime...");

        try {
            logger.info("   Calling client.executeHTTP()...");
            HTTPResponse response = client.executeHTTP(request);

            logger.info("   Response received!");
            logger.info("   Status: {}", response.getStatusCode());

            if (!response.is2xx()) {
                logger.error("❌ Connection test failed: {}", response.getStatusCode());
                logger.error("");
                logger.error("⚠️  RAI Endpoint Simulator is not running!");
                logger.error("");
                logger.error("To run this example, you need RAI Endpoint Simulator:");
                logger.error("1. Docker: docker run -d -p 4545:4545 rai-endpoint-simulator:latest");
                logger.error("2. Or from source: cd rai-endpoint-simulator && cargo run");
                logger.error("");
                System.exit(1);
            }

            // Parse test response
            String testMessage = parseTestResponse(response.getBodyAsString());
            logger.info("✅ {}", testMessage);
            logger.info("");

        } catch (Exception e) {
            logger.error("❌ Connection test failed: {}", e.getMessage());
            e.printStackTrace();
            throw e;
        }
    }

    private String parseTestResponse(String json) {
        try {
            com.google.gson.Gson gson = new com.google.gson.Gson();
            java.util.Map<String, Object> data = gson.fromJson(json,
                new com.google.gson.reflect.TypeToken<java.util.Map<String, Object>>(){}.getType());

            @SuppressWarnings("unchecked")
            java.util.List<java.util.Map<String, Object>> choices =
                (java.util.List<java.util.Map<String, Object>>) data.get("choices");

            if (choices != null && !choices.isEmpty()) {
                @SuppressWarnings("unchecked")
                java.util.Map<String, Object> message =
                    (java.util.Map<String, Object>) choices.get(0).get("message");
                return (String) message.get("content");
            }
        } catch (Exception e) {
            // Return raw response if parsing fails
        }
        return json;
    }

    private void example1_StreamingChatCompletion() throws Exception {
        logger.info("Example 1: Streaming Chat Completion");
        logger.info("─────────────────────────────────────────────────────────────");

        ChatRequest chatRequest = ChatRequest.builder()
            .model(config.getModel())
            .addMessage("user", "Explain quantum computing in simple terms.")
            .stream(true)
            .maxTokens(500)
            .temperature(0.7)
            .build();

        logger.info("User: Explain quantum computing in simple terms.");
        logger.info("AI: ");

        String response = sendChatRequest(chatRequest);
        logger.info(response);
        logger.info("─────────────────────────────────────────────────────────────");
        logger.info("📊 Total response length: {} characters", response.length());
        logger.info("");
    }

    private void example2_NonStreamingChatCompletion() throws Exception {
        logger.info("Example 2: Non-Streaming Chat Completion");
        logger.info("─────────────────────────────────────────────────────────────");

        ChatRequest chatRequest = ChatRequest.builder()
            .model(config.getModel())
            .addMessage("user", "What is the capital of France?")
            .stream(true)
            .maxTokens(100)
            .build();

        logger.info("User: What is the capital of France?");
        logger.info("AI: ");

        String response = sendChatRequest(chatRequest);
        logger.info(response);
        logger.info("");
    }

    private void example3_InteractiveChat() throws Exception {
        logger.info("Example 3: Interactive Chat");
        logger.info("─────────────────────────────────────────────────────────────");
        logger.info("Type 'quit' to exit");
        logger.info("");

        ChatRequest.Builder builder = ChatRequest.builder()
            .model(config.getModel())
            .stream(true)
            .maxTokens(200)
            .temperature(0.8);

        // Add system message
        builder.addMessage("system", "You are a helpful AI assistant.");

        // Simulate a few interactions
        String[] questions = {
            "Hello! How are you?",
            "What can you help me with?",
            "Tell me a fun fact about space."
        };

        for (String question : questions) {
            logger.info("You: {}", question);

            builder.addMessage("user", question);

            logger.info("AI: ");
            String response = sendChatRequest(builder.build());
            logger.info(response);

            // Add assistant response to history for next turn
            builder.addMessage("assistant", response);

            logger.info("");

            // Small delay between questions
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    private String sendChatRequest(ChatRequest chatRequest) throws Exception {
        String url = config.getBaseUrl() + "/v1/chat/completions";
        String jsonBody = chatRequest.toJSON();

        HTTPRequest request = HTTPRequest.builder()
            .method("POST")
            .url(url)
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer " + config.getApiKey())
            .body(jsonBody)
            .timeoutMs(config.getTimeoutMs())
            .tenantId(config.runtime.tenantId)
            .workspaceId(config.runtime.workspaceId)
            .build();

        HTTPResponse response = client.executeHTTP(request);

        if (!response.is2xx()) {
            throw new Exception("Request failed with status " + response.getStatusCode() +
                ": " + response.getBodyAsString());
        }

        return ChatResponse.parseResponse(response.getBodyAsString());
    }

    private static Config loadConfig() throws IOException {
        Yaml yaml = new Yaml();
        try (InputStream input = new FileInputStream("config.yaml")) {
            Map<String, Object> data = yaml.load(input);
            return Config.fromMap(data);
        }
    }

    @Override
    public void close() throws IOException {
        if (client != null) {
            client.close();
        }
    }

    // Configuration classes
    static class Config {
        boolean useRealOpenai;
        OpenAIConfig openai;
        SimulatorConfig simulator;
        RuntimeConfig runtime;

        @SuppressWarnings("unchecked")
        static Config fromMap(Map<String, Object> data) {
            Config config = new Config();
            config.useRealOpenai = (Boolean) data.get("use_real_openai");

            Map<String, Object> openaiData = (Map<String, Object>) data.get("openai");
            config.openai = new OpenAIConfig();
            config.openai.apiKey = expandEnvVar((String) openaiData.get("api_key"));
            config.openai.baseUrl = (String) openaiData.get("base_url");
            config.openai.model = (String) openaiData.get("model");
            config.openai.timeoutMs = (Integer) openaiData.get("timeout_ms");

            Map<String, Object> simData = (Map<String, Object>) data.get("simulator");
            config.simulator = new SimulatorConfig();
            config.simulator.baseUrl = (String) simData.get("base_url");
            config.simulator.timeoutMs = (Integer) simData.get("timeout_ms");

            Map<String, Object> runtimeData = (Map<String, Object>) data.get("runtime");
            config.runtime = new RuntimeConfig();
            config.runtime.socketPath = (String) runtimeData.get("socket_path");
            config.runtime.tenantId = (String) runtimeData.get("tenant_id");
            config.runtime.workspaceId = (String) runtimeData.get("workspace_id");

            return config;
        }

        private static String expandEnvVar(String value) {
            if (value == null) return null;
            if (value.startsWith("${") && value.endsWith("}")) {
                String envVar = value.substring(2, value.length() - 1);
                return System.getenv(envVar);
            }
            return value;
        }

        String getBaseUrl() {
            return useRealOpenai ? openai.baseUrl : simulator.baseUrl;
        }

        String getApiKey() {
            return useRealOpenai ? openai.apiKey : "dummy-key";
        }

        String getModel() {
            return useRealOpenai ? openai.model : "gpt-3.5-turbo";
        }

        int getTimeoutMs() {
            return useRealOpenai ? openai.timeoutMs : simulator.timeoutMs;
        }
    }

    static class OpenAIConfig {
        String apiKey;
        String baseUrl;
        String model;
        int timeoutMs;
    }

    static class SimulatorConfig {
        String baseUrl;
        int timeoutMs;
    }

    static class RuntimeConfig {
        String socketPath;
        String tenantId;
        String workspaceId;
    }
}


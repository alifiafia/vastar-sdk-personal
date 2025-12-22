# Using Vastar Connector Java SDK

**Complete Guide for Building Connectors with Java SDK**

This document explains how to use the Vastar Connector Java SDK to build custom connectors, using the OpenAI Stream SSE Connector as a practical example.

---

## 📚 Table of Contents

1. [SDK Overview](#sdk-overview)
2. [Setup & Dependencies](#setup--dependencies)
3. [Basic Usage](#basic-usage)
4. [Building HTTP Requests](#building-http-requests)
5. [Processing Responses](#processing-responses)
6. [SSE Stream Handling](#sse-stream-handling)
7. [Error Handling](#error-handling)
8. [Configuration Management](#configuration-management)
9. [Complete Example Walkthrough](#complete-example-walkthrough)
10. [Best Practices](#best-practices)

---

## SDK Overview

### What is Vastar Connector SDK?

The Vastar Connector SDK provides a Java library for building connectors that communicate with external APIs through the Vastar Connector Runtime. The SDK handles:

- **IPC Communication** - FlatBuffers-based protocol over Unix Socket/TCP
- **HTTP Requests** - Type-safe HTTP request/response handling
- **Connection Management** - Automatic connection pooling and retry
- **Error Handling** - Comprehensive exception handling
- **Type Safety** - Builder patterns and strongly-typed APIs

### Architecture

```
┌──────────────────────────────────────────────────────┐
│           Your Java Connector Application            │
│                                                       │
│  ┌─────────────────┐                                 │
│  │  Main.java      │  Your connector logic           │
│  │  - Config       │                                 │
│  │  - Business     │                                 │
│  │  - Logic        │                                 │
│  └────────┬────────┘                                 │
│           │                                           │
│           │ Uses                                      │
│           ▼                                           │
│  ┌─────────────────────────────────────────────┐    │
│  │  Vastar Connector Java SDK                  │    │
│  │  - RuntimeClient (IPC)                      │    │
│  │  - HTTPRequest (Builder)                    │    │
│  │  - HTTPResponse (Parser)                    │    │
│  └────────┬────────────────────────────────────┘    │
└───────────┼──────────────────────────────────────────┘
            │ IPC Protocol
            │ (FlatBuffers)
            ▼
┌───────────────────────────────────────────────────────┐
│        Vastar Connector Runtime (Daemon)              │
│  - HTTP Transport Pack (SSE Streaming)                │
│  - Connection Pooling                                 │
│  - Circuit Breaker & Retry                            │
└───────────────────────────────────────────────────────┘
```

---

## Setup & Dependencies

### Step 1: Add SDK JAR to Project

Copy the SDK JAR to your project's `libs/` directory:

```bash
cp ../../sdk-java/build/libs/vastar-connector-sdk-java-0.1.0.jar libs/
```

### Step 2: Configure Gradle

**build.gradle.kts:**

```kotlin
dependencies {
    // Vastar Connector SDK
    implementation(files("libs/vastar-connector-sdk-java-0.1.0.jar"))
    
    // Required dependencies
    implementation("com.google.flatbuffers:flatbuffers-java:2.0.8")
    implementation("org.slf4j:slf4j-api:1.7.36")
    implementation("ch.qos.logback:logback-classic:1.2.11")
    
    // Optional: For JSON processing
    implementation("com.google.code.gson:gson:2.10.1")
    
    // Optional: For YAML config
    implementation("org.yaml:snakeyaml:2.0")
}
```

### Step 3: Verify Runtime is Running

```bash
# Check if runtime is running
pgrep vastar-connector-runtime

# Check if socket exists
ls -la /tmp/vastar-connector-runtime.sock

# Start runtime if needed
./start_runtime.sh
```

---

## Basic Usage

### Creating a RuntimeClient

The `RuntimeClient` is the main entry point for communicating with the Vastar Runtime.

#### Simple Creation

```java
import io.vastar.connector.sdk.*;

// Default configuration
RuntimeClient client = RuntimeClient.createDefault();
```

#### Using Builder Pattern

```java
RuntimeClient client = RuntimeClient.builder()
    .tenantId("my-tenant")
    .workspaceId("workspace-123")
    .timeoutMs(60000)  // 60 seconds
    .build();
```

#### With Auto-Close (Recommended)

```java
try (RuntimeClient client = RuntimeClient.builder()
        .tenantId("openai-connector")
        .build()) {
    
    // Use client here
    HTTPResponse response = client.executeHTTP(request);
    
} // Client automatically closed
```

### Making Your First HTTP Request

```java
import io.vastar.connector.sdk.*;

public class SimpleExample {
    public static void main(String[] args) {
        try (RuntimeClient client = RuntimeClient.createDefault()) {
            
            // Build request
            HTTPRequest request = HTTPRequest.builder()
                .method("GET")
                .url("https://api.github.com/zen")
                .header("Accept", "application/json")
                .build();
            
            // Execute request
            HTTPResponse response = client.executeHTTP(request);
            
            // Check response
            if (response.is2xx()) {
                System.out.println("Success: " + response.getBodyAsString());
            } else {
                System.err.println("Error: " + response.getStatusCode());
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

---

## Building HTTP Requests

### HTTPRequest Builder

The `HTTPRequest` class uses a builder pattern for constructing requests:

```java
HTTPRequest request = HTTPRequest.builder()
    .method("POST")                              // HTTP method (required)
    .url("https://api.example.com/endpoint")     // URL (required)
    .header("Content-Type", "application/json")  // Add headers (optional)
    .header("Authorization", "Bearer token")     
    .body("{\"key\": \"value\"}")                // Request body (optional)
    .timeoutMs(30000)                            // Timeout (optional)
    .tenantId("custom-tenant")                   // Override tenant (optional)
    .build();
```

### Common Patterns

#### GET Request with Headers

```java
HTTPRequest request = HTTPRequest.builder()
    .method("GET")
    .url("https://api.example.com/users/123")
    .header("Accept", "application/json")
    .header("User-Agent", "MyConnector/1.0")
    .build();
```

#### POST Request with JSON Body

```java
import com.google.gson.Gson;

// Create JSON payload
Map<String, Object> payload = Map.of(
    "name", "John Doe",
    "email", "john@example.com"
);
String jsonBody = new Gson().toJson(payload);

HTTPRequest request = HTTPRequest.builder()
    .method("POST")
    .url("https://api.example.com/users")
    .header("Content-Type", "application/json")
    .body(jsonBody)
    .build();
```

#### Request with Custom Timeout

```java
HTTPRequest request = HTTPRequest.builder()
    .method("POST")
    .url("https://api.example.com/slow-operation")
    .body(data)
    .timeoutMs(120000)  // 2 minutes for slow operation
    .build();
```

---

## Processing Responses

### HTTPResponse Object

The `HTTPResponse` provides methods to access response data:

```java
HTTPResponse response = client.executeHTTP(request);

// Status code
int status = response.getStatusCode();

// Check status ranges
boolean success = response.is2xx();    // 200-299
boolean redirect = response.is3xx();   // 300-399
boolean clientError = response.is4xx(); // 400-499
boolean serverError = response.is5xx(); // 500-599

// Headers
Map<String, String> headers = response.getHeaders();
String contentType = headers.get("Content-Type");

// Body
String bodyText = response.getBodyAsString();
byte[] bodyBytes = response.getBodyAsBytes();

// Metadata
long requestId = response.getRequestId();
long durationMicros = response.getDurationUs();
```

### Processing JSON Response

```java
import com.google.gson.Gson;
import com.google.gson.JsonObject;

HTTPResponse response = client.executeHTTP(request);

if (response.is2xx()) {
    String json = response.getBodyAsString();
    JsonObject data = new Gson().fromJson(json, JsonObject.class);
    
    String userId = data.get("id").getAsString();
    String username = data.get("username").getAsString();
    
    System.out.println("User: " + username + " (ID: " + userId + ")");
}
```

### Handling Different Response Types

```java
HTTPResponse response = client.executeHTTP(request);

switch (response.getStatusCode()) {
    case 200:
        // Success
        processSuccessResponse(response);
        break;
    case 201:
        // Created
        System.out.println("Resource created");
        break;
    case 400:
        // Bad request
        System.err.println("Invalid request: " + response.getBodyAsString());
        break;
    case 401:
        // Unauthorized
        System.err.println("Authentication required");
        break;
    case 404:
        // Not found
        System.err.println("Resource not found");
        break;
    case 500:
        // Server error
        System.err.println("Server error occurred");
        break;
    default:
        System.err.println("Unexpected status: " + response.getStatusCode());
}
```

---

## SSE Stream Handling

### Understanding SSE Format

Server-Sent Events (SSE) is a streaming format used by APIs like OpenAI:

```
data: {"id":"123","delta":{"content":"Hello"}}

data: {"id":"123","delta":{"content":" world"}}

data: [DONE]
```

### Parsing SSE Stream in Java

The runtime automatically collects the full SSE stream. You need to parse it:

```java
public class SSEParser {
    public static String parseSSEStream(String sseStream) {
        StringBuilder fullContent = new StringBuilder();
        
        // Split by double newlines
        String[] chunks = sseStream.split("\n\n");
        
        for (String chunk : chunks) {
            if (!chunk.startsWith("data: ")) {
                continue;
            }
            
            String content = parseChunk(chunk);
            if (content != null) {
                fullContent.append(content);
            }
        }
        
        return fullContent.toString();
    }
    
    private static String parseChunk(String sseChunk) {
        // Remove "data: " prefix
        String json = sseChunk.substring(6);
        
        // Check for end marker
        if ("[DONE]".equals(json.trim())) {
            return null;
        }
        
        try {
            JsonObject data = JsonParser.parseString(json).getAsJsonObject();
            JsonArray choices = data.getAsJsonArray("choices");
            
            if (choices != null && choices.size() > 0) {
                JsonObject choice = choices.get(0).getAsJsonObject();
                JsonObject delta = choice.getAsJsonObject("delta");
                
                if (delta != null && delta.has("content")) {
                    return delta.get("content").getAsString();
                }
            }
        } catch (Exception e) {
            // Ignore parse errors
        }
        
        return null;
    }
}
```

### Using SSE Parser in Connector

```java
public class OpenAIConnector {
    private final RuntimeClient client;
    
    public String streamingChat(String userMessage) throws Exception {
        // Build request
        HTTPRequest request = HTTPRequest.builder()
            .method("POST")
            .url("https://api.openai.com/v1/chat/completions")
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer " + apiKey)
            .body(buildChatPayload(userMessage, true))  // stream=true
            .build();
        
        // Execute
        HTTPResponse response = client.executeHTTP(request);
        
        if (!response.is2xx()) {
            throw new Exception("API error: " + response.getStatusCode());
        }
        
        // Parse SSE stream
        String sseData = response.getBodyAsString();
        return SSEParser.parseSSEStream(sseData);
    }
}
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── IOException (connection/IPC errors)
└── ConnectorException (business logic errors)
    ├── requestId: long
    ├── errorClass: ErrorClass
    └── message: String
```

### Handling ConnectorException

```java
import io.vastar.connector.sdk.*;
import Vastar.Connector.Ipc.ErrorClass;

try {
    HTTPResponse response = client.executeHTTP(request);
    // Process response
    
} catch (ConnectorException e) {
    long requestId = e.getRequestId();
    byte errorClass = e.getErrorClass();
    String message = e.getMessage();
    
    switch (errorClass) {
        case ErrorClass.Transient:
            // Network hiccup, retry recommended
            logger.warn("Transient error (req: {}): {}", requestId, message);
            retryRequest(request);
            break;
            
        case ErrorClass.RateLimited:
            // Too many requests
            logger.warn("Rate limited (req: {})", requestId);
            Thread.sleep(5000);
            retryRequest(request);
            break;
            
        case ErrorClass.Timeout:
            // Request took too long
            logger.error("Timeout (req: {}): {}", requestId, message);
            break;
            
        case ErrorClass.Permanent:
        case ErrorClass.InvalidRequest:
            // Don't retry these
            logger.error("Permanent error (req: {}): {}", requestId, message);
            break;
    }
    
} catch (IOException e) {
    // Connection to runtime failed
    logger.error("Communication error: {}", e.getMessage());
}
```

### Retry Pattern

```java
public HTTPResponse executeWithRetry(
        RuntimeClient client,
        HTTPRequest request,
        int maxRetries) throws Exception {
    
    int attempt = 0;
    long backoffMs = 1000;
    
    while (true) {
        try {
            return client.executeHTTP(request);
            
        } catch (ConnectorException e) {
            attempt++;
            
            // Check if retryable
            if (e.getErrorClass() != ErrorClass.Transient &&
                e.getErrorClass() != ErrorClass.RateLimited) {
                throw e;  // Not retryable
            }
            
            if (attempt >= maxRetries) {
                throw new Exception("Max retries exceeded", e);
            }
            
            // Exponential backoff
            logger.info("Retry {}/{} after {}ms", attempt, maxRetries, backoffMs);
            Thread.sleep(backoffMs);
            backoffMs *= 2;
        }
    }
}
```

---

## Configuration Management

### Using YAML Configuration

**config.yaml:**

```yaml
# OpenAI API Configuration
openai:
  api_key: ${OPENAI_API_KEY}
  base_url: "https://api.openai.com"
  model: "gpt-3.5-turbo"
  timeout_ms: 60000

# Vastar Runtime Configuration
runtime:
  tenant_id: "openai-connector"
  workspace_id: "default"
  timeout_ms: 60000

# Simulator Configuration (for testing)
simulator:
  enabled: false
  base_url: "http://localhost:4545"
```

### Loading Configuration

```java
import org.yaml.snakeyaml.Yaml;
import java.io.FileInputStream;
import java.io.InputStream;

public class Config {
    public OpenAIConfig openai;
    public RuntimeConfig runtime;
    public SimulatorConfig simulator;
    
    public static class OpenAIConfig {
        public String api_key;
        public String base_url;
        public String model;
        public int timeout_ms;
    }
    
    public static class RuntimeConfig {
        public String tenant_id;
        public String workspace_id;
        public int timeout_ms;
    }
    
    public static class SimulatorConfig {
        public boolean enabled;
        public String base_url;
    }
    
    public static Config load(String configPath) throws IOException {
        Yaml yaml = new Yaml();
        try (InputStream input = new FileInputStream(configPath)) {
            return yaml.loadAs(input, Config.class);
        }
    }
    
    // Resolve environment variables
    public String getApiKey() {
        String key = openai.api_key;
        if (key.startsWith("${") && key.endsWith("}")) {
            String envVar = key.substring(2, key.length() - 1);
            return System.getenv(envVar);
        }
        return key;
    }
}
```

### Using Configuration

```java
public class OpenAIConnector {
    private final RuntimeClient client;
    private final Config config;
    
    public OpenAIConnector(String configPath) throws IOException {
        this.config = Config.load(configPath);
        this.client = RuntimeClient.builder()
            .tenantId(config.runtime.tenant_id)
            .workspaceId(config.runtime.workspace_id)
            .timeoutMs(config.runtime.timeout_ms)
            .build();
    }
    
    public HTTPResponse sendRequest(String endpoint, String body) throws Exception {
        String baseUrl = config.simulator.enabled 
            ? config.simulator.base_url 
            : config.openai.base_url;
        
        HTTPRequest request = HTTPRequest.builder()
            .method("POST")
            .url(baseUrl + endpoint)
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer " + config.getApiKey())
            .body(body)
            .timeoutMs(config.openai.timeout_ms)
            .build();
        
        return client.executeHTTP(request);
    }
}
```

---

## Complete Example Walkthrough

Let's walk through the complete OpenAI connector implementation step by step.

### Step 1: Project Structure

```
openai-stream-sse-connector/
├── src/main/java/io/vastar/examples/openai/
│   ├── OpenAIStreamConnector.java    # Main application
│   ├── ChatResponse.java             # SSE parser
│   └── Config.java                   # Configuration loader
├── config.yaml                        # Configuration file
├── config.example.yaml               # Example configuration
├── build.gradle.kts                  # Gradle build file
└── libs/
    └── vastar-connector-sdk-java-0.1.0.jar
```

### Step 2: Main Connector Class

**OpenAIStreamConnector.java:**

```java
package io.vastar.examples.openai;

import io.vastar.connector.sdk.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OpenAIStreamConnector {
    private static final Logger logger = LoggerFactory.getLogger(OpenAIStreamConnector.class);
    
    private final RuntimeClient client;
    private final Config config;
    
    public OpenAIStreamConnector(Config config) throws IOException {
        this.config = config;
        this.client = RuntimeClient.builder()
            .tenantId(config.runtime.tenantId)
            .workspaceId(config.runtime.workspaceId)
            .timeoutMs(config.runtime.timeoutMs)
            .build();
    }
    
    public String sendChatMessage(String message) throws Exception {
        // Determine base URL (simulator or real API)
        String baseUrl = config.simulator.enabled
            ? config.simulator.baseUrl
            : config.openai.baseUrl;
        
        // Build request payload
        String jsonBody = buildChatPayload(message);
        
        // Build HTTP request
        HTTPRequest request = HTTPRequest.builder()
            .method("POST")
            .url(baseUrl + "/v1/chat/completions")
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer " + config.getApiKey())
            .body(jsonBody)
            .timeoutMs(config.openai.timeoutMs)
            .build();
        
        // Execute request
        HTTPResponse response = client.executeHTTP(request);
        
        // Check status
        if (!response.is2xx()) {
            throw new Exception("API error: " + response.getStatusCode() 
                + " - " + response.getBodyAsString());
        }
        
        // Parse response
        return ChatResponse.parseResponse(response.getBodyAsString());
    }
    
    private String buildChatPayload(String message) {
        JsonObject payload = new JsonObject();
        payload.addProperty("model", config.openai.model);
        payload.addProperty("stream", true);
        
        JsonArray messages = new JsonArray();
        JsonObject msg = new JsonObject();
        msg.addProperty("role", "user");
        msg.addProperty("content", message);
        messages.add(msg);
        
        payload.add("messages", messages);
        return new Gson().toJson(payload);
    }
    
    public void close() throws IOException {
        client.close();
    }
    
    public static void main(String[] args) {
        try {
            Config config = Config.load("config.yaml");
            
            try (OpenAIStreamConnector connector = new OpenAIStreamConnector(config)) {
                String response = connector.sendChatMessage(
                    "Explain quantum computing in simple terms."
                );
                System.out.println("AI Response: " + response);
            }
            
        } catch (Exception e) {
            logger.error("Error: ", e);
        }
    }
}
```

### Step 3: Run the Example

```bash
# Set API key (if using real OpenAI)
export OPENAI_API_KEY="sk-..."

# Run with Gradle
./gradlew run

# Or run specific task
./gradlew runSimulator  # Use simulator
./gradlew runOpenAI     # Use real OpenAI API
```

---

## Best Practices

### 1. Always Use Try-With-Resources

```java
// GOOD: Automatic cleanup
try (RuntimeClient client = RuntimeClient.createDefault()) {
    HTTPResponse response = client.executeHTTP(request);
}

// BAD: Manual cleanup required
RuntimeClient client = RuntimeClient.createDefault();
HTTPResponse response = client.executeHTTP(request);
client.close();  // Might be forgotten
```

### 2. Reuse RuntimeClient

```java
// GOOD: One client for multiple requests
RuntimeClient client = RuntimeClient.createDefault();
for (String url : urls) {
    HTTPResponse response = client.executeHTTP(
        HTTPRequest.builder().url(url).build()
    );
}
client.close();

// BAD: Creating new client per request
for (String url : urls) {
    try (RuntimeClient client = RuntimeClient.createDefault()) {
        HTTPResponse response = client.executeHTTP(...);
    }
}
```

### 3. Set Appropriate Timeouts

```java
// Fast API - short timeout
HTTPRequest fastRequest = HTTPRequest.builder()
    .url("https://api.example.com/health")
    .timeoutMs(5000)  // 5 seconds
    .build();

// Slow operation - long timeout
HTTPRequest slowRequest = HTTPRequest.builder()
    .url("https://api.example.com/heavy-processing")
    .timeoutMs(300000)  // 5 minutes
    .build();
```

### 4. Handle All Error Cases

```java
try {
    HTTPResponse response = client.executeHTTP(request);
    
    if (response.is2xx()) {
        // Success
    } else if (response.is4xx()) {
        // Client error (bad request, auth, etc.)
    } else if (response.is5xx()) {
        // Server error (retry might help)
    }
    
} catch (ConnectorException e) {
    // Runtime-level errors
} catch (IOException e) {
    // Connection errors
}
```

### 5. Use Logging Effectively

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

private static final Logger logger = LoggerFactory.getLogger(MyConnector.class);

// Log with request ID
HTTPResponse response = client.executeHTTP(request);
logger.info("Request {} completed in {}μs", 
           response.getRequestId(), 
           response.getDurationUs());

// Log errors with context
catch (ConnectorException e) {
    logger.error("Request {} failed: {} (class: {})",
                e.getRequestId(),
                e.getMessage(),
                e.getErrorClass());
}
```

### 6. Externalize Configuration

```java
// GOOD: Configuration in file
Config config = Config.load("config.yaml");
String apiKey = config.getApiKey();

// BAD: Hardcoded values
String apiKey = "sk-hardcoded123";  // Never do this!
```

### 7. Validate Responses

```java
HTTPResponse response = client.executeHTTP(request);

// Validate status
if (!response.is2xx()) {
    throw new Exception("Request failed: " + response.getStatusCode());
}

// Validate content type
String contentType = response.getHeaders().get("Content-Type");
if (!contentType.contains("application/json")) {
    throw new Exception("Unexpected content type: " + contentType);
}

// Validate body is not empty
String body = response.getBodyAsString();
if (body == null || body.isEmpty()) {
    throw new Exception("Empty response body");
}
```

---

## Summary

This guide covered:

✅ **SDK Setup** - Adding dependencies and configuring Gradle  
✅ **Basic Usage** - Creating clients and making requests  
✅ **HTTP Requests** - Building requests with builder pattern  
✅ **Response Processing** - Handling different response types  
✅ **SSE Streaming** - Parsing Server-Sent Events  
✅ **Error Handling** - Exception handling and retry strategies  
✅ **Configuration** - YAML-based configuration management  
✅ **Complete Example** - Full OpenAI connector walkthrough  
✅ **Best Practices** - Production-ready patterns

### Next Steps

1. 📖 Read the [Java Developer Guide](../../sdk-java/docs/JAVA_DEVELOPER_GUIDE.md) for advanced topics
2. 🔍 Review the [RuntimeClient JavaDoc](../../sdk-java/build/docs/javadoc/) for API details
3. 💻 Study this example's source code in `src/main/java/`
4. 🚀 Build your own custom connector!

### Additional Resources

- **SDK Documentation**: `../../sdk-java/docs/`
- **Runtime Guide**: `../../connector-runtime/RUNTIME_INTEGRATION_GUIDE.md`
- **FlatBuffers Protocol**: `../../connector-runtime/FLATBUFFERS_IPC_COMPLETE.md`
- **Example Code**: `src/main/java/io/vastar/examples/openai/`

---

**For questions or issues**: See the main SDK documentation or contact support.


# 🤖 OpenAI Stream SSE Connector - Java

**Streaming Chat Completions with OpenAI-compatible API using Vastar Connector SDK**

[![Java Version](https://img.shields.io/badge/Java-17+-orange?style=flat&logo=java)](https://www.oracle.com/java/)
[![Gradle](https://img.shields.io/badge/Gradle-8.5-blue?style=flat&logo=gradle)](https://gradle.org/)

---

## 📚 Documentation

- **[Java SDK Usage Guide](JAVA_SDK_USAGE.md)** - Complete guide for using Vastar Connector Java SDK
- **[Java Developer Guide](../../sdk-java/docs/JAVA_DEVELOPER_GUIDE.md)** - Advanced topics and best practices
- **[JavaDoc API Reference](../../sdk-java/build/docs/javadoc/)** - Complete API documentation

---

## 📋 Overview

This example demonstrates how to build an OpenAI-compatible connector using the Vastar Connector SDK for Java. It supports both the RAI Endpoint Simulator and real OpenAI API.

### ✨ Features

- ✅ **Chat Completions** - Non-streaming mode
- ✅ **System Messages** - Custom system prompts
- ✅ **Multi-turn Conversations** - Conversation history
- ✅ **Configuration** - YAML-based configuration
- ✅ **Dual Mode** - Simulator or Real OpenAI
- ✅ **Error Handling** - Robust error handling
- ✅ **Type Safety** - Strongly typed Java classes

---

## 🚀 Quick Start

### Prerequisites

1. **Java 11+** - [Download](https://adoptium.net/)
2. **Vastar Runtime** - Must be running
3. **RAI Simulator** (for testing) or **OpenAI API Key** (for production)

### Step 1: Start Vastar Runtime

```bash
# From repository root
cd ../../..
./start_runtime.sh
```

### Step 2: Start RAI Simulator (Optional)

For testing with simulator:

```bash
docker run -d --name rai-simulator \
    -p 4545:4545 \
    rai-endpoint-simulator:latest
```

### Step 3: Configure

Copy example config:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

**For Simulator (default):**
```yaml
use_real_openai: false
```

**For Real OpenAI:**
```yaml
use_real_openai: true
openai:
  api_key: "sk-your-api-key-here"
```

Or set environment variable:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### Step 4: Run

**With Simulator:**
```bash
./gradlew runSimulator
```

**With Real OpenAI:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
./gradlew runOpenAI
```

**Default run (uses config.yaml):**
```bash
./gradlew run
```

---

## 📁 Project Structure

```
openai-stream-sse-connector/
├── build.gradle.kts          # Gradle build configuration
├── config.yaml                # Configuration (create from example)
├── config.example.yaml        # Example configuration
├── src/main/
│   ├── java/io/vastar/examples/openai/
│   │   ├── OpenAIStreamConnector.java  # Main application
│   │   ├── ChatRequest.java            # Request builder
│   │   └── ChatResponse.java           # Response parser
│   └── resources/
│       └── logback.xml                  # Logging configuration
└── README.md                  # This file
```

---

## 🔧 Configuration

### config.yaml

```yaml
# Use real OpenAI API or simulator
use_real_openai: false

# OpenAI API Configuration
openai:
  api_key: "${OPENAI_API_KEY}"  # Environment variable
  base_url: "https://api.openai.com"
  model: "gpt-3.5-turbo"
  timeout_ms: 30000

# RAI Simulator Configuration
simulator:
  base_url: "http://localhost:4545"
  timeout_ms: 10000

# Vastar Runtime Configuration
runtime:
  socket_path: "/tmp/vastar-connector-runtime.sock"
  tenant_id: "openai-demo"
  workspace_id: "demo-workspace"
```

### Environment Variables

```bash
# OpenAI API Key (required for real OpenAI)
export OPENAI_API_KEY="sk-..."

# Override use_real_openai from config
export USE_REAL_OPENAI=true

# Vastar Runtime socket (optional)
export VASTAR_SOCKET_PATH="/tmp/vastar-connector-runtime.sock"
```

---

## 📝 Code Examples

### Simple Chat Completion

```java
ChatRequest chatRequest = ChatRequest.builder()
    .model("gpt-3.5-turbo")
    .addMessage("user", "Explain quantum computing in simple terms.")
    .stream(false)
    .build();

String response = sendChatRequest(chatRequest);
System.out.println("AI: " + response);
```

### Chat with System Message

```java
ChatRequest chatRequest = ChatRequest.builder()
    .model("gpt-3.5-turbo")
    .addMessage("system", "You are a helpful assistant.")
    .addMessage("user", "What is a REST API?")
    .stream(false)
    .build();

String response = sendChatRequest(chatRequest);
```

### Multi-turn Conversation

```java
ChatRequest.Builder builder = ChatRequest.builder()
    .model("gpt-3.5-turbo");

// Turn 1
builder.addMessage("user", "What is Python?");
String response1 = sendChatRequest(builder.build());

// Turn 2 - continue conversation
builder.addMessage("assistant", response1);
builder.addMessage("user", "What are its main uses?");
String response2 = sendChatRequest(builder.build());
```

---

## 🧪 Running Examples

### Example 1: Simple Chat Completion

```bash
./gradlew runSimulator
```

Output:
```
🤖 OpenAI Stream Connector Demo
═════════════════════════════════════════════════════
🧪 Using RAI Simulator
🔗 Base URL: http://localhost:4545

━━━ Example 1: Simple Chat Completion ━━━
👤 User: Explain quantum computing in simple terms.
🤖 AI: Quantum computing uses quantum mechanics...
```

### Example 2: Real OpenAI

```bash
export OPENAI_API_KEY="sk-your-key"
./gradlew runOpenAI
```

---

## 🛠️ Build Commands

```bash
# Build
./gradlew build

# Run with simulator
./gradlew runSimulator

# Run with real OpenAI
./gradlew runOpenAI

# Run (uses config.yaml)
./gradlew run

# Clean
./gradlew clean
```

---

## 📚 Dependencies

This project uses:

- **Vastar Connector SDK** - From `../libs/vastar-connector-sdk-java-0.1.0-all.jar`
- **SLF4J + Logback** - For logging
- **SnakeYAML** - For configuration
- **Gson** - For JSON (included in SDK)

The SDK JAR is a fat JAR that includes all necessary dependencies (FlatBuffers, Gson, SLF4J API).

---

## 🐛 Troubleshooting

### Runtime connection failed

```bash
# Check runtime is running
pgrep -a vastar-connector-runtime

# Check socket
ls -la /tmp/vastar-connector-runtime.sock

# Restart runtime
cd ../../..
./clean_vcr.sh
./start_runtime.sh
```

### Simulator connection failed

```bash
# Check simulator is running
docker ps | grep rai-simulator

# Check port
curl http://localhost:4545/v1/models

# Restart simulator
docker restart rai-simulator
```

### OpenAI API errors

```bash
# Check API key is set
echo $OPENAI_API_KEY

# Check quota
# Visit: https://platform.openai.com/account/usage
```

### Build errors

```bash
# Rebuild SDK if needed
cd ../../sdk-java
./gradlew clean build fatJar
cp build/libs/vastar-connector-sdk-java-0.1.0-all.jar ../examples-java/libs/

# Clean and rebuild example
cd ../examples-java/openai-stream-sse-connector
./gradlew clean build
```

---

## 🎯 Use Cases

1. **Chatbots** - Build conversational AI applications
2. **Content Generation** - Generate text content
3. **Code Assistance** - AI-powered code help
4. **Customer Support** - Automated support systems
5. **Education** - Interactive learning assistants

---

## 📖 More Information

- **SDK Documentation**: See `../../sdk-java/README.md`
- **Library Usage**: See `../../sdk-java/docs/LIBRARY_USAGE.md`
- **Root README**: See `../../../README.md`

---

## 🎓 Next Steps

1. **Modify examples** - Add your own chat scenarios
2. **Add streaming** - Implement SSE streaming support
3. **Error handling** - Enhance retry logic
4. **Integrate** - Use in your own Java application

---

**Ready to build AI-powered applications with Java!** 🚀


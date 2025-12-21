// OpenAI Stream Connector - Streaming Chat Completions
// Uses Vastar Connector SDK to communicate with OpenAI Simulator
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	vastar "github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang"
)

// OpenAI API Types
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatCompletionRequest struct {
	Model       string    `json:"model"`
	Messages    []Message `json:"messages"`
	Stream      bool      `json:"stream"`
	MaxTokens   int       `json:"max_tokens,omitempty"`
	Temperature float64   `json:"temperature,omitempty"`
}

type StreamChunk struct {
	ID      string `json:"id"`
	Object  string `json:"object"`
	Created int64  `json:"created"`
	Model   string `json:"model"`
	Choices []struct {
		Index int `json:"index"`
		Delta struct {
			Content string `json:"content"`
		} `json:"delta"`
		FinishReason *string `json:"finish_reason"`
	} `json:"choices"`
	Usage *struct {
		PromptTokens     int `json:"prompt_tokens"`
		CompletionTokens int `json:"completion_tokens"`
		TotalTokens      int `json:"total_tokens"`
	} `json:"usage,omitempty"`
}

type OpenAIConnector struct {
	client  *vastar.RuntimeClient
	baseURL string
	apiKey  string
}

func NewOpenAIConnector(baseURL string) (*OpenAIConnector, error) {
	return NewOpenAIConnectorWithAuth(baseURL, "")
}

func NewOpenAIConnectorWithAuth(baseURL, apiKey string) (*OpenAIConnector, error) {
	client, err := vastar.NewRuntimeClient()
	if err != nil {
		return nil, fmt.Errorf("failed to create runtime client: %w", err)
	}

	return &OpenAIConnector{
		client:  client,
		baseURL: baseURL,
		apiKey:  apiKey,
	}, nil
}

func (c *OpenAIConnector) Close() error {
	return c.client.Close()
}

// TestConnection tests connection to OpenAI simulator
func (c *OpenAIConnector) TestConnection() (string, error) {
	req := vastar.POST(c.baseURL+"/test_completion").
		WithHeader("Content-Type", "application/json").
		WithTimeout(30000)

	resp, err := c.client.ExecuteHTTP(req)
	if err != nil {
		return "", fmt.Errorf("connection test failed: %w", err)
	}

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	// Parse response to get message
	var testResp struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}

	if err := json.Unmarshal(resp.Body, &testResp); err != nil {
		return "", fmt.Errorf("failed to parse response: %w", err)
	}

	if len(testResp.Choices) > 0 {
		return testResp.Choices[0].Message.Content, nil
	}

	return string(resp.Body), nil
}

// ChatCompletionStream performs streaming chat completion
func (c *OpenAIConnector) ChatCompletionStream(req ChatCompletionRequest) (<-chan string, <-chan error) {
	chunkChan := make(chan string, 100)
	errorChan := make(chan error, 1)

	go func() {
		defer close(chunkChan)
		defer close(errorChan)

		// Marshal request
		reqBody, err := json.Marshal(req)
		if err != nil {
			errorChan <- fmt.Errorf("failed to marshal request: %w", err)
			return
		}

		// Debug: log request body (remove this in production)
		// fmt.Printf("DEBUG: Request JSON: %s\n", string(reqBody))

		// Make HTTP request via Vastar
		httpReq := vastar.POST(c.baseURL+"/v1/chat/completions").
			WithHeader("Content-Type", "application/json").
			WithHeader("Accept", "text/event-stream").
			WithBody(reqBody).
			WithTimeout(300000) // 5 minutes for streaming

		// Add Authorization header if API key is provided
		if c.apiKey != "" {
			httpReq = httpReq.WithHeader("Authorization", "Bearer "+c.apiKey)
		}

		resp, err := c.client.ExecuteHTTP(httpReq)
		if err != nil {
			errorChan <- fmt.Errorf("request failed: %w", err)
			return
		}

		if resp.StatusCode != 200 {
			// Show error details from OpenAI
			errorChan <- fmt.Errorf("unexpected status code: %d - %s", resp.StatusCode, string(resp.Body))
			return
		}

		// Parse SSE stream
		scanner := bufio.NewScanner(bytes.NewReader(resp.Body))
		for scanner.Scan() {
			line := scanner.Text()

			// Skip empty lines
			if line == "" {
				continue
			}

			// Parse SSE data line
			if !strings.HasPrefix(line, "data: ") {
				continue
			}

			data := strings.TrimPrefix(line, "data: ")

			// Check for stream end
			if data == "[DONE]" {
				break
			}

			// Parse chunk
			var chunk StreamChunk
			if err := json.Unmarshal([]byte(data), &chunk); err != nil {
				// Skip malformed chunks
				continue
			}

			// Extract content
			if len(chunk.Choices) > 0 {
				content := chunk.Choices[0].Delta.Content
				if content != "" {
					chunkChan <- content
				}

				// Check finish reason
				if chunk.Choices[0].FinishReason != nil {
					// Stream complete
					break
				}
			}

			// Send usage info if present
			if chunk.Usage != nil {
				usageMsg := fmt.Sprintf("\n[Usage: %d prompt + %d completion = %d total tokens]",
					chunk.Usage.PromptTokens,
					chunk.Usage.CompletionTokens,
					chunk.Usage.TotalTokens)
				chunkChan <- usageMsg
			}
		}

		if err := scanner.Err(); err != nil {
			errorChan <- fmt.Errorf("error reading stream: %w", err)
		}
	}()

	return chunkChan, errorChan
}

// ChatCompletion performs non-streaming chat completion (collects all chunks)
func (c *OpenAIConnector) ChatCompletion(req ChatCompletionRequest) (string, error) {
	req.Stream = true // Force streaming mode

	chunkChan, errorChan := c.ChatCompletionStream(req)
	var fullResponse strings.Builder

	for {
		select {
		case chunk, ok := <-chunkChan:
			if !ok {
				return fullResponse.String(), nil
			}
			fullResponse.WriteString(chunk)

		case err := <-errorChan:
			if err != nil {
				return "", err
			}
		}
	}
}

func main() {
	fmt.Println("🤖 OpenAI Stream Connector Demo")
	fmt.Println("=" + strings.Repeat("=", 60))
	fmt.Println()

	// Get configuration from environment
	apiKey := os.Getenv("OPENAI_API_KEY")
	baseURL := os.Getenv("OPENAI_BASE_URL")

	// Default to simulator if not specified
	if baseURL == "" {
		if apiKey != "" {
			baseURL = "https://api.openai.com"
			fmt.Println("🌐 Using Real OpenAI API")
		} else {
			baseURL = "http://localhost:4545"
			fmt.Println("🧪 Using RAI Simulator (localhost:4545)")
		}
	}

	fmt.Printf("🔗 Base URL: %s\n", baseURL)
	if apiKey != "" {
		fmt.Printf("🔑 API Key: %s...%s\n", apiKey[:7], apiKey[len(apiKey)-4:])
	}
	fmt.Println()

	// Create connector
	var connector *OpenAIConnector
	var err error

	if apiKey != "" {
		connector, err = NewOpenAIConnectorWithAuth(baseURL, apiKey)
	} else {
		connector, err = NewOpenAIConnector(baseURL)
	}

	if err != nil {
		log.Fatalf("Failed to create connector: %v", err)
	}
	defer connector.Close()

	// Test connection (skip for real OpenAI as it doesn't have /test_completion)
	if baseURL == "http://localhost:4545" {
		fmt.Println("📡 Testing connection to OpenAI Simulator...")
		testMsg, err := connector.TestConnection()
		if err != nil {
			fmt.Printf("❌ Connection test failed: %v\n\n", err)
			fmt.Println("⚠️  RAI Endpoint Simulator is not running!")
			fmt.Println()
			fmt.Println("To run this example, you need RAI Endpoint Simulator:")
			fmt.Println("1. Docker: docker run -d -p 4545:4545 rai-endpoint-simulator:latest")
			fmt.Println("2. Or from source: cd rai-endpoint-simulator && cargo run")
			fmt.Println()
			fmt.Println("Or set OPENAI_API_KEY to use real OpenAI API.")
			fmt.Println()
			return
		}

		fmt.Printf("✅ %s\n\n", testMsg)
	} else {
		fmt.Println("📡 Skipping test_completion (not available for real OpenAI API)")
		fmt.Println()
	}

	// Example 1: Streaming chat completion
	fmt.Println("Example 1: Streaming Chat Completion")
	fmt.Println("-" + strings.Repeat("-", 60))

	req := ChatCompletionRequest{
		Model: "gpt-3.5-turbo",  // Using GPT-3.5 Turbo (faster and cheaper)
		Messages: []Message{
			{
				Role:    "user",
				Content: "Explain quantum computing in simple terms.",
			},
		},
		Stream:      true,
		MaxTokens:   500,
		Temperature: 0.7,
	}

	fmt.Println("User: Explain quantum computing in simple terms.")
	fmt.Print("AI: ")

	chunkChan, errorChan := connector.ChatCompletionStream(req)
	var fullResponse strings.Builder

	for {
		select {
		case chunk, ok := <-chunkChan:
			if !ok {
				fmt.Println() // New line after stream
				goto StreamComplete
			}
			fmt.Print(chunk)
			os.Stdout.Sync() // Flush output to show streaming in real-time
			fullResponse.WriteString(chunk)

		case err := <-errorChan:
			if err != nil {
				fmt.Printf("\n❌ Error: %v\n", err)
				return
			}
		}
	}

StreamComplete:
	fmt.Println()
	fmt.Println("-" + strings.Repeat("-", 60))
	fmt.Printf("📊 Total response length: %d characters\n", fullResponse.Len())
	fmt.Println()

	// Example 2: Non-streaming (collect all)
	fmt.Println("Example 2: Non-Streaming Chat Completion")
	fmt.Println("-" + strings.Repeat("-", 60))

	req2 := ChatCompletionRequest{
		Model: "gpt-3.5-turbo",
		Messages: []Message{
			{
				Role:    "user",
				Content: "What is the capital of France?",
			},
		},
		Stream:    true,
		MaxTokens: 100,
	}

	fmt.Println("User: What is the capital of France?")
	fmt.Print("AI: ")

	response, err := connector.ChatCompletion(req2)
	if err != nil {
		log.Fatalf("Request failed: %v", err)
	}

	fmt.Println(response)
	fmt.Println()

	// Example 3: Interactive chat loop
	fmt.Println("Example 3: Interactive Chat")
	fmt.Println("-" + strings.Repeat("-", 60))
	fmt.Println("Type 'quit' to exit")
	fmt.Println()

	conversationHistory := []Message{
		{
			Role:    "system",
			Content: "You are a helpful AI assistant.",
		},
	}

	// Simulate a few interactions
	questions := []string{
		"Hello! How are you?",
		"What can you help me with?",
		"Tell me a fun fact about space.",
	}

	for _, question := range questions {
		fmt.Printf("You: %s\n", question)

		// Add user message to history
		conversationHistory = append(conversationHistory, Message{
			Role:    "user",
			Content: question,
		})

		// Create request with full conversation history
		req := ChatCompletionRequest{
			Model:       "gpt-3.5-turbo",
			Messages:    conversationHistory,
			Stream:      true,
			MaxTokens:   200,
			Temperature: 0.8,
		}

		fmt.Print("AI: ")

		// Get streaming response
		chunkChan, errorChan := connector.ChatCompletionStream(req)
		var assistantResponse strings.Builder

	streamLoop:
		for {
			select {
			case chunk, ok := <-chunkChan:
				if !ok {
					break streamLoop
				}
				fmt.Print(chunk)
				os.Stdout.Sync() // Flush output immediately
				assistantResponse.WriteString(chunk)

			case err := <-errorChan:
				if err != nil {
					fmt.Printf("\n❌ Error: %v\n", err)
					return
				}
			}
		}

		fmt.Println()

		// Add assistant response to history
		conversationHistory = append(conversationHistory, Message{
			Role:    "assistant",
			Content: assistantResponse.String(),
		})

		fmt.Println()
		time.Sleep(500 * time.Millisecond) // Small delay between questions
	}

	fmt.Println("=" + strings.Repeat("=", 60))
	fmt.Println("✅ Demo completed successfully!")
}

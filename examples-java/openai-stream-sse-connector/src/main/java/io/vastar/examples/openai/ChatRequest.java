package io.vastar.examples.openai;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * ChatRequest builder for OpenAI Chat Completions API
 */
public class ChatRequest {
    private static final Gson gson = new GsonBuilder().create();

    private final String model;
    private final List<Message> messages;
    private final boolean stream;
    private final Double temperature;
    private final Integer maxTokens;

    private ChatRequest(Builder builder) {
        this.model = builder.model;
        this.messages = new ArrayList<>(builder.messages);
        this.stream = builder.stream;
        this.temperature = builder.temperature;
        this.maxTokens = builder.maxTokens;
    }

    public static Builder builder() {
        return new Builder();
    }

    public String toJSON() {
        Map<String, Object> data = new HashMap<>();
        data.put("model", model);
        data.put("messages", messages);
        data.put("stream", stream);

        if (temperature != null) {
            data.put("temperature", temperature);
        }
        if (maxTokens != null) {
            data.put("max_tokens", maxTokens);
        }

        return gson.toJson(data);
    }

    public static class Builder {
        private String model = "gpt-3.5-turbo";
        private List<Message> messages = new ArrayList<>();
        private boolean stream = false;
        private Double temperature;
        private Integer maxTokens;

        public Builder model(String model) {
            this.model = model;
            return this;
        }

        public Builder addMessage(String role, String content) {
            this.messages.add(new Message(role, content));
            return this;
        }

        public Builder stream(boolean stream) {
            this.stream = stream;
            return this;
        }

        public Builder temperature(double temperature) {
            this.temperature = temperature;
            return this;
        }

        public Builder maxTokens(int maxTokens) {
            this.maxTokens = maxTokens;
            return this;
        }

        public ChatRequest build() {
            if (messages.isEmpty()) {
                throw new IllegalStateException("At least one message is required");
            }
            return new ChatRequest(this);
        }
    }

    static class Message {
        private final String role;
        private final String content;

        Message(String role, String content) {
            this.role = role;
            this.content = content;
        }

        public String getRole() {
            return role;
        }

        public String getContent() {
            return content;
        }
    }
}


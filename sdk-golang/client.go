// Package vastar provides IPC client for Vastar Connector Runtime
//
// ✅ Protocol: [4-byte length BE] + [1-byte msg_type] + [FlatBuffers payload]
// ✅ Schema: connector_ipc.fbs (ExecuteRequest/ExecuteResponse)
// ✅ Verified with: test_flatbuffers_protocol.py
//
// Reference: scripts/test_flatbuffers_protocol.py
package vastar

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"runtime"
	"sync/atomic"
	"time"

	flatbuffers "github.com/google/flatbuffers/go"
	ipc "github.com/fullstack-aidev/vastar-wf-connector-sdk-bin/sdk-golang/protocol"
)

// Frame protocol constants
const (
	FrameLengthSize = 4 // 4-byte length prefix (big-endian)
	MessageTypeSize = 1 // 1-byte message type

	MessageTypeExecuteRequest  = 0x00
	MessageTypeExecuteResponse = 0x01
	MessageTypeHealthCheck     = 0x02
	MessageTypeHealthResponse  = 0x03
	MessageTypeCreditUpdate    = 0x04

	MaxPayloadSize = 10 * 1024 * 1024 // 10MB
)

// RuntimeClient represents a connection to Vastar Connector Runtime
type RuntimeClient struct {
	conn         net.Conn
	platform     string
	timeout      time.Duration
	tenantID     string
	workspaceID  string
	requestIDSeq uint64
}

// HTTPRequest represents an HTTP request
type HTTPRequest struct {
	Method      string
	URL         string
	Headers     map[string]string
	Body        []byte
	TimeoutMs   uint32
	TenantID    string
	WorkspaceID string
	TraceID     string
}

// HTTPResponse represents response from runtime
type HTTPResponse struct {
	RequestID    uint64
	StatusCode   uint16
	Success      bool
	Body         []byte
	Headers      map[string]string
	ErrorMessage string
	ErrorClass   ipc.ErrorClass
	DurationUs   uint64
}

// ConnectorError represents an error from runtime
type ConnectorError struct {
	Message    string
	ErrorClass ipc.ErrorClass
	RequestID  uint64
}

func (e *ConnectorError) Error() string {
	return fmt.Sprintf("[%s] %s (request_id: %d)", e.ErrorClass, e.Message, e.RequestID)
}

func (e *ConnectorError) IsRetryable() bool {
	return e.ErrorClass == ipc.ErrorClassTransient ||
		e.ErrorClass == ipc.ErrorClassRateLimited ||
		e.ErrorClass == ipc.ErrorClassTimeout
}

// NewRuntimeClient creates new client with defaults
func NewRuntimeClient() (*RuntimeClient, error) {
	return NewRuntimeClientWithOptions(60*time.Second, "default", "")
}

// NewRuntimeClientWithOptions creates client with custom options
func NewRuntimeClientWithOptions(timeout time.Duration, tenantID, workspaceID string) (*RuntimeClient, error) {
	client := &RuntimeClient{
		platform:     runtime.GOOS,
		timeout:      timeout,
		tenantID:     tenantID,
		workspaceID:  workspaceID,
		requestIDSeq: uint64(time.Now().UnixNano()),
	}

	if err := client.connect(); err != nil {
		return nil, fmt.Errorf("failed to connect to runtime: %w", err)
	}

	return client, nil
}

// connect establishes connection
func (c *RuntimeClient) connect() error {
	useTCP := os.Getenv("VASTAR_USE_TCP") == "true"

	if useTCP {
		return c.connectTCP()
	}

	if c.platform == "linux" || c.platform == "darwin" {
		if err := c.connectUnixSocket(); err == nil {
			return nil
		}
	}

	return c.connectTCP()
}

// connectUnixSocket connects via Unix Domain Socket
func (c *RuntimeClient) connectUnixSocket() error {
	socketPath := os.Getenv("VASTAR_SOCKET_PATH")
	if socketPath == "" {
		socketPath = "/tmp/vastar-connector-runtime.sock"
	}

	conn, err := net.DialTimeout("unix", socketPath, c.timeout)
	if err != nil {
		return err
	}

	c.conn = conn
	fmt.Printf("🐧 Connected via Unix Socket: %s\n", socketPath)
	return nil
}

// connectTCP connects via TCP
func (c *RuntimeClient) connectTCP() error {
	tcpPort := os.Getenv("VASTAR_TCP_PORT")
	if tcpPort == "" {
		tcpPort = "5000"
	}

	tcpAddr := fmt.Sprintf("127.0.0.1:%s", tcpPort)
	conn, err := net.DialTimeout("tcp", tcpAddr, c.timeout)
	if err != nil {
		return err
	}

	c.conn = conn
	fmt.Printf("🔌 Connected via TCP: %s\n", tcpAddr)
	return nil
}

// Close closes the connection
func (c *RuntimeClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// nextRequestID generates next request ID
func (c *RuntimeClient) nextRequestID() uint64 {
	return atomic.AddUint64(&c.requestIDSeq, 1)
}

// sendFrame sends a frame: [4-byte length BE] + [1-byte msg_type] + [payload]
func (c *RuntimeClient) sendFrame(messageType uint8, payload []byte) error {
	// Frame: [length][msgtype][payload]
	totalLen := uint32(MessageTypeSize + len(payload))

	// Send length (big-endian)
	lengthBuf := make([]byte, FrameLengthSize)
	binary.BigEndian.PutUint32(lengthBuf, totalLen)
	if _, err := c.conn.Write(lengthBuf); err != nil {
		return fmt.Errorf("failed to write frame length: %w", err)
	}

	// Send message type
	if _, err := c.conn.Write([]byte{messageType}); err != nil {
		return fmt.Errorf("failed to write message type: %w", err)
	}

	// Send payload
	if _, err := c.conn.Write(payload); err != nil {
		return fmt.Errorf("failed to write frame payload: %w", err)
	}

	return nil
}

// receiveFrame receives a frame and returns message type + payload
func (c *RuntimeClient) receiveFrame() (uint8, []byte, error) {
	if err := c.conn.SetReadDeadline(time.Now().Add(c.timeout)); err != nil {
		return 0, nil, fmt.Errorf("failed to set read deadline: %w", err)
	}

	// Read length (big-endian)
	lengthBuf := make([]byte, FrameLengthSize)
	if _, err := io.ReadFull(c.conn, lengthBuf); err != nil {
		return 0, nil, fmt.Errorf("failed to read frame length: %w", err)
	}

	totalLen := binary.BigEndian.Uint32(lengthBuf)

	if totalLen > MaxPayloadSize {
		return 0, nil, fmt.Errorf("payload too large: %d bytes (max %d)", totalLen, MaxPayloadSize)
	}

	// Read message type
	msgTypeBuf := make([]byte, MessageTypeSize)
	if _, err := io.ReadFull(c.conn, msgTypeBuf); err != nil {
		return 0, nil, fmt.Errorf("failed to read message type: %w", err)
	}
	messageType := msgTypeBuf[0]

	// Read payload
	payloadLen := totalLen - MessageTypeSize
	payload := make([]byte, payloadLen)
	if _, err := io.ReadFull(c.conn, payload); err != nil {
		return 0, nil, fmt.Errorf("failed to read frame payload: %w", err)
	}

	return messageType, payload, nil
}

// ExecuteHTTP executes HTTP request via runtime
func (c *RuntimeClient) ExecuteHTTP(req *HTTPRequest) (*HTTPResponse, error) {
	requestID := c.nextRequestID()

	// Set defaults
	if req.TenantID == "" {
		req.TenantID = c.tenantID
	}
	if req.TenantID == "" {
		req.TenantID = "default"
	}
	if req.WorkspaceID == "" {
		req.WorkspaceID = c.workspaceID
	}

	// Build HTTP payload as JSON (connector-specific data)
	httpPayload := map[string]interface{}{
		"method": req.Method,
		"url":    req.URL,
	}
	if req.Headers != nil && len(req.Headers) > 0 {
		httpPayload["headers"] = req.Headers
	}
	if req.Body != nil {
		// Convert body to string to ensure valid JSON encoding
		httpPayload["body"] = string(req.Body)
	}

	payloadJSON, err := json.Marshal(httpPayload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %w", err)
	}

	// Build FlatBuffers ExecuteRequest
	builder := flatbuffers.NewBuilder(1024)

	tenantOffset := builder.CreateString(req.TenantID)
	connectorOffset := builder.CreateString("http")
	operationOffset := builder.CreateString("request")
	payloadOffset := builder.CreateByteVector(payloadJSON)

	var workspaceOffset flatbuffers.UOffsetT
	if req.WorkspaceID != "" {
		workspaceOffset = builder.CreateString(req.WorkspaceID)
	}
	var traceOffset flatbuffers.UOffsetT
	if req.TraceID != "" {
		traceOffset = builder.CreateString(req.TraceID)
	}

	timeout := req.TimeoutMs
	if timeout == 0 {
		timeout = 30000
	}
	deadlineMs := uint64(time.Now().Add(time.Duration(timeout) * time.Millisecond).UnixMilli())

	ipc.ExecuteRequestStart(builder)
	ipc.ExecuteRequestAddRequestId(builder, requestID)
	ipc.ExecuteRequestAddTenantId(builder, tenantOffset)
	if req.WorkspaceID != "" {
		ipc.ExecuteRequestAddWorkspaceId(builder, workspaceOffset)
	}
	if req.TraceID != "" {
		ipc.ExecuteRequestAddTraceId(builder, traceOffset)
	}
	ipc.ExecuteRequestAddConnectorName(builder, connectorOffset)
	ipc.ExecuteRequestAddOperation(builder, operationOffset)
	ipc.ExecuteRequestAddDeadlineAtMs(builder, deadlineMs)
	ipc.ExecuteRequestAddPayload(builder, payloadOffset)

	request := ipc.ExecuteRequestEnd(builder)
	builder.Finish(request)

	// Send frame
	if err := c.sendFrame(MessageTypeExecuteRequest, builder.FinishedBytes()); err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}

	// Receive response
	respMsgType, respPayload, err := c.receiveFrame()
	if err != nil {
		return nil, fmt.Errorf("failed to receive response: %w", err)
	}

	if respMsgType != MessageTypeExecuteResponse {
		return nil, fmt.Errorf("unexpected message type: %d", respMsgType)
	}

	// Parse ExecuteResponse
	response := ipc.GetRootAsExecuteResponse(respPayload, 0)

	resp := &HTTPResponse{
		RequestID:    response.RequestId(),
		ErrorClass:   response.ErrorClass(),
		ErrorMessage: string(response.ErrorMessage()),
		Body:         response.PayloadBytes(),
		DurationUs:   response.DurationUs(),
		Headers:      make(map[string]string),
	}

	resp.Success = resp.ErrorClass == ipc.ErrorClassSuccess

	// Parse HTTP response from payload if success
	if resp.Success && len(resp.Body) > 0 {
		var httpResp map[string]interface{}
		if err := json.Unmarshal(resp.Body, &httpResp); err == nil {
			if statusCode, ok := httpResp["status_code"].(float64); ok {
				resp.StatusCode = uint16(statusCode)
			}
			if body, ok := httpResp["body"].(string); ok {
				resp.Body = []byte(body)
			}
			if headers, ok := httpResp["headers"].(map[string]interface{}); ok {
				for k, v := range headers {
					if vstr, ok := v.(string); ok {
						resp.Headers[k] = vstr
					}
				}
			}
		}
	}

	if !resp.Success {
		return resp, &ConnectorError{
			Message:    resp.ErrorMessage,
			ErrorClass: resp.ErrorClass,
			RequestID:  resp.RequestID,
		}
	}

	return resp, nil
}

// Convenience functions
func GET(url string) *HTTPRequest {
	return &HTTPRequest{Method: "GET", URL: url}
}

func POST(url string) *HTTPRequest {
	return &HTTPRequest{Method: "POST", URL: url}
}

func PUT(url string) *HTTPRequest {
	return &HTTPRequest{Method: "PUT", URL: url}
}

func DELETE(url string) *HTTPRequest {
	return &HTTPRequest{Method: "DELETE", URL: url}
}

func (r *HTTPRequest) WithHeader(key, value string) *HTTPRequest {
	if r.Headers == nil {
		r.Headers = make(map[string]string)
	}
	r.Headers[key] = value
	return r
}

func (r *HTTPRequest) WithBody(body []byte) *HTTPRequest {
	r.Body = body
	return r
}

func (r *HTTPRequest) WithJSON(v interface{}) *HTTPRequest {
	data, _ := json.Marshal(v)
	r.Body = data
	r.WithHeader("Content-Type", "application/json")
	return r
}

func (r *HTTPRequest) WithTimeout(timeoutMs uint32) *HTTPRequest {
	r.TimeoutMs = timeoutMs
	return r
}

func (r *HTTPRequest) WithTenantID(tenantID string) *HTTPRequest {
	r.TenantID = tenantID
	return r
}

func (r *HTTPRequest) WithWorkspaceID(workspaceID string) *HTTPRequest {
	r.WorkspaceID = workspaceID
	return r
}

func (r *HTTPRequest) WithTraceID(traceID string) *HTTPRequest {
	r.TraceID = traceID
	return r
}


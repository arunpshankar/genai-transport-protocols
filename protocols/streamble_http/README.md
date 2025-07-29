# Protocol: Streamable HTTP

Real-time streaming multi-turn chat server and client implementation using HTTP chunked transfer encoding, session management, and live response streaming.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start server (Terminal 1)
python server.py

# 3. Start client (Terminal 2)
python client.py

# 4. Try the web demo (Optional)
# Visit http://localhost:8000/demo
```

**Server**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs  
**HTTP Demo**: http://localhost:8000/demo

## HTTP Streaming Features

- **Chunked Transfer Encoding**: Real-time response streaming using HTTP/1.1 chunked encoding
- **NDJSON Protocol**: Newline-delimited JSON for structured streaming data
- **Multi-turn Context**: Persistent conversation history across streaming responses
- **Session Management**: Independent streaming conversations with context preservation
- **Connection Monitoring**: Real-time tracking of active HTTP streams and connections
- **Standard HTTP**: Compatible with any HTTP client, no special protocols required

## Server Implementation

- **HTTP Streaming Engine**: Real-time response streaming using FastAPI + StreamingResponse
- **Multi-turn Chat Sessions**: Context-aware conversations with streaming responses
- **Connection Management**: Track and monitor active HTTP streaming connections
- **Stream Lifecycle Logging**: Detailed logs for stream start, chunks, and completion
- **Session Isolation**: Multiple independent streaming conversations
- **Performance Monitoring**: Stream statistics, timing, and connection metrics
- **Interactive Demo Page**: Built-in web interface for testing HTTP streaming functionality
- **Auto-generated API Documentation**: Interactive OpenAPI schema with streaming endpoints

## Client Implementation

- **Real-time Stream Processing**: Live display of AI responses as they arrive via HTTP
- **Multi-turn Session Management**: Create, switch, and manage streaming chat sessions
- **Stream State Monitoring**: Visual indicators for active streams and session context
- **Chunk-by-chunk Display**: Smooth real-time text rendering as responses stream in
- **Connection Recovery**: Graceful handling of stream interruptions and reconnections
- **Session Statistics**: Track streaming performance, chunks received, and timing
- **Interactive Commands**: Full session management during live conversations

## Client Commands

### Basic Commands
| Command | Action |
|---------|--------|
| `/help` | Show all available commands |
| `/stats` | Show client streaming statistics |
| `/server` | Display server and streaming statistics |
| `/health` | Check server health and active streams |
| `/docs` | Open API documentation in browser |
| `/demo` | Open interactive HTTP streaming demo page |
| `/clear` | Clear screen |
| `/quit` | Exit client |

### Session Management
| Command | Action |
|---------|--------|
| `/new` | Create a new streaming chat session |
| `/info` | Show current session details |
| `/sessions` | List all active sessions on server |
| `/reset` | Clear current session history |
| `/delete` | Delete current session |

## API Endpoints

### Streaming Chat Endpoints
- `POST /chat/stream` - Start HTTP stream for chat message with session context
- `POST /sessions/new` - Create a new chat session for streaming
- `GET /sessions/{session_id}` - Get session information and message history
- `DELETE /sessions/{session_id}` - Delete a specific session
- `POST /sessions/{session_id}/clear` - Clear session conversation history
- `GET /sessions` - List all active sessions with streaming capability

### System Endpoints
- `GET /health` - Health check with streaming connection statistics
- `GET /stats` - Detailed server statistics including stream metrics
- `GET /demo` - Interactive web-based HTTP streaming demo page
- `GET /docs` - Interactive API documentation
- `GET /` - Server information and available streaming endpoints

## HTTP Streaming Protocol

The streaming endpoint uses standard HTTP with chunked transfer encoding and NDJSON format:

### Request Headers
```http
POST /chat/stream HTTP/1.1
Content-Type: application/json
Accept: application/x-ndjson
```

### Response Headers
```http
HTTP/1.1 200 OK
Content-Type: application/x-ndjson
Transfer-Encoding: chunked
Cache-Control: no-cache
Connection: keep-alive
```

### NDJSON Stream Format
Each line in the response is a separate JSON object:

```json
{"type": "session_info", "session_id": "...", "model": "gemini-2.0-flash", "timestamp": "..."}
{"type": "status", "message": "Generating response...", "context_messages": 4}
{"type": "chunk", "text": "Hello there!", "chunk_number": 1, "is_final": false, "timestamp": "..."}
{"type": "chunk", "text": "How can I", "chunk_number": 2, "is_final": false, "timestamp": "..."}
{"type": "chunk", "text": "help you today?", "chunk_number": 3, "is_final": true, "timestamp": "..."}
{"type": "complete", "total_chunks": 3, "processing_time": 1.23, "message_count": 6, "session_id": "...", "timestamp": "..."}
```

## Configuration

Set environment variable:
```bash
export GENAI_MODEL_ID="your-model-id"  # Default: gemini-2.0-flash
```

## Sample Output

### HTTP Streaming Server Logs
```
╔══════════════════════════════════════════════════════════════╗
║             📡 FASTAPI STREAMABLE HTTP CHAT SERVER 📡         ║
╠══════════════════════════════════════════════════════════════╣
║  Model: gemini-2.0-flash                                      ║
║  Framework: FastAPI + HTTP Streaming                          ║
║  Multi-turn: ENABLED                                          ║
║  Streaming: CHUNKED HTTP                                      ║
║  Status: READY                                                ║
╚══════════════════════════════════════════════════════════════╝

┌─ 📡 HTTP STREAM STARTED [14:32:15.123] ───────────────────────┐
│ Client IP: 127.0.0.1                                          │
│ Session: a1b2c3d4...                                         │
│ Message: "Explain quantum computing"                          │
│ Active Streams: 1                                            │
│ Transfer-Encoding: chunked                                    │
└────────────────────────────────────────────────────────────┘

📡 [14:32:15.456] Chunk #1: "Quantum computing is a..."
📡 [14:32:15.523] Chunk #2: "revolutionary approach to..."
📡 [14:32:15.598] Chunk #3: "information processing that..."

┌─ 📡 HTTP STREAM COMPLETED [14:32:17.234] ──────────────────────┐
│ Session: a1b2c3d4...                                         │
│ Total Chunks: 23                                            │
│ Total Time: 2.111s                                          │
│ Active Streams: 0                                           │
│ Status: SUCCESS                                              │
└────────────────────────────────────────────────────────────┘
```

### Real-time Client Interface
```
📡 FASTAPI STREAMABLE HTTP CHAT CLIENT 📡
🎉 Connected to FastAPI HTTP streaming server successfully!
📡 HTTP chunked streaming enabled - responses will appear as they're generated!

You [a1b2c3d4...] › Explain quantum computing

💭 Generating response... (Context: 6 messages)

🤖 AI Response (HTTP Streaming) (a1b2c3d4... - gemini-2.0-flash)
────────────────────────────────────────────────────────────
Quantum computing is a revolutionary approach to information 
processing that leverages the principles of quantum mechanics 
to perform calculations in ways that classical computers cannot. 
Unlike traditional computers that use bits (0s and 1s), quantum 
computers use quantum bits or "qubits" that can exist in multiple 
states simultaneously through a property called superposition...
────────────────────────────────────────────────────────────

┌─ 📡 HTTP STREAM COMPLETED [14:32:17.234] ─────────────────────┐
│ Total Chunks: 23                                            │
│ Total Time: 2.111s                                          │
│ Context Messages: 8                                         │
│ Transfer-Encoding: chunked                                   │
│ Status: SUCCESS                                              │
└────────────────────────────────────────────────────────────┘
```

### Interactive Web Demo
```
You › /demo
📡 Opening HTTP streaming demo page in your browser...
   URL: http://localhost:8000/demo

# Browser opens with interactive chat interface
# Real-time HTTP streaming visible in web UI with:
# - Live text appearing as it's generated via fetch() API
# - Session management through web interface
# - Visual indicators for chunked transfer encoding
# - Real-time JSON parsing of NDJSON stream
```

### Session Management During Streaming
```
You [a1b2c3d4...] › /info

┌─ 📋 SESSION INFO ────────────────────────────────────────────┐
│ Session ID: a1b2c3d4...                                      │
│ Model: gemini-2.0-flash                                      │
│ Total Messages: 8                                            │
│ User Messages: 4                                             │
│ AI Messages: 4                                               │
│ Duration: 0:05:23                                            │
│ Created: 14:26:52                                            │
└──────────────────────────────────────────────────────────────┘

You › /sessions

┌─ 📋 ALL ACTIVE SESSIONS (3) ────────────────────────────────┐
│ 1. a1b2c3d4... (8 msgs, 0:05:23, 14:26:52) ← CURRENT       │
│ 2. e5f6g7h8... (12 msgs, 0:12:45, 14:15:30)                │
│ 3. i9j0k1l2... (3 msgs, 0:02:10, 14:30:15)                 │
└──────────────────────────────────────────────────────────────┘

You › /new
✨ New session created successfully!
   Session ID: m3n4o5p6...
   Model: gemini-2.0-flash

You [m3n4o5p6...] › Hello! This is a new HTTP streaming conversation
💭 Generating response... (Context: 1 messages)

🤖 AI Response (HTTP Streaming) (m3n4o5p6... - gemini-2.0-flash)
────────────────────────────────────────────────────────────
Hello! Welcome to our new HTTP streaming conversation! I'm 
excited to chat with you using chunked transfer encoding. 
You'll see my responses appear word by word as I generate...
────────────────────────────────────────────────────────────
```

### HTTP Streaming Statistics
```
You › /stats

┌─ 📊 CLIENT SESSION STATISTICS ──────────────────────────────┐
│ Client Session Duration: 0:15:23                             │
│ Messages Sent: 12                                           │
│ Successful Streams: 11                                      │
│ Failed Streams: 1                                           │
│ Total Chunks Received: 267                                  │
│ Avg Chunks per Stream: 24.3                                │
│ Sessions Created: 2                                         │
│ Avg Response Time: 2.456s                                  │
│ Current Session: a1b2c3d4...                               │
│ Session Messages: 8                                         │
└────────────────────────────────────────────────────────────┘

You › /server

┌─ 🖥️  HTTP STREAMING SERVER STATISTICS ──────────────────────┐
│ Server Uptime: 1:23:45                                      │
│ Total Requests: 47                                          │
│ Successful: 45                                              │
│ Failed: 2                                                   │
│ Active Sessions: 3                                          │
│ Active Streams: 0                                           │
│ Total Sessions Created: 8                                   │
│ Avg Response Time: 2.234s                                  │
│ Model: gemini-2.0-flash                                     │
│ Framework: FastAPI + HTTP Streaming                         │
└────────────────────────────────────────────────────────────┘
```

## Technical Implementation

### HTTP Streaming Architecture
- **FastAPI + StreamingResponse**: High-performance async HTTP streaming implementation
- **Chunked Transfer Encoding**: Standard HTTP/1.1 streaming without custom protocols
- **NDJSON Format**: Newline-delimited JSON for structured streaming data
- **Connection Pool Management**: Efficient handling of multiple concurrent streams
- **Stream State Tracking**: Comprehensive monitoring of active connections and sessions

### Streaming Protocol Details
- **Standard HTTP**: Compatible with any HTTP client, no special libraries required
- **Transfer-Encoding: chunked**: Enables real-time streaming without Content-Length
- **NDJSON**: Each line is a complete JSON object for easy parsing
- **Error Recovery**: Graceful handling of connection drops and stream interruptions
- **Flow Control**: Optimized chunk timing for natural reading experience

### Multi-turn Architecture
- **ChatSession Class**: Manages conversation context and history during streaming
- **Session Storage**: In-memory session management with UUID identification
- **Context Preservation**: Full conversation history maintained per streaming session
- **Automatic Lifecycle**: Sessions created on-demand, persist until deleted

### Performance Features
- **Async Processing**: Non-blocking stream handling for multiple concurrent users
- **Memory Efficient**: Optimized stream buffering and connection management
- **Real-time Monitoring**: Live statistics for streams, sessions, and performance
- **Connection Resilience**: Automatic cleanup and resource management
- **Scalable Architecture**: Designed for multiple concurrent streaming sessions

### Technology Stack
- **FastAPI**: Modern async web framework with automatic OpenAPI generation
- **StreamingResponse**: Built-in FastAPI streaming support for HTTP chunked encoding
- **Pydantic**: Type-safe request/response validation and serialization
- **Uvicorn**: High-performance ASGI server with streaming support
- **Colorama**: Cross-platform colored console output for enhanced UX
- **GenAI Client**: Google GenAI integration with context management

## Stream Lifecycle

1. **Initiation**: Client sends POST request to `/chat/stream` with message and optional session_id
2. **Session Setup**: Server creates or retrieves session, establishes HTTP streaming response
3. **Context Loading**: Full conversation history loaded for multi-turn awareness
4. **Response Generation**: AI processes message with full conversation context
5. **Chunk Streaming**: Response delivered in real-time via HTTP chunked transfer encoding
6. **Stream Completion**: Final NDJSON object sent with completion statistics and session info
7. **Connection Cleanup**: Resources released, session state updated, statistics logged

## HTTP Stream Flow

```
Client Request → HTTP Stream Response → Session Info JSON → Status JSON
     ↓
Processing Start → Chunk JSONs (real-time) → Completion JSON
     ↓
Connection Close → Statistics Update → Session State Saved
```

## Browser Compatibility

The HTTP streaming implementation is compatible with:
- **Fetch API**: Native browser support for streaming HTTP responses
- **XMLHttpRequest**: Traditional AJAX with chunked response handling
- **ReadableStream**: Modern streaming API for real-time data processing
- **HTTP/1.1 & HTTP/2**: Compatible with all modern HTTP versions
- **Universal Support**: Works with any HTTP client library

## Interactive Demo Features

The built-in web demo (`/demo`) provides:
- **Real-time Chat Interface**: Full-featured web-based chat with HTTP streaming
- **Session Management**: Create, switch, and manage sessions through web UI
- **Visual Stream Indicators**: Live progress and streaming status display
- **Chunk-by-chunk Display**: Watch responses build up via NDJSON parsing
- **Error Handling**: Visual error states and recovery options
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

## Development Features

- **Hot Reload**: Development server supports code changes without losing sessions
- **Comprehensive Logging**: Detailed stream lifecycle and performance monitoring
- **Error Handling**: Graceful degradation and informative error messages
- **Debug Information**: Rich console output for troubleshooting and monitoring
- **Testing Tools**: Built-in demo and debug endpoints for development

## HTTP Streaming vs Other Protocols

| Feature | Traditional HTTP | HTTP Streaming | Server-Sent Events | WebSockets |
|---------|------------------|----------------|-------------------|------------|
| Protocol | HTTP/1.1 | HTTP/1.1 + Chunked | HTTP + SSE | WebSocket |
| Complexity | Simple | Simple | Medium | Complex |
| Browser Support | Universal | Universal | Modern | Modern |
| Real-time | No | Yes | Yes | Yes |
| Bi-directional | No | No | No | Yes |
| Overhead | Low | Low | Medium | Medium |
| Firewall Friendly | Yes | Yes | Yes | Sometimes |

## Performance Characteristics

- **First Chunk Latency**: ~100-200ms from request
- **Chunk Frequency**: 3-5 words every 100ms (configurable)
- **Memory Usage**: Minimal buffering, immediate delivery via HTTP chunks
- **Concurrent Streams**: Supports multiple simultaneous users
- **Connection Overhead**: Standard HTTP connection reuse
- **Error Recovery**: HTTP-level error handling and retry mechanisms

## HTTP Headers and Protocol Details

### Request Example
```http
POST /chat/stream HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Accept: application/x-ndjson
Content-Length: 45

{"message": "Hello", "session_id": "abc123"}
```

### Response Example
```http
HTTP/1.1 200 OK
Content-Type: application/x-ndjson
Transfer-Encoding: chunked
Cache-Control: no-cache
Connection: keep-alive

{"type": "session_info", "session_id": "abc123", "model": "gemini-2.0-flash"}
{"type": "status", "message": "Generating response...", "context_messages": 2}
{"type": "chunk", "text": "Hello there!", "chunk_number": 1, "is_final": false}
{"type": "complete", "total_chunks": 1, "processing_time": 0.5, "message_count": 4}
```

## Client Implementation Examples

### Python (requests)
```python
response = requests.post('/chat/stream', json={'message': 'Hello'}, stream=True)
for line in response.iter_lines(decode_unicode=True):
    if line:
        data = json.loads(line)
        if data['type'] == 'chunk':
            print(data['text'], end='', flush=True)
```

### JavaScript (fetch)
```javascript
const response = await fetch('/chat/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: 'Hello'})
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value, {stream: true});
    const lines = chunk.split('\n');
    
    for (let line of lines) {
        if (line.trim()) {
            const data = JSON.parse(line);
            if (data.type === 'chunk') {
                console.log(data.text);
            }
        }
    }
}
```

## Advantages of HTTP Streaming

- **Universal Compatibility**: Works with any HTTP client
- **Simple Protocol**: Standard HTTP with chunked encoding
- **Firewall Friendly**: Uses standard HTTP ports and protocols
- **Easy Debugging**: Standard HTTP tools work for debugging
- **No Special Libraries**: Client implementation is straightforward
- **Robust Error Handling**: HTTP-level error codes and handling
- **Caching Friendly**: Can leverage HTTP caching mechanisms where appropriate
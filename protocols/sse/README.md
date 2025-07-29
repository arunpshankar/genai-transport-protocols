# Protocol: Server-Sent Events (SSE)

Real-time streaming multi-turn chat server and client implementation with Server-Sent Events, session management, and live response streaming.

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
**SSE Demo**: http://localhost:8000/demo

## Real-time Streaming Features

- **Live Response Streaming**: AI responses appear word-by-word as they're generated
- **Server-Sent Events**: Efficient real-time communication using SSE protocol
- **Multi-turn Context**: Persistent conversation history across streaming responses
- **Session Management**: Independent streaming conversations with context preservation
- **Connection Monitoring**: Real-time tracking of active streams and connections
- **Chunk-based Delivery**: Responses delivered in optimized chunks for smooth streaming

## Server Implementation

- **SSE Streaming Engine**: Real-time response streaming using FastAPI + SSE-Starlette
- **Multi-turn Chat Sessions**: Context-aware conversations with streaming responses
- **Connection Management**: Track and monitor active SSE connections
- **Stream Lifecycle Logging**: Detailed logs for stream start, chunks, and completion
- **Session Isolation**: Multiple independent streaming conversations
- **Performance Monitoring**: Stream statistics, timing, and connection metrics
- **Interactive Demo Page**: Built-in web interface for testing SSE functionality
- **Auto-generated API Documentation**: Interactive OpenAPI schema with SSE endpoints

## Client Implementation

- **Real-time Stream Processing**: Live display of AI responses as they arrive
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
| `/demo` | Open interactive SSE demo page |
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
- `POST /chat/stream` - Start SSE stream for chat message with session context
- `POST /sessions/new` - Create a new chat session for streaming
- `GET /sessions/{session_id}` - Get session information and message history
- `DELETE /sessions/{session_id}` - Delete a specific session
- `POST /sessions/{session_id}/clear` - Clear session conversation history
- `GET /sessions` - List all active sessions with streaming capability

### System Endpoints
- `GET /health` - Health check with streaming connection statistics
- `GET /stats` - Detailed server statistics including stream metrics
- `GET /demo` - Interactive web-based SSE demo page
- `GET /docs` - Interactive API documentation
- `GET /` - Server information and available streaming endpoints

## SSE Event Types

The streaming endpoint emits different event types:

```json
// Session information
{"type": "session_info", "session_id": "...", "model": "gemini-2.0-flash"}

// Processing status
{"type": "status", "message": "Generating response...", "context_messages": 4}

// Response chunks (streamed in real-time)
{"type": "chunk", "text": "Hello there!", "chunk_number": 1, "is_final": false}

// Stream completion
{"type": "complete", "total_chunks": 15, "processing_time": 2.34, "message_count": 8}

// Error handling
{"type": "error", "message": "Error description", "session_id": "..."}
```

## Configuration

Set environment variable:
```bash
export GENAI_MODEL_ID="your-model-id"  # Default: gemini-2.0-flash
```

## Sample Output

### SSE Server Logs
```
╔══════════════════════════════════════════════════════════════╗
║               🌊 FASTAPI SSE MULTI-TURN CHAT SERVER 🌊        ║
╠══════════════════════════════════════════════════════════════╣
║  Model: gemini-2.0-flash                                      ║
║  Framework: FastAPI + SSE                                     ║
║  Multi-turn: ENABLED                                          ║
║  Streaming: REAL-TIME                                         ║
║  Status: READY                                                ║
╚══════════════════════════════════════════════════════════════╝

┌─ 🌊 SSE STREAM STARTED [14:32:15.123] ──────────────────────────┐
│ Client IP: 127.0.0.1                                            │
│ Session: a1b2c3d4...                                           │
│ Message: "Explain quantum computing"                            │
│ Active Streams: 1                                              │
└────────────────────────────────────────────────────────────┘

🌊 [14:32:15.456] Chunk #1: "Quantum computing is a..."
🌊 [14:32:15.523] Chunk #2: "revolutionary approach to..."
🌊 [14:32:15.598] Chunk #3: "information processing that..."

┌─ 🌊 SSE STREAM COMPLETED [14:32:17.234] ────────────────────────┐
│ Session: a1b2c3d4...                                           │
│ Total Chunks: 23                                              │
│ Total Time: 2.111s                                            │
│ Active Streams: 0                                             │
│ Status: SUCCESS                                               │
└────────────────────────────────────────────────────────────┘
```

### Real-time Client Interface
```
🌊 FASTAPI SSE MULTI-TURN CHAT CLIENT 🌊
🎉 Connected to FastAPI SSE server successfully!
🌊 Real-time streaming enabled - responses will appear as they're generated!

You [a1b2c3d4...] › Explain quantum computing

💭 Generating response... (Context: 6 messages)

🤖 AI Response (Streaming) (a1b2c3d4... - gemini-2.0-flash)
────────────────────────────────────────────────────────────
Quantum computing is a revolutionary approach to information 
processing that leverages the principles of quantum mechanics 
to perform calculations in ways that classical computers cannot. 
Unlike traditional computers that use bits (0s and 1s), quantum 
computers use quantum bits or "qubits" that can exist in multiple 
states simultaneously through a property called superposition...
────────────────────────────────────────────────────────────

┌─ 🌊 SSE STREAM COMPLETED [14:32:17.234] ──────────────────────┐
│ Total Chunks: 23                                              │
│ Total Time: 2.111s                                            │
│ Context Messages: 8                                           │
│ Status: SUCCESS                                                │
└────────────────────────────────────────────────────────────┘
```

### Interactive Web Demo
```
You › /demo
🌊 Opening SSE demo page in your browser...
   URL: http://localhost:8000/demo

# Browser opens with interactive chat interface
# Real-time streaming visible in web UI with:
# - Live text appearing as it's generated
# - Session management through web interface  
# - Visual indicators for streaming status
# - Chunk-by-chunk progress display
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

You [m3n4o5p6...] › Hello! This is a brand new streaming conversation
💭 Generating response... (Context: 1 messages)

🤖 AI Response (Streaming) (m3n4o5p6... - gemini-2.0-flash)
────────────────────────────────────────────────────────────
Hello! Welcome to our new streaming conversation! I'm excited 
to chat with you in real-time. You'll see my responses appear 
word by word as I generate them. What would you like to...
────────────────────────────────────────────────────────────
```

### Streaming Statistics
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

┌─ 🖥️  SSE SERVER STATISTICS ──────────────────────────────────┐
│ Server Uptime: 1:23:45                                      │
│ Total Requests: 47                                          │
│ Successful: 45                                              │
│ Failed: 2                                                   │
│ Active Sessions: 3                                          │
│ Active Streams: 0                                           │
│ Total Sessions Created: 8                                   │
│ Avg Response Time: 2.234s                                  │
│ Model: gemini-2.0-flash                                     │
│ Framework: FastAPI + SSE                                    │
└────────────────────────────────────────────────────────────┘
```
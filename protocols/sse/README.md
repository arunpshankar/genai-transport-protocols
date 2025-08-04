# Protocol: Server-Sent Events (SSE)

Real-time streaming multi-turn chat server and client implementation with Server-Sent Events, session management, and live response streaming.

## Quick Start

**Prerequisites**

```bash
pip install -r requirements.txt
export GENAI_MODEL_ID="gemini-2.0-flash"  # Optional, defaults to gemini-2.0-flash
```

**Initial Setup**

**Before running any server.py, execute these commands from the project root:**

```bash
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$PYTHONPATH:.
```

**Important**: These environment variables must be set from the root directory of the project to ensure proper module imports and clean Python execution.

**Run the Protocol**

```bash
# 1. Start server (Terminal 1)
python protocols/sse/server.py

# 2. Start client (Terminal 2)
python protocols/sse/client.py
```

**Optional: Try the web demo**

```bash
# Visit http://localhost:8000/demo
```

**Server**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs  
**SSE Demo**: http://localhost:8000/demo

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
{"type": "session_info", "session_id": "...", "model": "gemini-2.0-flash"}

{"type": "status", "message": "Generating response...", "context_messages": 4}

{"type": "chunk", "text": "Hello there!", "chunk_number": 1, "is_final": false}

{"type": "complete", "total_chunks": 15, "processing_time": 2.34, "message_count": 8}

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
══════════════════════════════════════════════════════════════
               🌊 FASTAPI SSE MULTI-TURN CHAT SERVER 🌊        
══════════════════════════════════════════════════════════════
  Model: gemini-2.0-flash                                      
  Framework: FastAPI + SSE                                     
  Multi-turn: ENABLED                                          
  Streaming: REAL-TIME                                         
  Status: READY                                                
══════════════════════════════════════════════════════════════

─ 🌊 SSE STREAM STARTED [14:32:15.123] ───────────────────────
 Client IP: 127.0.0.1                                          
 Session: a1b2c3d4...                                         
 Message: "Explain quantum computing"                          
 Active Streams: 1                                            
────────────────────────────────────────────────────────────

🌊 [14:32:15.456] Chunk #1: "Quantum computing is a..."
🌊 [14:32:15.523] Chunk #2: "revolutionary approach to..."
🌊 [14:32:15.598] Chunk #3: "information processing that..."

─ 🌊 SSE STREAM COMPLETED [14:32:17.234] ──────────────────────
 Session: a1b2c3d4...                                         
 Total Chunks: 23                                            
 Total Time: 2.111s                                          
 Active Streams: 0                                           
 Status: SUCCESS                                              
────────────────────────────────────────────────────────────
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

─ 🌊 SSE STREAM COMPLETED [14:32:17.234] ──────────────────────
 Total Chunks: 23                                            
 Total Time: 2.111s                                          
 Context Messages: 8                                         
 Status: SUCCESS                                              
────────────────────────────────────────────────────────────
```
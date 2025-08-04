# Protocol: WebSockets

Real-time bidirectional multi-turn chat server and client implementation using WebSockets, session management, and interactive communication features.

## Quick Start

**Prerequisites**

```bash
pip install -r requirements.txt
pip install websockets
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
python protocols/websockets/server.py

# 2. Start client (Terminal 2)
python protocols/websockets/client.py
```

**Optional: Try the web demo**

```bash
# Visit http://localhost:8000/demo
```

**Server**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs  
**WebSocket Demo**: http://localhost:8000/demo  
**WebSocket Endpoint**: ws://localhost:8000/ws

## Real-time Bidirectional Features

- **Full-Duplex Communication**: Simultaneous two-way real-time messaging
- **WebSocket Protocol**: Native browser and library support for persistent connections
- **Multi-turn Context**: Persistent conversation history across real-time interactions
- **Session Management**: Independent real-time conversations with context preservation
- **Typing Indicators**: Real-time typing status updates between connected clients
- **Session Broadcasting**: Live updates to all clients connected to the same session
- **Connection Health**: Ping/pong heartbeat mechanism for reliable connections

## Server Implementation

- **WebSocket Engine**: Real-time bidirectional communication using FastAPI + WebSockets
- **Multi-turn Chat Sessions**: Context-aware conversations with real-time streaming
- **Connection Management**: Track and monitor active WebSocket connections per session
- **Session Broadcasting**: Real-time updates pushed to all connected clients
- **Message Routing**: Intelligent routing of messages to appropriate session members
- **Performance Monitoring**: Live connection statistics and session analytics
- **Interactive Demo Page**: Built-in web interface for testing WebSocket functionality
- **Hybrid API**: RESTful endpoints combined with WebSocket real-time features

## Client Implementation

- **Asynchronous WebSocket Client**: Non-blocking real-time message handling
- **Multi-turn Session Management**: Create, join, and manage real-time chat sessions
- **Connection State Management**: Automatic reconnection and connection monitoring
- **Real-time Display**: Live message streaming with chunk-by-chunk rendering
- **Bidirectional Features**: Send typing indicators and receive live session updates
- **Session Statistics**: Track connection health, message timing, and performance
- **Interactive Commands**: Full session and connection management

## Client Commands

### Basic Commands
| Command | Action |
|---------|--------|
| `/help` | Show all available commands |
| `/stats` | Show client session statistics |
| `/server` | Display server statistics |
| `/health` | Check server health |
| `/docs` | Open API documentation in browser |
| `/demo` | Open interactive WebSocket demo page |
| `/clear` | Clear screen |
| `/quit` | Exit client |

### WebSocket Commands
| Command | Action |
|---------|--------|
| `/connect` | Connect to WebSocket server |
| `/disconnect` | Disconnect from WebSocket server |
| `/ping` | Send ping to test connection health |

### Session Management
| Command | Action |
|---------|--------|
| `/new` | Create a new real-time chat session |
| `/info` | Show current session details |
| `/sessions` | List all active sessions with connected clients |

## API Endpoints

### WebSocket Endpoints
- `WS /ws` - Main WebSocket endpoint for real-time bidirectional communication

### RESTful Endpoints
- `POST /sessions/new` - Create a new chat session
- `GET /sessions/{session_id}` - Get session information and message history
- `DELETE /sessions/{session_id}` - Delete a specific session
- `POST /sessions/{session_id}/clear` - Clear session conversation history
- `GET /sessions` - List all active sessions with connection counts

### System Endpoints
- `GET /health` - Health check with WebSocket connection statistics
- `GET /stats` - Detailed server statistics including connection metrics
- `GET /demo` - Interactive web-based WebSocket demo page
- `GET /docs` - Interactive API documentation
- `GET /` - Server information and available endpoints

## WebSocket Message Protocol

The WebSocket endpoint uses structured JSON messages for bidirectional communication:

### Client to Server Messages

```json
{"type": "create_session", "model_id": "gemini-2.0-flash"}

{"type": "join_session", "session_id": "abc123"}

{"type": "chat", "message": "Hello!", "session_id": "abc123"}

{"type": "typing_start"}
{"type": "typing_stop"}

{"type": "ping"}
```

### Server to Client Messages

```json
{"type": "connected", "connection_id": "xyz789", "message": "Connected!", "server_info": {...}}

{"type": "session_created", "session_id": "abc123", "model": "gemini-2.0-flash"}
{"type": "session_joined", "session_id": "abc123", "message_count": 5}

{"type": "status", "message": "Generating response...", "context_messages": 4}
{"type": "response_start", "session_id": "abc123", "total_length": 150}
{"type": "chunk", "text": "Hello there!", "chunk_number": 1, "is_final": false}
{"type": "response_complete", "total_chunks": 8, "processing_time": 2.1, "message_count": 6}

{"type": "session_update", "update_type": "user_typing", "typing": true}
{"type": "session_update", "update_type": "message_added", "message_count": 7}

{"type": "pong"}

{"type": "error", "message": "Error description"}
```

## Configuration

Set environment variable:
```bash
export GENAI_MODEL_ID="your-model-id"  # Default: gemini-2.0-flash
```

## Sample Output

### WebSocket Server Logs
```
══════════════════════════════════════════════════════════════
               🔌 FASTAPI WEBSOCKET CHAT SERVER 🔌             
══════════════════════════════════════════════════════════════
  Model: gemini-2.0-flash                                      
  Framework: FastAPI + WebSockets                              
  Multi-turn: ENABLED                                          
  Real-time: BIDIRECTIONAL                                     
  Status: READY                                                
══════════════════════════════════════════════════════════════

─ 🔌 WEBSOCKET CONNECTED [14:32:15.123] ───────────────────────
 Connection ID: a1b2c3d4...                                    
 Client IP: 127.0.0.1                                         
 Active Connections: 1                                        
 Protocol: WebSocket                                          
────────────────────────────────────────────────────────────

─ 📩 WEBSOCKET MESSAGE [14:32:16.456] ──────────────────────────
 Connection: a1b2c3d4...                                       
 Session: e5f6g7h8...                                         
 Type: chat                                                   
 Message: "Explain quantum computing"                         
────────────────────────────────────────────────────────────

─ 🧠 GENERATING RESPONSE [14:32:16.500] ────────────────────────
 Connection: a1b2c3d4...                                       
 Session: e5f6g7h8...                                         
 Context Messages: 6                                          
 Model: gemini-2.0-flash                                       
────────────────────────────────────────────────────────────

🔌 [14:32:16.789] Chunk #1 → a1b2c3d4...: "Quantum computing is..."
🔌 [14:32:16.856] Chunk #2 → a1b2c3d4...: "a revolutionary approach..."
🔌 [14:32:16.923] Chunk #3 → a1b2c3d4...: "to information processing..."
```

### Real-time Client Interface
```
🔌 FASTAPI WEBSOCKET CHAT CLIENT 🔌
🎉 FastAPI WebSocket server is available!
🚀 Auto-connecting to WebSocket server...

─ 🔌 WEBSOCKET CONNECTED [14:32:15.123] ───────────────────────
 Server: ws://localhost:8000/ws                               
 Framework: FastAPI + WebSockets                             
 Protocol: WebSocket                                         
 Connection: a1b2c3d4...                                     
 Bidirectional: ENABLED                                      
────────────────────────────────────────────────────────────

✅ WebSocket connected successfully!
📡 Server: FastAPI + WebSockets (gemini-2.0-flash)
✨ New session created: e5f6g7h8... (gemini-2.0-flash)

You [e5f6g7h8...] ● › Explain quantum computing

💭 Generating response... (Context: 6 messages)

🤖 AI Response (WebSocket Streaming) (e5f6g7h8... - gemini-2.0-flash)
────────────────────────────────────────────────────────────
Quantum computing is a revolutionary approach to information 
processing that leverages the principles of quantum mechanics 
to perform calculations in ways that classical computers cannot. 
Unlike traditional computers that use bits (0s and 1s), quantum 
computers use quantum bits or "qubits" that can exist in multiple 
states simultaneously through a property called superposition...
────────────────────────────────────────────────────────────

─ 🔌 WEBSOCKET RESPONSE COMPLETED [14:32:18.234] ──────────────
 Total Chunks: 23                                            
 Total Time: 1.734s                                          
 Context Messages: 8                                         
 Protocol: WebSocket                                         
 Status: SUCCESS                                              
────────────────────────────────────────────────────────────

👤 Someone else is typing...
📩 Session updated: 10 messages
```

### Interactive Web Demo
```
You › /demo
🔌 Opening WebSocket demo page in your browser...
   URL: http://localhost:8000/demo

Browser opens with interactive WebSocket chat interface featuring:
- Real-time connection status indicator
- Live session management
- Typing indicators between users
- Real-time message streaming
- Connection health monitoring
- Session broadcasting to multiple clients
```

### Multi-client Session Management
```
You [e5f6g7h8...] ● › /sessions

─ 📋 ALL ACTIVE SESSIONS (3) ────────────────────────────────
 1. e5f6g7h8... (8 msgs, 2 clients, 0:05:23, 14:26:52) ← CURRENT
 2. i9j0k1l2... (12 msgs, 1 clients, 0:12:45, 14:15:30)     
 3. m3n4o5p6... (3 msgs, 3 clients, 0:02:10, 14:30:15)      
────────────────────────────────────────────────────────────

You › /new
✨ New session created: q7r8s9t0...
   Model: gemini-2.0-flash

You [q7r8s9t0...] ● › Hello! This is a new real-time conversation
💭 Generating response... (Context: 1 messages)

🤖 AI Response (WebSocket Streaming) (q7r8s9t0... - gemini-2.0-flash)
────────────────────────────────────────────────────────────
Hello! Welcome to our new real-time WebSocket conversation! I'm 
excited to chat with you using bidirectional communication. You'll 
see my responses appear as I generate them, and I can detect when 
you're typing. This creates a much more interactive experience...
────────────────────────────────────────────────────────────
```

### Connection and Performance Statistics
```
You › /stats

─ 📊 CLIENT SESSION STATISTICS ──────────────────────────────
 Client Session Duration: 0:15:23                             
 Messages Sent: 12                                           
 Successful Streams: 11                                      
 Failed Streams: 1                                           
 Total Chunks Received: 267                                  
 Avg Chunks per Stream: 24.3                                
 Connection Attempts: 2                                      
 Reconnections: 1                                            
 Sessions Created: 2                                         
 Avg Response Time: 2.456s                                  
 WebSocket Status: Connected                                  
 Current Session: e5f6g7h8...                               
 Session Messages: 8                                         
────────────────────────────────────────────────────────────

You › /server

─ 🖥️  WEBSOCKET SERVER STATISTICS ───────────────────────────
 Server Uptime: 1:23:45                                      
 Total Requests: 89                                          
 Successful: 85                                              
 Failed: 4                                                   
 Active Sessions: 3                                          
 WebSocket Connections: 5                                    
 Total Sessions Created: 8                                   
 Avg Response Time: 2.234s                                  
 Model: gemini-2.0-flash                                     
 Framework: FastAPI + WebSockets                             
────────────────────────────────────────────────────────────
```

## Technical Implementation

### WebSocket Architecture
- **FastAPI + WebSockets**: Native async WebSocket support with automatic connection management
- **Bidirectional Protocol**: Full-duplex communication enabling real-time interactions
- **Connection Pooling**: Efficient management of multiple concurrent WebSocket connections
- **Message Routing**: Intelligent routing of messages to appropriate session participants
- **Session Broadcasting**: Real-time updates pushed to all connected clients per session

### Real-time Features
- **Persistent Connections**: Long-lived connections for immediate message delivery
- **Typing Indicators**: Live typing status shared between connected clients
- **Session Updates**: Real-time notifications when users join, leave, or send messages
- **Connection Health**: Ping/pong heartbeat mechanism for reliable connections
- **Automatic Reconnection**: Client-side reconnection logic for network resilience

### Multi-turn Architecture
- **ChatSession Class**: Manages conversation context and history during real-time interactions
- **Session Storage**: In-memory session management with WebSocket connection tracking
- **Context Preservation**: Full conversation history maintained per real-time session
- **Connection Association**: Mapping of WebSocket connections to chat sessions

### Performance Features
- **Async Processing**: Non-blocking message handling for multiple concurrent connections
- **Event-driven Architecture**: Efficient handling of real-time events and broadcasts
- **Memory Efficient**: Optimized connection management and message buffering
- **Real-time Monitoring**: Live statistics for connections, sessions, and performance
- **Scalable Design**: Architecture designed for thousands of concurrent WebSocket connections

### Technology Stack
- **FastAPI**: Modern async web framework with native WebSocket support
- **WebSockets Library**: Python websockets library for client-side connections
- **Pydantic**: Type-safe request/response validation and serialization
- **Uvicorn**: High-performance ASGI server with WebSocket support
- **Colorama**: Cross-platform colored console output for enhanced UX
- **GenAI Client**: Google GenAI integration with real-time context management

## WebSocket Lifecycle

1. **Connection Establishment**: Client connects to WebSocket endpoint, server accepts and assigns connection ID
2. **Authentication/Welcome**: Server sends welcome message with connection details and capabilities
3. **Session Management**: Client creates or joins session, server associates connection with session
4. **Real-time Communication**: Bidirectional message exchange with live streaming responses
5. **Session Broadcasting**: Updates automatically shared with all session participants
6. **Connection Health**: Periodic ping/pong messages ensure connection reliability
7. **Graceful Disconnection**: Clean connection closure with session state preservation

## WebSocket Message Flow

```
Client Connect → Server Accept → Welcome Message → Session Join/Create
     ↓
Chat Message → Real-time Processing → Streaming Response Chunks
     ↓
Session Updates → Broadcast to All Clients → Connection Maintenance
     ↓
Disconnect → Connection Cleanup → Session State Update
```

## Browser WebSocket Integration

### JavaScript Client Example
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function(event) {
    console.log('Connected to WebSocket server');
    
    ws.send(JSON.stringify({
        type: 'create_session'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'session_created':
            console.log('Session created:', data.session_id);
            break;
            
        case 'chunk':
            document.getElementById('response').innerHTML += data.text;
            break;
            
        case 'session_update':
            if (data.update_type === 'user_typing') {
                showTypingIndicator(data.typing);
            }
            break;
    }
};

function sendMessage(message) {
    ws.send(JSON.stringify({
        type: 'chat',
        message: message,
        session_id: currentSessionId
    }));
}

function sendTyping(isTyping) {
    ws.send(JSON.stringify({
        type: isTyping ? 'typing_start' : 'typing_stop'
    }));
}
```

## Advantages of WebSocket Implementation

- **Real-time Bidirectional**: Immediate two-way communication
- **Persistent Connection**: No connection overhead per message
- **Native Browser Support**: Built-in WebSocket API in all modern browsers
- **Low Latency**: Direct TCP connection for minimal delays
- **Event-driven**: Natural fit for real-time interactive applications
- **Scalable**: Efficient for applications with many concurrent users
- **Rich Interactions**: Support for typing indicators, presence, and live updates

## WebSocket vs Other Protocols

| Feature | WebSockets | HTTP Streaming | Server-Sent Events | Traditional HTTP |
|---------|------------|----------------|-------------------|------------------|
| Bidirectional | Yes | No | No | No |
| Real-time | Yes | Yes | Yes | No |
| Connection Overhead | Low | Medium | Medium | High |
| Browser Support | Universal | Universal | Modern | Universal |
| Complexity | Medium | Low | Low | Low |
| Interactive Features | Excellent | Limited | Limited | None |
| Typing Indicators | Yes | No | No | No |
| Live Session Updates | Yes | No | Limited | No |

## Performance Characteristics

- **Connection Latency**: ~50-100ms initial connection setup
- **Message Latency**: ~1-10ms for message delivery
- **Memory Usage**: Minimal per connection, efficient connection pooling
- **Concurrent Connections**: Thousands per server instance
- **Throughput**: High message throughput with low overhead
- **Reliability**: Built-in error handling and automatic reconnection

## Development and Debugging

- **WebSocket Inspector**: Browser dev tools show WebSocket traffic
- **Message Logging**: Comprehensive logging of all WebSocket messages
- **Connection Monitoring**: Real-time connection health and statistics
- **Error Handling**: Detailed error messages and recovery mechanisms
- **Testing Tools**: Built-in demo page for interactive testing

## Security Considerations

- **Origin Validation**: Server validates WebSocket connection origins
- **Authentication**: Session-based authentication for WebSocket connections
- **Rate Limiting**: Protection against message flooding
- **Input Validation**: All WebSocket messages validated and sanitized
- **Connection Limits**: Per-IP connection limits to prevent abuse

## Deployment Notes

- **Proxy Configuration**: Nginx/Apache configuration for WebSocket proxy
- **Load Balancing**: Sticky sessions required for WebSocket load balancing
- **Firewall Rules**: Ensure WebSocket ports are open
- **SSL/TLS**: WSS (WebSocket Secure) support for production deployments
- **Monitoring**: WebSocket-specific monitoring and alerting
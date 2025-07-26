# Protocol 1: REST HTTP

REST HTTP multi-turn chat server and client implementation with session management, console logging and API documentation.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start server (Terminal 1)
python protocols/rest_http/server.py

# 3. Start client (Terminal 2)
python protocols/rest_http/client.py
```

**Server**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs

## Server Implementation

- **Multi-turn Chat Sessions**: Context-aware conversations using ChatSession class
- **Session Lifecycle Management**: Create, monitor, clear, and delete sessions
- **Real-time Statistics**: Server uptime, session counts, and performance metrics
- **Auto-generated API Documentation**: Interactive OpenAPI schema
- **Health Monitoring**: Comprehensive system status with session information
- **Type-safe Validation**: Pydantic models for all request/response data

## Client Implementation

- **Interactive Multi-turn Chat**: Continuous conversations with context
- **Session Management Commands**: Create, switch, and manage chat sessions
- **Visual Session Indicators**: Current session display in chat prompt
- **HTTP Request/Response Logging**: Detailed logs with session information
- **Session Statistics Tracking**: Per-session and overall usage metrics
- **Browser Integration**: Direct access to API documentation

## Client Commands

### Basic Commands
| Command | Action |
|---------|--------|
| `/help` | Show all available commands |
| `/stats` | Show client session statistics |
| `/server` | Display server statistics |
| `/health` | Check server health status |
| `/docs` | Open API documentation in browser |
| `/clear` | Clear screen |
| `/quit` | Exit client |

### Session Management
| Command | Action |
|---------|--------|
| `/new` | Create a new chat session |
| `/info` | Show current session details |
| `/sessions` | List all active sessions on server |
| `/reset` | Clear current session history |
| `/delete` | Delete current session |

## API Endpoints

### Chat Endpoints
- `POST /chat` - Send message with optional session context
- `POST /sessions/new` - Create a new chat session
- `GET /sessions/{session_id}` - Get session information
- `DELETE /sessions/{session_id}` - Delete a specific session
- `POST /sessions/{session_id}/clear` - Clear session history
- `GET /sessions` - List all active sessions

### System Endpoints
- `GET /health` - Health check with session statistics
- `GET /stats` - Detailed server and session statistics
- `GET /docs` - Interactive API documentation
- `GET /` - Server information and available endpoints

## Configuration
## Sample Output

### Multi-turn Server Logs
```
╔══════════════════════════════════════════════════════════════╗
║               🚀 FASTAPI MULTI-TURN CHAT SERVER 🚀            ║
╠══════════════════════════════════════════════════════════════╣
║  Model: gemini-2.0-flash                                      ║
║  Framework: FastAPI                                           ║
║  Multi-turn: ENABLED                                          ║
║  Status: READY                                                ║
╚══════════════════════════════════════════════════════════════╝

┌─ 📥 INCOMING REQUEST [14:32:15.123] ─────────────────────────┐
│ Client IP: 127.0.0.1                                        │
│ Method: POST /chat                                           │
│ Session: a1b2c3d4... (existing)                            │
│ Message: "What did we discuss earlier?"                      │
│ Message Length: 28 characters                               │
└────────────────────────────────────────────────────────────┘

┌─ 🧠 AI PROCESSING [14:32:15.125] ──────────────────────────────┐
│ Model: gemini-2.0-flash                                       │
│ Session: a1b2c3d4...                                          │
│ Context: 6 messages                                           │
│ Status: Generating response...                                │
│ Input: 28 chars                                              │
└────────────────────────────────────────────────────────────┘

┌─ 📤 RESPONSE GENERATED [14:32:16.847] ─────────────────────────┐
│ Processing Time: 1.722s                                       │
│ Session: a1b2c3d4...                                          │
│ Context Messages: 8                                           │
│ Response Length: 156 characters                               │
│ Status: SUCCESS                                                │
│ Response: Earlier we talked about machine learning concepts... │
└────────────────────────────────────────────────────────────┘
```

### Multi-turn Client Interface
```
💬 FASTAPI MULTI-TURN CHAT CLIENT 💬
🎉 Connected to FastAPI multi-turn server successfully!

You [a1b2c3d4...] › What did we discuss earlier?

🤖 AI Response (8 messages)
────────────────────────────────────────────────────────────
Earlier we talked about machine learning concepts, specifically 
neural networks and deep learning. You asked about the difference 
between supervised and unsupervised learning, and I explained...
────────────────────────────────────────────────────────────

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
```

### Session Management
```
You › /sessions

┌─ 📋 ALL ACTIVE SESSIONS (3) ────────────────────────────────┐
│ 1. a1b2c3d4... (8 msgs, 0:05:23, 14:26:52) ← CURRENT        
│ 2. e5f6g7h8... (12 msgs, 0:12:45, 14:15:30)                 
│ 3. i9j0k1l2... (3 msgs, 0:02:10, 14:30:15)                   
└──────────────────────────────────────────────────────────────┘

You › /new
✨ New session created successfully!
   Session ID: m3n4o5p6...
   Model: gemini-2.0-flash

You [m3n4o5p6...] › Hello, this is a new conversation!
```
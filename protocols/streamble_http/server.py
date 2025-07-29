from fastapi.middleware.cors import CORSMiddleware
from shared.setup import initialize_genai_client
from fastapi.responses import StreamingResponse
from fastapi.responses import HTMLResponse 
from shared.llm import create_chat_session
from contextlib import asynccontextmanager
from shared.llm import ChatSession
from fastapi import HTTPException
from typing import AsyncGenerator
from pydantic import BaseModel
from datetime import datetime
from fastapi import Request
from fastapi import FastAPI
from typing import Optional 
from colorama import Style
from colorama import Fore
from colorama import Back
from colorama import init 
from typing import List 
from typing import Dict
import asyncio
import uvicorn
import uuid
import json
import time
import os

# Initialize colorama for cross-platform colored output
init(autoreset=True)


# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatStreamRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class NewSessionRequest(BaseModel):
    model_id: Optional[str] = None


class NewSessionResponse(BaseModel):
    session_id: str
    model: str
    timestamp: str


class SessionInfoResponse(BaseModel):
    session_id: str
    model: str
    message_count: int
    session_duration_seconds: float
    user_messages: int
    model_messages: int
    created_at: str


class HealthResponse(BaseModel):
    status: str
    model: str
    uptime_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    active_sessions: int
    streaming_connections: int


class StatsResponse(BaseModel):
    uptime_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    model: str
    start_time: str
    active_sessions: int
    total_sessions_created: int
    streaming_connections: int

# Configuration
MODEL_ID = os.environ.get('GENAI_MODEL_ID', 'gemini-2.0-flash')

# Global variables
chat_sessions: Dict[str, ChatSession] = {}
session_metadata: Dict[str, dict] = {}
active_streams: Dict[str, dict] = {}
chat_stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'total_response_time': 0,
    'total_sessions_created': 0,
    'streaming_connections': 0,
    'start_time': datetime.now()
}

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print_banner()
    print(f"\n{Fore.GREEN}🚀 FastAPI Streamable HTTP Multi-turn Chat Server starting up...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 API Documentation: http://localhost:8000/docs{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📊 Statistics endpoint: http://localhost:8000/stats{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}❤️  Health check: http://localhost:8000/health{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🌊 Stream Demo: http://localhost:8000/demo{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔧 Use Ctrl+C to stop the server{Style.RESET_ALL}\n")
    
    yield
    
    # Shutdown
    print(f"\n\n{Fore.YELLOW}👋 FastAPI Streamable HTTP server shutting down gracefully...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}💭 Active sessions: {len(chat_sessions)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🌊 Active streams: {len(active_streams)}{Style.RESET_ALL}")
    print_stats()
    print(f"{Fore.GREEN}✅ Server stopped successfully!{Style.RESET_ALL}")

# FastAPI app initialization
app = FastAPI(
    title="Streamable HTTP Multi-turn Chat API",
    description="FastAPI-based streamable HTTP multi-turn chat server with chunked streaming",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def print_banner():
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║             📡 FASTAPI STREAMABLE HTTP CHAT SERVER 📡         ║
╠══════════════════════════════════════════════════════════════╣
║  Model: {MODEL_ID:<48} ║
║  Framework: FastAPI + HTTP Streaming{' ' * 27} ║
║  Multi-turn: {Fore.GREEN}ENABLED{Fore.CYAN}{' ' * 41} ║
║  Streaming: {Fore.GREEN}CHUNKED HTTP{Fore.CYAN}{' ' * 36} ║
║  Status: {Fore.GREEN}READY{Fore.CYAN}{' ' * 45} ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "Unknown"

def create_new_session(model_id: str = None) -> tuple[str, ChatSession]:
    """
    Create a new chat session
    """
    session_id = str(uuid.uuid4())
    if model_id is None:
        model_id = MODEL_ID
    
    try:
        chat_session = create_chat_session(model_id)
        chat_sessions[session_id] = chat_session
        session_metadata[session_id] = {
            'created_at': datetime.now(),
            'model_id': model_id,
            'last_activity': datetime.now()
        }
        chat_stats['total_sessions_created'] += 1
        
        print(f"{Fore.CYAN}INFO: Created new session {session_id} with model {model_id}{Style.RESET_ALL}")
        return session_id, chat_session
    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to create new session: {e}{Style.RESET_ALL}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")

def get_or_create_session(session_id: str = None, model_id: str = None) -> tuple[str, ChatSession, bool]:
    """
    Get existing session or create new one
    """
    is_new_session = False
    
    if session_id is None or session_id not in chat_sessions:
        session_id, chat_session = create_new_session(model_id)
        is_new_session = True
    else:
        chat_session = chat_sessions[session_id]
        session_metadata[session_id]['last_activity'] = datetime.now()
    
    return session_id, chat_session, is_new_session

def log_stream_start(session_id: str, client_ip: str, message: str):
    """
    Log the start of an HTTP stream
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.MAGENTA}┌─ 📡 HTTP STREAM STARTED [{timestamp}] ───────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Client IP: {Fore.GREEN}{client_ip}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Message: {Fore.WHITE}\"{message[:40]}{'...' if len(message) > 40 else ''}\"{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Active Streams: {len(active_streams) + 1}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Transfer-Encoding: chunked")
    print(f"{Fore.MAGENTA}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def log_stream_end(session_id: str, total_chunks: int, total_time: float):
    """
    Log the end of an HTTP stream
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.GREEN}┌─ 📡 HTTP STREAM COMPLETED [{timestamp}] ──────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Total Chunks: {total_chunks}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Total Time: {Fore.YELLOW}{total_time:.3f}s{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Active Streams: {len(active_streams)}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Status: {Fore.GREEN}SUCCESS{Style.RESET_ALL}")
    print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def log_stream_chunk(session_id: str, chunk_num: int, chunk_text: str):
    """
    Log individual stream chunks
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    preview = chunk_text[:30].replace('\n', ' ') + ('...' if len(chunk_text) > 30 else '')
    
    print(f"{Fore.YELLOW}📡 [{timestamp}] Chunk #{chunk_num}: \"{preview}\"{Style.RESET_ALL}")

def print_stats():
    """
    Print current server statistics
    """
    uptime = datetime.now() - chat_stats['start_time']
    avg_response_time = (chat_stats['total_response_time'] / chat_stats['successful_requests'] 
                        if chat_stats['successful_requests'] > 0 else 0)
    
    print(f"\n{Fore.CYAN}┌─ 📊 STREAMABLE HTTP SERVER STATISTICS ──────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Uptime: {str(uptime).split('.')[0]}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Requests: {Fore.YELLOW}{chat_stats['total_requests']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Successful: {Fore.GREEN}{chat_stats['successful_requests']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Failed: {Fore.RED}{chat_stats['failed_requests']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Active Sessions: {Fore.MAGENTA}{len(chat_sessions)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Active Streams: {Fore.MAGENTA}{len(active_streams)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Sessions: {Fore.MAGENTA}{chat_stats['total_sessions_created']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Avg Response Time: {Fore.YELLOW}{avg_response_time:.3f}s{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

async def generate_chat_stream(chat_session: ChatSession, user_message: str, session_id: str, client_ip: str) -> AsyncGenerator[str, None]:
    """
    Generate streaming chat response using HTTP chunked transfer
    """
    stream_id = str(uuid.uuid4())
    start_time = time.time()
    chunk_count = 0
    
    try:
        # Track active stream
        active_streams[stream_id] = {
            'session_id': session_id,
            'client_ip': client_ip,
            'start_time': start_time
        }
        chat_stats['streaming_connections'] += 1
        
        # Log stream start
        log_stream_start(session_id, client_ip, user_message)
        
        # Send initial stream info as JSON chunk
        yield json.dumps({
            'type': 'session_info', 
            'session_id': session_id, 
            'model': chat_session.model_id,
            'timestamp': datetime.now().isoformat()
        }) + '\n'
        
        # Add user message to session
        chat_session.add_message("user", user_message)
        
        # Send status update as JSON chunk
        yield json.dumps({
            'type': 'status', 
            'message': 'Generating response...', 
            'context_messages': chat_session.get_message_count()
        }) + '\n'
        
        # Generate response using chat session
        try:
            # Generate full response first (since GenAI doesn't have native streaming yet)
            full_response = chat_session.client.models.generate_content(
                model=chat_session.model_id,
                contents=chat_session.chat_history
            )
            response_text = full_response.text.strip()
            
            # Add model response to history
            chat_session.add_message("model", response_text)
            
            # Simulate streaming by sending chunks
            words = response_text.split()
            current_chunk = ""
            
            for i, word in enumerate(words):
                current_chunk += word + " "
                
                # Send chunk every 3-5 words or at end
                if (i + 1) % 4 == 0 or i == len(words) - 1:
                    chunk_count += 1
                    chunk_data = {
                        'type': 'chunk',
                        'text': current_chunk.strip(),
                        'chunk_number': chunk_count,
                        'is_final': i == len(words) - 1,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    yield json.dumps(chunk_data) + '\n'
                    
                    # Log chunk
                    log_stream_chunk(session_id, chunk_count, current_chunk.strip())
                    current_chunk = ""
                    
                    # Simulate natural typing delay
                    await asyncio.sleep(0.1)
            
            # Send completion info as final JSON chunk
            total_time = time.time() - start_time
            completion_data = {
                'type': 'complete',
                'total_chunks': chunk_count,
                'processing_time': round(total_time, 3),
                'message_count': chat_session.get_message_count(),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            yield json.dumps(completion_data) + '\n'
            
            # Update statistics
            chat_stats['successful_requests'] += 1
            chat_stats['total_response_time'] += total_time
            
            # Log completion
            log_stream_end(session_id, chunk_count, total_time)
            
        except Exception as e:
            # Send error as JSON chunk
            error_data = {
                'type': 'error',
                'message': str(e),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            yield json.dumps(error_data) + '\n'
            
            chat_stats['failed_requests'] += 1
            print(f"{Fore.RED}ERROR: Error in stream generation: {e}{Style.RESET_ALL}")
            
    finally:
        # Clean up stream tracking
        if stream_id in active_streams:
            del active_streams[stream_id]
        chat_stats['streaming_connections'] = max(0, chat_stats['streaming_connections'] - 1)

@app.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest, http_request: Request):
    """
    Main HTTP streaming chat endpoint with chunked transfer encoding
    """
    client_ip = get_client_ip(http_request)
    chat_stats['total_requests'] += 1
    
    try:
        # Get or create session
        session_id, chat_session, is_new_session = get_or_create_session(request.session_id)
        
        user_message = request.message.strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Return HTTP streaming response with chunked transfer encoding
        return StreamingResponse(
            generate_chat_stream(chat_session, user_message, session_id, client_ip),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        chat_stats['failed_requests'] += 1
        print(f"{Fore.RED}ERROR: Error in chat stream: {e}{Style.RESET_ALL}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/sessions/new", response_model=NewSessionResponse)
async def create_session(request: NewSessionRequest):
    """
    Create a new chat session
    """
    try:
        model_id = request.model_id or MODEL_ID
        session_id, chat_session = create_new_session(model_id)
        
        return NewSessionResponse(
            session_id=session_id,
            model=model_id,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        print(f"{Fore.RED}ERROR: Error creating session: {e}{Style.RESET_ALL}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@app.get("/sessions/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    """
    Get information about a specific session
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    chat_session = chat_sessions[session_id]
    metadata = session_metadata[session_id]
    summary = chat_session.get_conversation_summary()
    
    return SessionInfoResponse(
        session_id=session_id,
        model=summary['model_id'],
        message_count=summary['total_messages'],
        session_duration_seconds=summary['session_duration_seconds'],
        user_messages=summary['user_messages'],
        model_messages=summary['model_messages'],
        created_at=metadata['created_at'].isoformat()
    )

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a specific session
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del chat_sessions[session_id]
    del session_metadata[session_id]
    
    return {"message": f"Session {session_id} deleted successfully"}

@app.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """
    Clear the history of a specific session
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    chat_sessions[session_id].clear_history()
    session_metadata[session_id]['last_activity'] = datetime.now()
    
    return {"message": f"Session {session_id} history cleared successfully"}

@app.get("/sessions")
async def list_sessions():
    """
    List all active sessions
    """
    sessions = []
    for session_id, metadata in session_metadata.items():
        chat_session = chat_sessions[session_id]
        summary = chat_session.get_conversation_summary()
        
        sessions.append({
            "session_id": session_id,
            "model": summary['model_id'],
            "message_count": summary['total_messages'],
            "duration_minutes": summary['session_duration_minutes'],
            "created_at": metadata['created_at'].isoformat(),
            "last_activity": metadata['last_activity'].isoformat()
        })
    
    return {"active_sessions": len(sessions), "sessions": sessions}

@app.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Health check endpoint with detailed status
    """
    uptime = datetime.now() - chat_stats['start_time']
    
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    client_ip = get_client_ip(request)
    
    print(f"\n{Fore.BLUE}┌─ ❤️  HEALTH CHECK [{timestamp}] ──────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Client IP: {Fore.GREEN}{client_ip}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Status: {Fore.GREEN}HEALTHY{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Uptime: {str(uptime).split('.')[0]}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Active Sessions: {Fore.MAGENTA}{len(chat_sessions)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Active Streams: {Fore.MAGENTA}{len(active_streams)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
    
    return HealthResponse(
        status='healthy',
        model=MODEL_ID,
        uptime_seconds=int(uptime.total_seconds()),
        total_requests=chat_stats['total_requests'],
        successful_requests=chat_stats['successful_requests'],
        failed_requests=chat_stats['failed_requests'],
        active_sessions=len(chat_sessions),
        streaming_connections=len(active_streams)
    )

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Detailed statistics endpoint
    """
    uptime = datetime.now() - chat_stats['start_time']
    avg_response_time = (chat_stats['total_response_time'] / chat_stats['successful_requests'] 
                        if chat_stats['successful_requests'] > 0 else 0)
    
    return StatsResponse(
        uptime_seconds=int(uptime.total_seconds()),
        total_requests=chat_stats['total_requests'],
        successful_requests=chat_stats['successful_requests'],
        failed_requests=chat_stats['failed_requests'],
        average_response_time=round(avg_response_time, 3),
        model=MODEL_ID,
        start_time=chat_stats['start_time'].isoformat(),
        active_sessions=len(chat_sessions),
        total_sessions_created=chat_stats['total_sessions_created'],
        streaming_connections=len(active_streams)
    )

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """
    Simple demo page for testing HTTP streaming
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HTTP Streaming Chat Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1e1e1e; color: #fff; }
            .container { max-width: 800px; margin: 0 auto; }
            .chat-box { border: 1px solid #444; height: 400px; overflow-y: auto; padding: 10px; background: #2d2d2d; margin-bottom: 10px; border-radius: 5px; }
            .input-box { width: 70%; padding: 10px; background: #333; border: 1px solid #555; color: #fff; border-radius: 3px; }
            .send-btn { padding: 10px 20px; background: #007acc; color: white; border: none; cursor: pointer; border-radius: 3px; margin-left: 10px; }
            .send-btn:hover { background: #005a9e; }
            .message { margin: 5px 0; padding: 8px; border-radius: 5px; }
            .user { background: #0066cc; text-align: right; }
            .ai { background: #333; }
            .status { background: #666; font-style: italic; }
            .error { background: #cc0000; }
            .session-info { background: #006600; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📡 HTTP Streaming Multi-turn Chat Demo</h1>
            <div id="chat" class="chat-box"></div>
            <input type="text" id="messageInput" class="input-box" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()" class="send-btn">Send</button>
            <button onclick="newSession()" class="send-btn">New Session</button>
        </div>

        <script>
            let currentSessionId = null;

            function addMessage(content, className) {
                const chat = document.getElementById('chat');
                const message = document.createElement('div');
                message.className = 'message ' + className;
                message.innerHTML = content;
                chat.appendChild(message);
                chat.scrollTop = chat.scrollHeight;
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }

            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;

                addMessage('You: ' + message, 'user');
                input.value = '';

                const requestBody = {
                    message: message,
                    session_id: currentSessionId
                };

                try {
                    const response = await fetch('/chat/stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestBody)
                    });

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let aiResponse = '';
                    let responseDiv = null;

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split('\\n');

                        for (let line of lines) {
                            if (line.trim()) {
                                try {
                                    const data = JSON.parse(line);
                                    
                                    if (data.type === 'session_info') {
                                        currentSessionId = data.session_id;
                                        addMessage(`Session: ${data.session_id.substring(0, 8)}... (${data.model})`, 'session-info');
                                    } else if (data.type === 'status') {
                                        addMessage(`Status: ${data.message} (Context: ${data.context_messages} messages)`, 'status');
                                    } else if (data.type === 'chunk') {
                                        if (!responseDiv) {
                                            responseDiv = document.createElement('div');
                                            responseDiv.className = 'message ai';
                                            responseDiv.innerHTML = 'AI: ';
                                            document.getElementById('chat').appendChild(responseDiv);
                                        }
                                        aiResponse += data.text + ' ';
                                        responseDiv.innerHTML = 'AI: ' + aiResponse;
                                        document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
                                    } else if (data.type === 'complete') {
                                        addMessage(`✅ Complete (${data.total_chunks} chunks, ${data.processing_time}s)`, 'status');
                                    } else if (data.type === 'error') {
                                        addMessage('❌ Error: ' + data.message, 'error');
                                    }
                                } catch (e) {
                                    console.error('Error parsing chunk:', e, 'Line:', line);
                                }
                            }
                        }
                    }
                } catch (error) {
                    addMessage('❌ Connection error: ' + error.message, 'error');
                }
            }

            function newSession() {
                fetch('/sessions/new', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({})
                }).then(response => response.json())
                .then(data => {
                    currentSessionId = data.session_id;
                    addMessage(`🆕 New session created: ${data.session_id.substring(0, 8)}... (${data.model})`, 'session-info');
                });
            }

            // Initialize
            addMessage('📡 HTTP Streaming Chat Demo Ready! Type a message to start or click "New Session"', 'status');
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": "GenAI Streamable HTTP Multi-turn Chat API",
        "version": "2.0.0",
        "framework": "FastAPI + HTTP Streaming",
        "model": MODEL_ID,
        "features": ["multi-turn conversations", "chunked HTTP streaming", "session management"],
        "endpoints": {
            "chat_stream": "POST /chat/stream",
            "new_session": "POST /sessions/new",
            "session_info": "GET /sessions/{session_id}",
            "delete_session": "DELETE /sessions/{session_id}",
            "clear_session": "POST /sessions/{session_id}/clear",
            "list_sessions": "GET /sessions",
            "health": "GET /health", 
            "stats": "GET /stats",
            "demo": "GET /demo",
            "docs": "GET /docs"
        }
    }


if __name__ == '__main__':
    try:
        uvicorn.run(
            app, 
            host='0.0.0.0', 
            port=8000, 
            log_level='info',
            access_log=False  # We handle our own logging
        )
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Streamable HTTP Server interrupted by user{Style.RESET_ALL}")
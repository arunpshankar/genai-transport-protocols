from fastapi.middleware.cors import CORSMiddleware
from shared.setup import initialize_genai_client
from contextlib import asynccontextmanager
from shared.llm import create_chat_session
from fastapi.responses import HTMLResponse
from fastapi import WebSocketDisconnect
from shared.llm import ChatSession
from fastapi import HTTPException
from pydantic import BaseModel
from datetime import datetime
from fastapi import WebSocket
from fastapi import Request 
from fastapi import FastAPI
from typing import Optional 
from colorama import Style
from colorama import Back
from colorama import Fore
from colorama import init 
from typing import Dict
from typing import List 
from typing import Set
import uvicorn
import asyncio
import uuid
import time
import json
import os


# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Pydantic models for request/response
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
    websocket_connections: int

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
    websocket_connections: int

# Configuration
MODEL_ID = os.environ.get('GENAI_MODEL_ID', 'gemini-2.0-flash')

# Global variables
chat_sessions: Dict[str, ChatSession] = {}
session_metadata: Dict[str, dict] = {}
websocket_connections: Dict[str, WebSocket] = {}
connection_sessions: Dict[str, str] = {}  # connection_id -> session_id
chat_stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'total_response_time': 0,
    'total_sessions_created': 0,
    'websocket_connections': 0,
    'start_time': datetime.now()
}

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print_banner()
    print(f"\n{Fore.GREEN}🚀 FastAPI WebSocket Multi-turn Chat Server starting up...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 API Documentation: http://localhost:8000/docs{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📊 Statistics endpoint: http://localhost:8000/stats{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}❤️  Health check: http://localhost:8000/health{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔌 WebSocket Demo: http://localhost:8000/demo{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔧 Use Ctrl+C to stop the server{Style.RESET_ALL}\n")
    
    yield
    
    # Shutdown
    print(f"\n\n{Fore.YELLOW}👋 FastAPI WebSocket server shutting down gracefully...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}💭 Active sessions: {len(chat_sessions)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔌 Active WebSocket connections: {len(websocket_connections)}{Style.RESET_ALL}")
    
    # Close all WebSocket connections
    for connection_id, websocket in websocket_connections.items():
        try:
            await websocket.close()
        except:
            pass
    
    print_stats()
    print(f"{Fore.GREEN}✅ Server stopped successfully!{Style.RESET_ALL}")

# FastAPI app initialization
app = FastAPI(
    title="GenAI WebSocket Multi-turn Chat API",
    description="Beautiful FastAPI-based WebSocket multi-turn chat server with real-time bidirectional communication",
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
    banner = f""" {Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
               🔌 FASTAPI WEBSOCKET CHAT SERVER 🔌             
╠══════════════════════════════════════════════════════════════╣
  Model: {MODEL_ID:<48} 
  Framework: FastAPI + WebSockets{' ' * 31} 
  Multi-turn: {Fore.GREEN}ENABLED{Fore.CYAN}{' ' * 41} 
  Real-time: {Fore.GREEN}BIDIRECTIONAL{Fore.CYAN}{' ' * 35} 
  Status: {Fore.GREEN}READY{Fore.CYAN}{' ' * 45} 
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
        
        print(f"{Fore.GREEN}✨ Created new session {session_id[:8]}... with model {model_id}{Style.RESET_ALL}")
        return session_id, chat_session
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to create new session: {e}{Style.RESET_ALL}")
        raise Exception("Failed to create chat session")

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

def print_websocket_connect(connection_id: str, client_ip: str):
    """
    Print WebSocket connection info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.MAGENTA}┌─ 🔌 WEBSOCKET CONNECTED [{timestamp}] ───────────────────────┐{Style.RESET_ALL}")
    print(f"  Connection ID: {Fore.CYAN}{connection_id[:8]}...{Style.RESET_ALL}")
    print(f"  Client IP: {Fore.GREEN}{client_ip}{Style.RESET_ALL}")
    print(f"  Active Connections: {len(websocket_connections) + 1}")
    print(f"  Protocol: WebSocket")
    print(f"{Fore.MAGENTA}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_websocket_disconnect(connection_id: str, reason: str = "Normal"):
    """
    Print WebSocket disconnection info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.YELLOW}┌─ 🔌 WEBSOCKET DISCONNECTED [{timestamp}] ─────────────────────┐{Style.RESET_ALL}")
    print(f"  Connection ID: {Fore.CYAN}{connection_id[:8]}...{Style.RESET_ALL}")
    print(f"  Reason: {reason}")
    print(f"  Active Connections: {len(websocket_connections)}")
    print(f"{Fore.YELLOW}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_message_received(connection_id: str, session_id: str, message_type: str, content: str):
    """
    Print received WebSocket message info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.BLUE}┌─ 📩 WEBSOCKET MESSAGE [{timestamp}] ──────────────────────────┐{Style.RESET_ALL}")
    print(f"  Connection: {Fore.CYAN}{connection_id[:8]}...{Style.RESET_ALL}")
    print(f"  Session: {Fore.CYAN}{session_id[:8] if session_id else 'None'}...{Style.RESET_ALL}")
    print(f"  Type: {message_type}")
    
    if message_type == 'chat':
        preview = content[:40] + ('...' if len(content) > 40 else '')
        print(f"  Message: {Fore.WHITE}\"{preview}\"{Style.RESET_ALL}")
    
    print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_response_start(connection_id: str, session_id: str, message_count: int):
    """
    Print response generation start info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.GREEN}┌─ 🧠 GENERATING RESPONSE [{timestamp}] ────────────────────────┐{Style.RESET_ALL}")
    print(f"  Connection: {Fore.CYAN}{connection_id[:8]}...{Style.RESET_ALL}")
    print(f"  Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
    print(f"  Context Messages: {message_count}")
    print(f"  Model: {MODEL_ID}")
    print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_chunk_sent(connection_id: str, chunk_num: int, chunk_text: str):
    """
    Print individual chunks sent info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    preview = chunk_text[:30].replace('\n', ' ') + ('...' if len(chunk_text) > 30 else '')
    
    print(f"{Fore.YELLOW}🔌 [{timestamp}] Chunk #{chunk_num} → {connection_id[:8]}...: \"{preview}\"{Style.RESET_ALL}")

def print_stats():
    """
    Print current server statistics
    """
    uptime = datetime.now() - chat_stats['start_time']
    avg_response_time = (chat_stats['total_response_time'] / chat_stats['successful_requests'] 
                        if chat_stats['successful_requests'] > 0 else 0)
    
    print(f"\n{Fore.CYAN}┌─ 📊 WEBSOCKET SERVER STATISTICS ────────────────────────────┐{Style.RESET_ALL}")
    print(f"  Uptime: {str(uptime).split('.')[0]}")
    print(f"  Total Requests: {Fore.YELLOW}{chat_stats['total_requests']}{Style.RESET_ALL}")
    print(f"  Successful: {Fore.GREEN}{chat_stats['successful_requests']}{Style.RESET_ALL}")
    print(f"  Failed: {Fore.RED}{chat_stats['failed_requests']}{Style.RESET_ALL}")
    print(f"  Active Sessions: {Fore.MAGENTA}{len(chat_sessions)}{Style.RESET_ALL}")
    print(f"  WebSocket Connections: {Fore.MAGENTA}{len(websocket_connections)}{Style.RESET_ALL}")
    print(f"  Total Sessions: {Fore.MAGENTA}{chat_stats['total_sessions_created']}{Style.RESET_ALL}")
    print(f"  Avg Response Time: {Fore.YELLOW}{avg_response_time:.3f}s{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

async def send_message(websocket: WebSocket, message_type: str, data: dict):
    """
    Send a structured message to WebSocket client
    """
    message = {
        'type': message_type,
        'timestamp': datetime.now().isoformat(),
        **data
    }
    await websocket.send_text(json.dumps(message))

async def broadcast_session_update(session_id: str, update_type: str, data: dict):
    """
    Broadcast session updates to all connected clients for this session
    """
    message = {
        'type': 'session_update',
        'session_id': session_id,
        'update_type': update_type,
        'timestamp': datetime.now().isoformat(),
        **data
    }
    
    # Send to all connections associated with this session
    disconnected = []
    for connection_id, websocket in websocket_connections.items():
        if connection_sessions.get(connection_id) == session_id:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(connection_id)
    
    # Clean up disconnected connections
    for connection_id in disconnected:
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]
        if connection_id in connection_sessions:
            del connection_sessions[connection_id]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time chat
    """
    connection_id = str(uuid.uuid4())
    client_ip = websocket.client.host if websocket.client else "Unknown"
    
    await websocket.accept()
    websocket_connections[connection_id] = websocket
    chat_stats['websocket_connections'] += 1
    
    print_websocket_connect(connection_id, client_ip)
    
    # Send welcome message
    await send_message(websocket, 'connected', {
        'connection_id': connection_id,
        'message': 'WebSocket connected successfully!',
        'server_info': {
            'model': MODEL_ID,
            'framework': 'FastAPI + WebSockets',
            'features': ['multi-turn', 'real-time', 'bidirectional']
        }
    })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get('type', 'unknown')
                
                chat_stats['total_requests'] += 1
                
                if message_type == 'ping':
                    # Handle ping/pong for connection health
                    await send_message(websocket, 'pong', {'connection_id': connection_id})
                
                elif message_type == 'create_session':
                    # Create new session
                    model_id = message.get('model_id', MODEL_ID)
                    session_id, chat_session = create_new_session(model_id)
                    connection_sessions[connection_id] = session_id
                    
                    await send_message(websocket, 'session_created', {
                        'session_id': session_id,
                        'model': model_id,
                        'connection_id': connection_id
                    })
                    
                    print_message_received(connection_id, session_id, 'create_session', model_id)
                
                elif message_type == 'join_session':
                    # Join existing session
                    session_id = message.get('session_id')
                    if session_id and session_id in chat_sessions:
                        connection_sessions[connection_id] = session_id
                        chat_session = chat_sessions[session_id]
                        
                        await send_message(websocket, 'session_joined', {
                            'session_id': session_id,
                            'model': chat_session.model_id,
                            'message_count': chat_session.get_message_count(),
                            'connection_id': connection_id
                        })
                        
                        print_message_received(connection_id, session_id, 'join_session', session_id)
                    else:
                        await send_message(websocket, 'error', {
                            'message': 'Session not found',
                            'session_id': session_id
                        })
                
                elif message_type == 'chat':
                    # Handle chat message
                    user_message = message.get('message', '').strip()
                    session_id = message.get('session_id') or connection_sessions.get(connection_id)
                    
                    if not user_message:
                        await send_message(websocket, 'error', {'message': 'Message is required'})
                        continue
                    
                    # Get or create session
                    session_id, chat_session, is_new_session = get_or_create_session(session_id)
                    connection_sessions[connection_id] = session_id
                    
                    print_message_received(connection_id, session_id, 'chat', user_message)
                    
                    if is_new_session:
                        await send_message(websocket, 'session_created', {
                            'session_id': session_id,
                            'model': chat_session.model_id,
                            'connection_id': connection_id
                        })
                    
                    # Send status update
                    await send_message(websocket, 'status', {
                        'message': 'Generating response...',
                        'session_id': session_id,
                        'context_messages': chat_session.get_message_count()
                    })
                    
                    print_response_start(connection_id, session_id, chat_session.get_message_count())
                    
                    start_time = time.time()
                    
                    try:
                        # Add user message to session
                        chat_session.add_message("user", user_message)
                        
                        # Generate full response first (since GenAI doesn't have native streaming yet)
                        full_response = chat_session.client.models.generate_content(
                            model=chat_session.model_id,
                            contents=chat_session.chat_history
                        )
                        response_text = full_response.text.strip()
                        
                        # Add model response to history
                        chat_session.add_message("model", response_text)
                        
                        # Send response start indicator
                        await send_message(websocket, 'response_start', {
                            'session_id': session_id,
                            'total_length': len(response_text)
                        })
                        
                        # Simulate streaming by sending chunks
                        words = response_text.split()
                        current_chunk = ""
                        chunk_count = 0
                        
                        for i, word in enumerate(words):
                            current_chunk += word + " "
                            
                            # Send chunk every 3-5 words or at end
                            if (i + 1) % 4 == 0 or i == len(words) - 1:
                                chunk_count += 1
                                chunk_text = current_chunk.strip()
                                
                                await send_message(websocket, 'chunk', {
                                    'text': chunk_text,
                                    'chunk_number': chunk_count,
                                    'is_final': i == len(words) - 1,
                                    'session_id': session_id
                                })
                                
                                print_chunk_sent(connection_id, chunk_count, chunk_text)
                                current_chunk = ""
                                
                                # Simulate natural typing delay
                                await asyncio.sleep(0.1)
                        
                        # Send completion info
                        total_time = time.time() - start_time
                        await send_message(websocket, 'response_complete', {
                            'total_chunks': chunk_count,
                            'processing_time': round(total_time, 3),
                            'message_count': chat_session.get_message_count(),
                            'session_id': session_id,
                            'full_response': response_text
                        })
                        
                        # Update statistics
                        chat_stats['successful_requests'] += 1
                        chat_stats['total_response_time'] += total_time
                        
                        # Broadcast session update to other clients
                        await broadcast_session_update(session_id, 'message_added', {
                            'message_count': chat_session.get_message_count(),
                            'last_message_preview': user_message[:50] + ('...' if len(user_message) > 50 else '')
                        })
                        
                    except Exception as e:
                        chat_stats['failed_requests'] += 1
                        await send_message(websocket, 'error', {
                            'message': f'Error generating response: {str(e)}',
                            'session_id': session_id
                        })
                        print(f"{Fore.RED}❌ Error in chat generation: {e}{Style.RESET_ALL}")
                
                elif message_type == 'typing_start':
                    # Handle typing indicator
                    session_id = connection_sessions.get(connection_id)
                    if session_id:
                        await broadcast_session_update(session_id, 'user_typing', {
                            'connection_id': connection_id,
                            'typing': True
                        })
                
                elif message_type == 'typing_stop':
                    # Handle typing stop
                    session_id = connection_sessions.get(connection_id)
                    if session_id:
                        await broadcast_session_update(session_id, 'user_typing', {
                            'connection_id': connection_id,
                            'typing': False
                        })
                
                else:
                    await send_message(websocket, 'error', {
                        'message': f'Unknown message type: {message_type}'
                    })
                    
            except json.JSONDecodeError:
                await send_message(websocket, 'error', {
                    'message': 'Invalid JSON format'
                })
            except Exception as e:
                await send_message(websocket, 'error', {
                    'message': f'Server error: {str(e)}'
                })
                print(f"{Fore.RED}❌ WebSocket error: {e}{Style.RESET_ALL}")
                
    except WebSocketDisconnect:
        print_websocket_disconnect(connection_id, "Client disconnected")
    except Exception as e:
        print_websocket_disconnect(connection_id, f"Error: {str(e)}")
    finally:
        # Clean up connection
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]
        if connection_id in connection_sessions:
            session_id = connection_sessions[connection_id]
            del connection_sessions[connection_id]
            
            # Notify other clients about disconnection
            try:
                await broadcast_session_update(session_id, 'user_disconnected', {
                    'connection_id': connection_id
                })
            except:
                pass
        
        chat_stats['websocket_connections'] = max(0, chat_stats['websocket_connections'] - 1)

@app.post("/sessions/new", response_model=NewSessionResponse)
async def create_session_http(request: NewSessionRequest):
    """
    Create a new chat session via HTTP
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
        print(f"{Fore.RED}❌ Error creating session: {e}{Style.RESET_ALL}")
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
    
    # Notify connected clients
    try:
        await broadcast_session_update(session_id, 'session_deleted', {})
    except:
        pass
    
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
    
    # Notify connected clients
    try:
        await broadcast_session_update(session_id, 'session_cleared', {})
    except:
        pass
    
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
        
        # Count connected clients for this session
        connected_clients = sum(1 for conn_session in connection_sessions.values() if conn_session == session_id)
        
        sessions.append({
            "session_id": session_id,
            "model": summary['model_id'],
            "message_count": summary['total_messages'],
            "duration_minutes": summary['session_duration_minutes'],
            "connected_clients": connected_clients,
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
    print(f"  Client IP: {Fore.GREEN}{client_ip}{Style.RESET_ALL}")
    print(f"  Status: {Fore.GREEN}HEALTHY{Style.RESET_ALL}")
    print(f"  Uptime: {str(uptime).split('.')[0]}")
    print(f"  Active Sessions: {Fore.MAGENTA}{len(chat_sessions)}{Style.RESET_ALL}")
    print(f"  WebSocket Connections: {Fore.MAGENTA}{len(websocket_connections)}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
    
    return HealthResponse(
        status='healthy',
        model=MODEL_ID,
        uptime_seconds=int(uptime.total_seconds()),
        total_requests=chat_stats['total_requests'],
        successful_requests=chat_stats['successful_requests'],
        failed_requests=chat_stats['failed_requests'],
        active_sessions=len(chat_sessions),
        websocket_connections=len(websocket_connections)
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
        websocket_connections=len(websocket_connections)
    )

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """
    Interactive WebSocket demo page
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Chat Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1e1e1e; color: #fff; }
            .container { max-width: 900px; margin: 0 auto; }
            .chat-box { border: 1px solid #444; height: 400px; overflow-y: auto; padding: 10px; background: #2d2d2d; margin-bottom: 10px; border-radius: 5px; }
            .input-container { display: flex; gap: 10px; margin-bottom: 10px; }
            .input-box { flex: 1; padding: 10px; background: #333; border: 1px solid #555; color: #fff; border-radius: 3px; }
            .send-btn { padding: 10px 20px; background: #007acc; color: white; border: none; cursor: pointer; border-radius: 3px; }
            .send-btn:hover { background: #005a9e; }
            .send-btn:disabled { background: #666; cursor: not-allowed; }
            .control-panel { display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
            .status-bar { background: #333; padding: 8px; border-radius: 3px; margin-bottom: 10px; font-size: 12px; }
            .message { margin: 5px 0; padding: 8px; border-radius: 5px; }
            .user { background: #0066cc; text-align: right; }
            .ai { background: #333; }
            .system { background: #666; font-style: italic; font-size: 12px; }
            .error { background: #cc0000; }
            .typing-indicator { background: #444; font-style: italic; animation: pulse 2s infinite; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .connected { color: #4CAF50; }
            .disconnected { color: #f44336; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔌 WebSocket Multi-turn Chat Demo</h1>
            
            <div class="status-bar">
                Status: <span id="connectionStatus" class="disconnected">Disconnected</span> |
                Session: <span id="sessionInfo">None</span> |
                Messages: <span id="messageCount">0</span>
            </div>
            
            <div class="control-panel">
                <button onclick="connect()" class="send-btn" id="connectBtn">Connect</button>
                <button onclick="disconnect()" class="send-btn" id="disconnectBtn" disabled>Disconnect</button>
                <button onclick="createSession()" class="send-btn" id="createSessionBtn" disabled>New Session</button>
                <button onclick="clearChat()" class="send-btn">Clear Chat</button>
            </div>
            
            <div id="chat" class="chat-box"></div>
            
            <div class="input-container">
                <input type="text" id="messageInput" class="input-box" placeholder="Type your message..." 
                       onkeypress="handleKeyPress(event)" oninput="handleTyping()" disabled>
                <button onclick="sendMessage()" class="send-btn" id="sendBtn" disabled>Send</button>
            </div>
        </div>

        <script>
            let ws = null;
            let currentSessionId = null;
            let messageCount = 0;
            let isConnected = false;
            let typingTimer = null;
            let isTyping = false;

            function updateStatus() {
                document.getElementById('connectionStatus').textContent = isConnected ? 'Connected' : 'Disconnected';
                document.getElementById('connectionStatus').className = isConnected ? 'connected' : 'disconnected';
                document.getElementById('sessionInfo').textContent = currentSessionId ? currentSessionId.substring(0, 8) + '...' : 'None';
                document.getElementById('messageCount').textContent = messageCount;
                
                document.getElementById('connectBtn').disabled = isConnected;
                document.getElementById('disconnectBtn').disabled = !isConnected;
                document.getElementById('createSessionBtn').disabled = !isConnected;
                document.getElementById('messageInput').disabled = !isConnected;
                document.getElementById('sendBtn').disabled = !isConnected;
            }

            function addMessage(content, className) {
                const chat = document.getElementById('chat');
                const message = document.createElement('div');
                message.className = 'message ' + className;
                message.innerHTML = content;
                chat.appendChild(message);
                chat.scrollTop = chat.scrollHeight;
            }

            function connect() {
                ws = new WebSocket('ws://localhost:8000/ws');
                
                ws.onopen = function(event) {
                    isConnected = true;
                    updateStatus();
                    addMessage('🔌 WebSocket connected!', 'system');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    switch(data.type) {
                        case 'connected':
                            addMessage(`✅ ${data.message}`, 'system');
                            addMessage(`Server: ${data.server_info.framework} (${data.server_info.model})`, 'system');
                            break;
                            
                        case 'session_created':
                        case 'session_joined':
                            currentSessionId = data.session_id;
                            messageCount = data.message_count || 0;
                            updateStatus();
                            addMessage(`📋 Session: ${data.session_id.substring(0, 8)}... (${data.model})`, 'system');
                            break;
                            
                        case 'status':
                            addMessage(`💭 ${data.message}`, 'system');
                            break;
                            
                        case 'response_start':
                            // Create a new response div
                            const chat = document.getElementById('chat');
                            const responseDiv = document.createElement('div');
                            responseDiv.className = 'message ai';
                            responseDiv.id = 'current-response';
                            responseDiv.innerHTML = 'AI: ';
                            chat.appendChild(responseDiv);
                            chat.scrollTop = chat.scrollHeight;
                            break;
                            
                        case 'chunk':
                            const currentResponse = document.getElementById('current-response');
                            if (currentResponse) {
                                currentResponse.innerHTML += data.text + ' ';
                                document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
                            }
                            break;
                            
                        case 'response_complete':
                            const responseElement = document.getElementById('current-response');
                            if (responseElement) {
                                responseElement.id = ''; // Remove the ID
                            }
                            messageCount = data.message_count;
                            updateStatus();
                            addMessage(`✅ Response complete (${data.total_chunks} chunks, ${data.processing_time}s)`, 'system');
                            break;
                            
                        case 'session_update':
                            if (data.update_type === 'user_typing' && data.typing) {
                                addMessage('👤 Someone is typing...', 'typing-indicator');
                                setTimeout(() => {
                                    const typingElements = document.querySelectorAll('.typing-indicator');
                                    typingElements.forEach(el => el.remove());
                                }, 3000);
                            }
                            break;
                            
                        case 'error':
                            addMessage('❌ Error: ' + data.message, 'error');
                            break;
                            
                        case 'pong':
                            // Handle ping/pong
                            break;
                    }
                };
                
                ws.onclose = function(event) {
                    isConnected = false;
                    updateStatus();
                    addMessage('🔌 WebSocket disconnected', 'system');
                };
                
                ws.onerror = function(error) {
                    addMessage('❌ WebSocket error: ' + error, 'error');
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                }
            }

            function createSession() {
                if (ws && isConnected) {
                    ws.send(JSON.stringify({
                        type: 'create_session'
                    }));
                }
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message || !isConnected) return;

                addMessage('You: ' + message, 'user');
                
                ws.send(JSON.stringify({
                    type: 'chat',
                    message: message,
                    session_id: currentSessionId
                }));
                
                input.value = '';
                stopTyping();
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }

            function handleTyping() {
                if (!isTyping && isConnected) {
                    isTyping = true;
                    ws.send(JSON.stringify({
                        type: 'typing_start'
                    }));
                }
                
                clearTimeout(typingTimer);
                typingTimer = setTimeout(stopTyping, 2000);
            }

            function stopTyping() {
                if (isTyping && isConnected) {
                    isTyping = false;
                    ws.send(JSON.stringify({
                        type: 'typing_stop'
                    }));
                }
                clearTimeout(typingTimer);
            }

            function clearChat() {
                document.getElementById('chat').innerHTML = '';
            }

            // Initialize
            updateStatus();
            addMessage('🔌 WebSocket Chat Demo Ready! Click "Connect" to start', 'system');
            
            // Ping every 30 seconds to keep connection alive
            setInterval(() => {
                if (ws && isConnected) {
                    ws.send(JSON.stringify({type: 'ping'}));
                }
            }, 30000);
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
        "name": "GenAI WebSocket Multi-turn Chat API",
        "version": "2.0.0",
        "framework": "FastAPI + WebSockets",
        "model": MODEL_ID,
        "features": ["multi-turn conversations", "real-time bidirectional communication", "session management", "typing indicators"],
        "endpoints": {
            "websocket": "WS /ws",
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
        print(f"\n{Fore.YELLOW}👋 WebSocket Server interrupted by user{Style.RESET_ALL}")
from fastapi.middleware.cors import CORSMiddleware
from shared.setup import initialize_genai_client
from contextlib import asynccontextmanager
from shared.llm import create_chat_session
from shared.llm import ChatSession
from fastapi import HTTPException 
from shared.logger import logger
from pydantic import BaseModel
from datetime import datetime
from fastapi import FastAPI
from typing import Optional 
from fastapi import Request
from colorama import Style
from colorama import Fore
from colorama import Back
from colorama import init
from typing import Dict
from typing import List 
import uvicorn
import time
import uuid
import os


# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    processing_time: float
    model: str
    timestamp: str
    message_count: int
    is_new_session: bool


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


# Configuration
MODEL_ID = os.environ.get('GENAI_MODEL_ID', 'gemini-2.0-flash')

# Global variables
chat_sessions: Dict[str, ChatSession] = {}
session_metadata: Dict[str, dict] = {}
chat_stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'total_response_time': 0,
    'total_sessions_created': 0,
    'start_time': datetime.now()
}

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print_banner()
    print(f"\n{Fore.GREEN}🚀 HTTP REST Multi-turn Chat Server starting up...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 API Documentation: http://localhost:8000/docs{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📊 Statistics endpoint: http://localhost:8000/stats{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}❤️  Health check: http://localhost:8000/health{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔧 Use Ctrl+C to stop the server{Style.RESET_ALL}\n")
    
    yield
    
    # Shutdown
    print(f"\n\n{Fore.YELLOW}👋 HTTP REST server shutting down gracefully...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}💭 Active sessions: {len(chat_sessions)}{Style.RESET_ALL}")
    print_stats()
    print(f"{Fore.GREEN}✅ Server stopped successfully!{Style.RESET_ALL}")

# FastAPI app initialization
app = FastAPI(
    title="GenAI Multi-turn Chat API",
    description="HTTP REST-based multi-turn chat server with GenAI integration",
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
    banner = f"""{Fore.CYAN}══════════════════════════════════════════════════════════════
               🚀 HTTP REST MULTI-TURN CHAT SERVER 🚀            
══════════════════════════════════════════════════════════════
  Model: {MODEL_ID:<48} 
  Framework: FastAPI{' ' * 41} 
  Multi-turn: {Fore.GREEN}ENABLED{Fore.CYAN}{' ' * 41} 
  Status: {Fore.GREEN}READY{Fore.CYAN}{' ' * 45} 
══════════════════════════════════════════════════════════════{Style.RESET_ALL}
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
        
        logger.info(f"Created new session {session_id} with model {model_id}")
        return session_id, chat_session
    except Exception as e:
        logger.error(f"Failed to create new session: {e}")
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

def log_request_details(request_data: ChatRequest, client_ip: str, content_length: int, session_info: str):
    """
    Log detailed request information
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.YELLOW}┌─ 📥 INCOMING REQUEST [{timestamp}] ─────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}│{Style.RESET_ALL} Client IP: {Fore.GREEN}{client_ip}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}│{Style.RESET_ALL} Method: {Fore.BLUE}POST{Style.RESET_ALL} /chat")
    print(f"{Fore.YELLOW}│{Style.RESET_ALL} Session: {session_info}")
    print(f"{Fore.YELLOW}│{Style.RESET_ALL} Content-Length: {content_length} bytes")
    
    message = request_data.message
    message_preview = (message[:50] + '...') if len(message) > 50 else message
    print(f"{Fore.YELLOW}│{Style.RESET_ALL} Message: {Fore.WHITE}\"{message_preview}\"{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}│{Style.RESET_ALL} Message Length: {len(message)} characters")
    
    print(f"{Fore.YELLOW}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def log_processing(user_message: str, session_id: str, message_count: int):
    """
    Log AI processing information
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.MAGENTA}┌─ 🧠 AI PROCESSING [{timestamp}] ──────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Model: {Fore.CYAN}{MODEL_ID}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Context: {message_count} messages")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Status: {Fore.YELLOW}Generating response...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Input: {len(user_message)} chars")
    print(f"{Fore.MAGENTA}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def log_response_details(response_text: str, processing_time: float, session_id: str, message_count: int):
    """
    Log detailed response information
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.GREEN}┌─ 📤 RESPONSE GENERATED [{timestamp}] ─────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Processing Time: {Fore.YELLOW}{processing_time:.3f}s{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Context Messages: {message_count}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Response Length: {len(response_text)} characters")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Status: {Fore.GREEN}SUCCESS{Style.RESET_ALL}")
    
    # Show response preview
    response_preview = (response_text[:100] + '...') if len(response_text) > 100 else response_text
    response_lines = response_preview.split('\n')
    for i, line in enumerate(response_lines[:3]):  # Show max 3 lines
        prefix = "│ Response: " if i == 0 else "│           "
        print(f"{Fore.GREEN}{prefix}{Style.RESET_ALL}{line}")
    
    if len(response_lines) > 3:
        print(f"{Fore.GREEN}│           {Fore.YELLOW}... (truncated){Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def log_error_details(error: Exception, processing_time: float):
    """
    Log detailed error information
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.RED}┌─ ❌ ERROR [{timestamp}] ──────────────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.RED}│{Style.RESET_ALL} Processing Time: {Fore.YELLOW}{processing_time:.3f}s{Style.RESET_ALL}")
    print(f"{Fore.RED}│{Style.RESET_ALL} Error Type: {Fore.RED}{type(error).__name__}{Style.RESET_ALL}")
    print(f"{Fore.RED}│{Style.RESET_ALL} Error Message: {Fore.RED}{str(error)}{Style.RESET_ALL}")
    print(f"{Fore.RED}│{Style.RESET_ALL} Status: {Fore.RED}FAILED{Style.RESET_ALL}")
    print(f"{Fore.RED}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_stats():
    """
    Print current server statistics
    """
    uptime = datetime.now() - chat_stats['start_time']
    avg_response_time = (chat_stats['total_response_time'] / chat_stats['successful_requests'] 
                        if chat_stats['successful_requests'] > 0 else 0)
    
    print(f"\n{Fore.CYAN}┌─ 📊 SERVER STATISTICS ──────────────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Uptime: {str(uptime).split('.')[0]}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Requests: {Fore.YELLOW}{chat_stats['total_requests']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Successful: {Fore.GREEN}{chat_stats['successful_requests']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Failed: {Fore.RED}{chat_stats['failed_requests']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Active Sessions: {Fore.MAGENTA}{len(chat_sessions)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Sessions: {Fore.MAGENTA}{chat_stats['total_sessions_created']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Avg Response Time: {Fore.YELLOW}{avg_response_time:.3f}s{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """
    Main chat endpoint with multi-turn support
    """
    start_time = time.time()
    client_ip = get_client_ip(http_request)
    
    # Update statistics
    chat_stats['total_requests'] += 1
    
    try:
        # Get or create session
        session_id, chat_session, is_new_session = get_or_create_session(request.session_id)
        
        # Get content length from request
        content_length = len(request.message.encode('utf-8'))
        
        # Session info for logging
        session_info = f"{Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL} ({'new' if is_new_session else 'existing'})"
        
        # Log request details
        log_request_details(request, client_ip, content_length, session_info)
        
        user_message = request.message.strip()
        
        if not user_message:
            processing_time = time.time() - start_time
            chat_stats['failed_requests'] += 1
            log_error_details(ValueError("Empty message received"), processing_time)
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Log processing start
        message_count = chat_session.get_message_count()
        log_processing(user_message, session_id, message_count)
        logger.info(f"Processing message from {client_ip} in session {session_id}")
        
        # Generate response using chat session
        response_text = chat_session.generate_response(user_message)
        processing_time = time.time() - start_time
        
        # Update statistics
        chat_stats['successful_requests'] += 1
        chat_stats['total_response_time'] += processing_time
        
        # Get updated message count
        updated_message_count = chat_session.get_message_count()
        
        # Log response details
        log_response_details(response_text, processing_time, session_id, updated_message_count)
        logger.info(f"Generated response for {client_ip} in session {session_id} in {processing_time:.3f}s")
        
        # Print updated statistics
        print_stats()
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            processing_time=round(processing_time, 3),
            model=chat_session.model_id,
            timestamp=datetime.now().isoformat(),
            message_count=updated_message_count,
            is_new_session=is_new_session
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        chat_stats['failed_requests'] += 1
        
        log_error_details(e, processing_time)
        logger.error(f"Error processing request from {client_ip}: {e}")
        
        print_stats()
        
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Internal server error',
                'processing_time': round(processing_time, 3),
                'timestamp': datetime.now().isoformat()
            }
        )

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
        logger.error(f"Error creating session: {e}")
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
    print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
    
    return HealthResponse(
        status='healthy',
        model=MODEL_ID,
        uptime_seconds=int(uptime.total_seconds()),
        total_requests=chat_stats['total_requests'],
        successful_requests=chat_stats['successful_requests'],
        failed_requests=chat_stats['failed_requests'],
        active_sessions=len(chat_sessions)
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
        total_sessions_created=chat_stats['total_sessions_created']
    )

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": "GenAI Multi-turn Chat API",
        "version": "2.0.0",
        "framework": "FastAPI",
        "model": MODEL_ID,
        "features": ["multi-turn conversations", "session management"],
        "endpoints": {
            "chat": "POST /chat",
            "new_session": "POST /sessions/new",
            "session_info": "GET /sessions/{session_id}",
            "delete_session": "DELETE /sessions/{session_id}",
            "clear_session": "POST /sessions/{session_id}/clear",
            "list_sessions": "GET /sessions",
            "health": "GET /health", 
            "stats": "GET /stats",
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
        print(f"\n{Fore.YELLOW}👋 Server interrupted by user{Style.RESET_ALL}")
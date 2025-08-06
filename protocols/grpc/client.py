from typing import AsyncGenerator
from datetime import timedelta 
from datetime import datetime
from typing import Optional
from colorama import Style 
from colorama import Fore
from colorama import Back
from colorama import init 
import chat_pb2_grpc  # import generated gRPC code
import threading
import chat_pb2  # import generated gRPC code
import asyncio
import signal
import json
import grpc
import time
import sys
import os


# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configuration
SERVER_URL = 'localhost:50051'

# Session statistics
session_stats = {
    'messages_sent': 0,
    'total_response_time': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'session_start': datetime.now(),
    'sessions_created': 0,
    'total_chunks_received': 0,
    'total_streams': 0,
    'connection_attempts': 0,
    'reconnections': 0
}

# Current session state
current_session = {
    'session_id': None,
    'model': None,
    'message_count': 0,
    'session_created_at': None,
    'is_connected': False
}

# gRPC state
grpc_state = {
    'channel': None,
    'stub': None,
    'chat_stream': None,
    'is_streaming': False,
    'current_response': '',
    'chunk_count': 0,
    'stream_start_time': None,
    'should_stop': False
}

# Global lock for print operations
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """
    Thread-safe print function
    """
    with print_lock:
        print(*args, **kwargs)

def print_banner():
    print(f"\n{Fore.GREEN}══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
    print(f"               🚀 GRPC MULTI-TURN CHAT CLIENT 🚀               ")
    print(f"{Fore.GREEN}══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
    print(f"  Server: {Fore.CYAN}{SERVER_URL:<47}{Style.RESET_ALL}  ")
    print(f"  Framework: {Fore.MAGENTA}gRPC + Async Streaming{' ' * 28}{Style.RESET_ALL}  ")
    print(f"  Multi-turn: {Fore.GREEN}ENABLED{' ' * 37}{Style.RESET_ALL}  ")
    print(f"  Streaming: {Fore.GREEN}BIDIRECTIONAL{' ' * 33}{Style.RESET_ALL}  ")
    print(f"  Status: {Fore.YELLOW}CONNECTING...{' ' * 35}{Style.RESET_ALL}  ")
    print(f"{Fore.GREEN}══════════════════════════════════════════════════════════════{Style.RESET_ALL}")

def check_server_health():
    """
    Check if the gRPC server is running and healthy
    """
    print(f"{Fore.YELLOW}🔍 Checking gRPC server health...{Style.RESET_ALL}")
    
    try:
        with grpc.insecure_channel(SERVER_URL) as channel:
            grpc.channel_ready_future(channel).result(timeout=5)
            
            stub = chat_pb2_grpc.ChatServiceStub(channel)
            
            # Try to get server stats as a health check
            response = stub.GetServerStats(chat_pb2.ServerStatsRequest())
            
            print(f"{Fore.GREEN}✅ gRPC server is healthy!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Model: {response.model}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Server Requests: {response.total_requests}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Active Sessions: {response.active_sessions}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Framework: {response.framework}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Uptime: {str(timedelta(seconds=response.uptime_seconds))}{Style.RESET_ALL}")
            
            return True
            
    except grpc.RpcError as e:
        print(f"{Fore.RED}❌ gRPC server health check failed: {e.details()}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Cannot connect to gRPC server at {SERVER_URL}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Make sure the server is running: python protocols/grpc/server.py{Style.RESET_ALL}")
        return False

def print_message_sent(message_type: str, content: str = ""):
    """
    Print outgoing gRPC message info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    safe_print(f"\n{Fore.BLUE}┌─ 📤 GRPC MESSAGE SENT [{timestamp}] ──────────────────────────┐{Style.RESET_ALL}")
    safe_print(f"  Type: {message_type}")
    safe_print(f"  Session: {Fore.CYAN}{current_session['session_id'][:8] if current_session['session_id'] else 'None'}...{Style.RESET_ALL}")
    
    if content:
        preview = content[:40] + ('...' if len(content) > 40 else '')
        safe_print(f"  Message: {Fore.WHITE}\"{preview}\"{Style.RESET_ALL}")
    
    safe_print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def display_ai_response_header(session_context: str = ""):
    """
    Display AI response header
    """
    safe_print(f"\n{Fore.CYAN}🤖 {Back.BLUE} AI Response (gRPC Streaming) {Style.RESET_ALL} {session_context}")
    safe_print(f"{Fore.WHITE}{'─' * 60}{Style.RESET_ALL}")

def display_ai_response_footer():
    """
    Display AI response footer
    """
    safe_print(f"{Fore.WHITE}{'─' * 60}{Style.RESET_ALL}")

def print_session_stats():
    """
    Print current session statistics
    """
    uptime = datetime.now() - session_stats['session_start']
    avg_response_time = (session_stats['total_response_time'] / session_stats['successful_requests'] 
                        if session_stats['successful_requests'] > 0 else 0)
    avg_chunks = (session_stats['total_chunks_received'] / session_stats['total_streams']
                 if session_stats['total_streams'] > 0 else 0)
    
    print(f"\n{Fore.MAGENTA}┌─ 📊 CLIENT SESSION STATISTICS ──────────────────────────────┐{Style.RESET_ALL}")
    print(f"  Client Session Duration: {str(uptime).split('.')[0]}")
    print(f"  Messages Sent: {Fore.YELLOW}{session_stats['messages_sent']}{Style.RESET_ALL}")
    print(f"  Successful Streams: {Fore.GREEN}{session_stats['successful_requests']}{Style.RESET_ALL}")
    print(f"  Failed Streams: {Fore.RED}{session_stats['failed_requests']}{Style.RESET_ALL}")
    print(f"  Total Chunks Received: {Fore.CYAN}{session_stats['total_chunks_received']}{Style.RESET_ALL}")
    print(f"  Avg Chunks per Stream: {Fore.CYAN}{avg_chunks:.1f}{Style.RESET_ALL}")
    print(f"  Connection Attempts: {Fore.YELLOW}{session_stats['connection_attempts']}{Style.RESET_ALL}")
    print(f"  Reconnections: {Fore.YELLOW}{session_stats['reconnections']}{Style.RESET_ALL}")
    print(f"  Sessions Created: {Fore.CYAN}{session_stats['sessions_created']}{Style.RESET_ALL}")
    print(f"  Avg Response Time: {Fore.YELLOW}{avg_response_time:.3f}s{Style.RESET_ALL}")
    
    connection_status = f"{Fore.GREEN}Connected{Style.RESET_ALL}" if current_session['is_connected'] else f"{Fore.RED}Disconnected{Style.RESET_ALL}"
    print(f"  gRPC Status: {connection_status}")
    
    if current_session['session_id']:
        print(f"  Current Session: {Fore.CYAN}{current_session['session_id'][:8]}...{Style.RESET_ALL}")
        print(f"  Session Messages: {Fore.CYAN}{current_session['message_count']}{Style.RESET_ALL}")
    else:
        print(f"  Current Session: {Fore.RED}None{Style.RESET_ALL}")
    
    print(f"{Fore.MAGENTA}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_help():
    """
    Print available commands
    """
    print(f"\n{Fore.YELLOW}📋 Available Commands:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  /help{Style.RESET_ALL}     - Show this help message")
    print(f"{Fore.CYAN}  /stats{Style.RESET_ALL}    - Show client session statistics")
    print(f"{Fore.CYAN}  /server{Style.RESET_ALL}   - Show server statistics")
    print(f"{Fore.CYAN}  /health{Style.RESET_ALL}   - Check server health")
    print(f"{Fore.CYAN}  /clear{Style.RESET_ALL}    - Clear the screen")
    print(f"{Fore.CYAN}  /quit{Style.RESET_ALL}     - Exit the chat client")
    print()
    print(f"{Fore.YELLOW}🚀 gRPC Commands:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  /connect{Style.RESET_ALL}  - Connect to gRPC server")
    print(f"{Fore.CYAN}  /disconnect{Style.RESET_ALL} - Disconnect from gRPC server")
    print(f"{Fore.CYAN}  /ping{Style.RESET_ALL}     - Send ping to server")
    print()
    print(f"{Fore.YELLOW}🔄 Session Management:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  /new{Style.RESET_ALL}      - Create a new chat session")
    print(f"{Fore.CYAN}  /info{Style.RESET_ALL}     - Show current session info")
    print(f"{Fore.CYAN}  /sessions{Style.RESET_ALL} - List all active sessions")
    print(f"{Fore.CYAN}  /delete{Style.RESET_ALL}   - Delete current session")

def get_server_stats():
    """
    Get and display server statistics
    """
    try:
        if not grpc_state['stub']:
            print(f"{Fore.RED}❌ Not connected to gRPC server{Style.RESET_ALL}")
            return
        
        response = grpc_state['stub'].GetServerStats(chat_pb2.ServerStatsRequest())
        uptime_str = str(timedelta(seconds=response.uptime_seconds))
        
        print(f"\n{Fore.CYAN}┌─ 🖥️  GRPC SERVER STATISTICS ─────────────────────────────────┐{Style.RESET_ALL}")
        print(f"  Server Uptime: {uptime_str}")
        print(f"  Total Requests: {Fore.YELLOW}{response.total_requests}{Style.RESET_ALL}")
        print(f"  Successful: {Fore.GREEN}{response.successful_requests}{Style.RESET_ALL}")
        print(f"  Failed: {Fore.RED}{response.failed_requests}{Style.RESET_ALL}")
        print(f"  Active Sessions: {Fore.MAGENTA}{response.active_sessions}{Style.RESET_ALL}")
        print(f"  Total Sessions Created: {Fore.MAGENTA}{response.total_sessions_created}{Style.RESET_ALL}")
        print(f"  Avg Response Time: {Fore.YELLOW}{response.average_response_time:.3f}s{Style.RESET_ALL}")
        print(f"  Model: {Fore.MAGENTA}{response.model}{Style.RESET_ALL}")
        print(f"  Framework: {Fore.MAGENTA}{response.framework}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        
    except grpc.RpcError as e:
        print(f"{Fore.RED}❌ Failed to get server statistics: {e.details()}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting server stats: {e}{Style.RESET_ALL}")

def get_session_info():
    """
    Get information about current session
    """
    try:
        if not current_session['session_id']:
            print(f"{Fore.RED}❌ No active session{Style.RESET_ALL}")
            return False
        
        if not grpc_state['stub']:
            print(f"{Fore.RED}❌ Not connected to gRPC server{Style.RESET_ALL}")
            return False
            
        request = chat_pb2.SessionInfoRequest(session_id=current_session['session_id'])
        response = grpc_state['stub'].GetSessionInfo(request)
        
        if not response.success:
            print(f"{Fore.RED}❌ Failed to get session info: {response.message}{Style.RESET_ALL}")
            return False
        
        duration = timedelta(seconds=response.duration_seconds)
        
        print(f"\n{Fore.CYAN}┌─ 📋 SESSION INFO ────────────────────────────────────────────┐{Style.RESET_ALL}")
        print(f"  Session ID: {response.session_id[:8]}...")
        print(f"  Model: {response.model}")
        print(f"  Total Messages: {response.message_count}")
        print(f"  User Messages: {response.user_messages}")
        print(f"  AI Messages: {response.model_messages}")
        print(f"  Duration: {str(duration).split('.')[0]}")
        print(f"  Created: {datetime.fromisoformat(response.created_at).strftime('%H:%M:%S')}")
        print(f"{Fore.CYAN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        return True
        
    except grpc.RpcError as e:
        print(f"{Fore.RED}❌ gRPC error getting session info: {e.details()}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting session info: {e}{Style.RESET_ALL}")
        return False

def list_all_sessions():
    """
    List all active sessions on the server
    """
    try:
        if not grpc_state['stub']:
            print(f"{Fore.RED}❌ Not connected to gRPC server{Style.RESET_ALL}")
            return False
        
        response = grpc_state['stub'].ListSessions(chat_pb2.ListSessionsRequest())
        
        print(f"\n{Fore.CYAN}┌─ 📋 ALL ACTIVE SESSIONS ({response.active_sessions}) ────────────────────────┐{Style.RESET_ALL}")
        
        if not response.sessions:
            print(f"  No active sessions")
        else:
            for i, session in enumerate(response.sessions, 1):
                duration_str = f"{session.duration_minutes}m"
                created_time = datetime.fromisoformat(session.created_at).strftime('%H:%M:%S')
                is_current = session.session_id == current_session['session_id']
                marker = " ← CURRENT" if is_current else ""
                
                print(f"  {i}. {session.session_id[:8]}... ({session.message_count} msgs, {duration_str}, {created_time}){Fore.GREEN}{marker}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        return True
        
    except grpc.RpcError as e:
        print(f"{Fore.RED}❌ gRPC error listing sessions: {e.details()}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error listing sessions: {e}{Style.RESET_ALL}")
        return False

def connect_grpc():
    """
    Connect to gRPC server
    """
    if current_session['is_connected']:
        print(f"{Fore.YELLOW}⚠️  Already connected to gRPC server{Style.RESET_ALL}")
        return True
    
    print(f"{Fore.YELLOW}🚀 Connecting to gRPC server...{Style.RESET_ALL}")
    
    try:
        session_stats['connection_attempts'] += 1
        
        # Create channel and stub
        grpc_state['channel'] = grpc.insecure_channel(SERVER_URL)
        grpc.channel_ready_future(grpc_state['channel']).result(timeout=5)
        grpc_state['stub'] = chat_pb2_grpc.ChatServiceStub(grpc_state['channel'])
        
        current_session['is_connected'] = True
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n{Fore.GREEN}┌─ 🚀 GRPC CONNECTED [{timestamp}] ─────────────────────────────┐{Style.RESET_ALL}")
        print(f"  Server: {Fore.CYAN}{SERVER_URL}{Style.RESET_ALL}")
        print(f"  Framework: {Fore.MAGENTA}gRPC + Async Streaming{Style.RESET_ALL}")
        print(f"  Protocol: gRPC")
        print(f"  Streaming: {Fore.GREEN}BIDIRECTIONAL{Style.RESET_ALL}")
        print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}✅ gRPC connected successfully!{Style.RESET_ALL}")
        return True
        
    except grpc.FutureTimeoutError:
        print(f"{Fore.RED}❌ Connection timeout - server may not be running{Style.RESET_ALL}")
        session_stats['failed_requests'] += 1
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error connecting to gRPC server: {e}{Style.RESET_ALL}")
        session_stats['failed_requests'] += 1
        return False

def disconnect_grpc():
    """
    Disconnect from gRPC server
    """
    if not current_session['is_connected']:
        print(f"{Fore.YELLOW}⚠️  Not connected to gRPC server{Style.RESET_ALL}")
        return
    
    print(f"{Fore.YELLOW}🚀 Disconnecting from gRPC server...{Style.RESET_ALL}")
    
    try:
        grpc_state['should_stop'] = True
        
        if grpc_state['chat_stream']:
            grpc_state['chat_stream'] = None
        
        if grpc_state['channel']:
            grpc_state['channel'].close()
        
        grpc_state['channel'] = None
        grpc_state['stub'] = None
        current_session['is_connected'] = False
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n{Fore.YELLOW}┌─ 🚀 GRPC DISCONNECTED [{timestamp}] ───────────────────────────┐{Style.RESET_ALL}")
        print(f"  Server: {Fore.CYAN}{SERVER_URL}{Style.RESET_ALL}")
        print(f"  Status: Disconnected")
        print(f"{Fore.YELLOW}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}✅ gRPC disconnected successfully!{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}❌ Error disconnecting: {e}{Style.RESET_ALL}")

def create_new_session():
    """
    Create a new chat session
    """
    if not current_session['is_connected']:
        print(f"{Fore.RED}❌ Not connected to gRPC server. Use /connect first.{Style.RESET_ALL}")
        return
    
    try:
        print_message_sent('CreateSession')
        
        request = chat_pb2.CreateSessionRequest(model_id="gemini-2.0-flash")
        response = grpc_state['stub'].CreateSession(request)
        
        if response.success:
            current_session['session_id'] = response.session_id
            current_session['model'] = response.model
            current_session['message_count'] = 0
            current_session['session_created_at'] = datetime.now()
            session_stats['sessions_created'] += 1
            
            print(f"{Fore.GREEN}✨ New session created: {response.session_id[:8]}... ({response.model}){Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Failed to create session: {response.message}{Style.RESET_ALL}")
            
    except grpc.RpcError as e:
        print(f"{Fore.RED}❌ gRPC error creating session: {e.details()}{Style.RESET_ALL}")
        session_stats['failed_requests'] += 1
    except Exception as e:
        print(f"{Fore.RED}❌ Error creating session: {e}{Style.RESET_ALL}")
        session_stats['failed_requests'] += 1

def delete_current_session():
    """
    Delete the current session
    """
    if not current_session['session_id']:
        print(f"{Fore.RED}❌ No active session to delete{Style.RESET_ALL}")
        return
    
    if not current_session['is_connected']:
        print(f"{Fore.RED}❌ Not connected to gRPC server{Style.RESET_ALL}")
        return
    
    try:
        print_message_sent('DeleteSession')
        
        request = chat_pb2.DeleteSessionRequest(session_id=current_session['session_id'])
        response = grpc_state['stub'].DeleteSession(request)
        
        if response.success:
            print(f"{Fore.GREEN}🗑️ Session {current_session['session_id'][:8]}... deleted successfully{Style.RESET_ALL}")
            current_session['session_id'] = None
            current_session['model'] = None
            current_session['message_count'] = 0
        else:
            print(f"{Fore.RED}❌ Failed to delete session: {response.message}{Style.RESET_ALL}")
            
    except grpc.RpcError as e:
        print(f"{Fore.RED}❌ gRPC error deleting session: {e.details()}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error deleting session: {e}{Style.RESET_ALL}")

async def send_chat_message(user_message: str):
    """
    Send a chat message via gRPC streaming
    """
    if not current_session['is_connected']:
        print(f"{Fore.RED}❌ Not connected to gRPC server. Use /connect first.{Style.RESET_ALL}")
        return
    
    if not current_session['session_id']:
        print(f"{Fore.RED}❌ No active session. Use /new to create a session first.{Style.RESET_ALL}")
        return
    
    try:
        session_stats['messages_sent'] += 1
        print_message_sent('Chat', user_message)
        
        # Create the request
        request = chat_pb2.ChatRequest(
            type=chat_pb2.ChatRequest.MESSAGE,
            session_id=current_session['session_id'],
            message=user_message,
            timestamp=datetime.now().isoformat()
        )
        
        # Use a simple generator function
        def request_generator():
            yield request
        
        # Start the chat stream - note: using the synchronous stub
        try:
            response_stream = grpc_state['stub'].Chat(request_generator())
            
            # Process responses synchronously
            for response in response_stream:
                if response.type == chat_pb2.ChatResponse.STATUS:
                    session_context = f"(Context: {response.context_messages} messages)"
                    safe_print(f"{Fore.YELLOW}💭 {response.status_message} {session_context}{Style.RESET_ALL}")
                
                elif response.type == chat_pb2.ChatResponse.RESPONSE_START:
                    grpc_state['is_streaming'] = True
                    grpc_state['current_response'] = ''
                    grpc_state['chunk_count'] = 0
                    grpc_state['stream_start_time'] = time.time()
                    session_stats['total_streams'] += 1
                    
                    session_context = f"({Fore.CYAN}{current_session['session_id'][:8]}...{Style.RESET_ALL} - {current_session['model']})"
                    display_ai_response_header(session_context)
                
                elif response.type == chat_pb2.ChatResponse.CHUNK:
                    grpc_state['chunk_count'] += 1
                    session_stats['total_chunks_received'] += 1
                    chunk_text = response.chunk_text
                    grpc_state['current_response'] += chunk_text + " "
                    
                    # Print chunk in real-time
                    with print_lock:
                        print(f"{Fore.WHITE}{chunk_text} {Style.RESET_ALL}", end='', flush=True)
                
                elif response.type == chat_pb2.ChatResponse.RESPONSE_COMPLETE:
                    if grpc_state['is_streaming']:
                        safe_print()  # New line after response
                        display_ai_response_footer()
                    
                    # Update session info
                    current_session['message_count'] = response.message_count
                    
                    # Calculate timing
                    total_time = time.time() - (grpc_state['stream_start_time'] or time.time())
                    session_stats['total_response_time'] += total_time
                    session_stats['successful_requests'] += 1
                    
                    # Print completion info
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    safe_print(f"\n{Fore.GREEN}┌─ 🚀 GRPC RESPONSE COMPLETED [{timestamp}] ────────────────────┐{Style.RESET_ALL}")
                    safe_print(f"  Total Chunks: {response.total_chunks}")
                    safe_print(f"  Total Time: {Fore.YELLOW}{response.processing_time:.3f}s{Style.RESET_ALL}")
                    safe_print(f"  Context Messages: {response.message_count}")
                    safe_print(f"  Protocol: gRPC Stream")
                    safe_print(f"  Status: {Fore.GREEN}SUCCESS{Style.RESET_ALL}")
                    safe_print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
                    
                    grpc_state['is_streaming'] = False
                    break
                
                elif response.type == chat_pb2.ChatResponse.ERROR:
                    session_stats['failed_requests'] += 1
                    safe_print(f"\n{Fore.RED}❌ Server Error: {response.error_message}{Style.RESET_ALL}")
                    break
        
        except Exception as stream_error:
            session_stats['failed_requests'] += 1
            print(f"\n{Fore.RED}❌ gRPC streaming error: {stream_error}{Style.RESET_ALL}")
            
    except grpc.RpcError as e:
        session_stats['failed_requests'] += 1
        print(f"\n{Fore.RED}❌ gRPC error sending message: {e.details()}{Style.RESET_ALL}")
    except Exception as e:
        session_stats['failed_requests'] += 1
        print(f"\n{Fore.RED}❌ Error sending message: {e}{Style.RESET_ALL}")

async def send_ping():
    """
    Send ping to server
    """
    if not current_session['is_connected']:
        print(f"{Fore.RED}❌ Not connected to gRPC server{Style.RESET_ALL}")
        return
    
    if not current_session['session_id']:
        print(f"{Fore.RED}❌ No active session{Style.RESET_ALL}")
        return
    
    try:
        print(f"{Fore.YELLOW}🏓 Sending ping to server...{Style.RESET_ALL}")
        
        request = chat_pb2.ChatRequest(
            type=chat_pb2.ChatRequest.PING,
            session_id=current_session['session_id'],
            timestamp=datetime.now().isoformat()
        )
        
        def ping_request_generator():
            yield request
        
        response_stream = grpc_state['stub'].Chat(ping_request_generator())
        
        for response in response_stream:
            if response.type == chat_pb2.ChatResponse.PONG:
                print(f"{Fore.GREEN}🏓 Pong received from server{Style.RESET_ALL}")
                break
        
    except grpc.RpcError as e:
        print(f"{Fore.RED}❌ gRPC error sending ping: {e.details()}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error sending ping: {e}{Style.RESET_ALL}")

async def main():
    """
    Main chat loop
    """
    print_banner()
    
    # Check server health before starting
    if not check_server_health():
        print(f"\n{Fore.RED}Cannot connect to gRPC server. Exiting...{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.GREEN}🎉 gRPC server is available!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/help' for available commands{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/connect' to establish gRPC connection{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/quit' to exit{Style.RESET_ALL}")
    print(f"\n{Fore.WHITE}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🚀 High-performance bidirectional streaming enabled via gRPC!{Style.RESET_ALL}")
    
    # Auto-connect on startup
    print(f"\n{Fore.CYAN}🚀 Auto-connecting to gRPC server...{Style.RESET_ALL}")
    connect_grpc()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print(f"\n{Fore.YELLOW}👋 Shutting down gracefully...{Style.RESET_ALL}")
        disconnect_grpc()
        print_session_stats()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while True:
            # Get user input
            session_indicator = ""
            if current_session['session_id']:
                session_indicator = f" {Fore.CYAN}[{current_session['session_id'][:8]}...]{Style.RESET_ALL}"
            
            connection_indicator = f" {Fore.GREEN}●{Style.RESET_ALL}" if current_session['is_connected'] else f" {Fore.RED}●{Style.RESET_ALL}"
            
            try:
                user_message = input(f'\n{Fore.CYAN}You{session_indicator}{connection_indicator}{Style.RESET_ALL} {Fore.WHITE}›{Style.RESET_ALL} ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not user_message:
                continue
            
            # Handle special commands
            if user_message.lower() == '/quit':
                print(f"\n{Fore.YELLOW}👋 Thanks for chatting with gRPC! Goodbye!{Style.RESET_ALL}")
                disconnect_grpc()
                print_session_stats()
                break
            
            elif user_message.lower() == '/help':
                print_help()
                continue
            
            elif user_message.lower() == '/stats':
                print_session_stats()
                continue
            
            elif user_message.lower() == '/server':
                get_server_stats()
                continue
            
            elif user_message.lower() == '/health':
                check_server_health()
                continue
            
            elif user_message.lower() == '/clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
                continue
            
            elif user_message.lower() == '/connect':
                connect_grpc()
                continue
            
            elif user_message.lower() == '/disconnect':
                disconnect_grpc()
                continue
            
            elif user_message.lower() == '/ping':
                await send_ping()
                continue
            
            elif user_message.lower() == '/new':
                create_new_session()
                continue
            
            elif user_message.lower() == '/info':
                get_session_info()
                continue
            
            elif user_message.lower() == '/sessions':
                list_all_sessions()
                continue
            
            elif user_message.lower() == '/delete':
                delete_current_session()
                continue
            
            # Send regular message via gRPC
            await send_chat_message(user_message)
    
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
    finally:
        print(f"\n{Fore.YELLOW}👋 Cleaning up...{Style.RESET_ALL}")
        disconnect_grpc()
        print_session_stats()


if __name__ == '__main__':
    asyncio.run(main())
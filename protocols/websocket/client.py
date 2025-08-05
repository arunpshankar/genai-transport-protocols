from datetime import timedelta
from datetime import datetime
from typing import Optional
from colorama import Style
from colorama import Back
from colorama import Fore
from colorama import init 
import websockets
import threading
import requests
import asyncio
import signal
import json
import time
import sys
import os


# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configuration
SERVER_URL = 'localhost:8000'
WEBSOCKET_URL = f'ws://{SERVER_URL}/ws'
HTTP_BASE_URL = f'http://{SERVER_URL}'
NEW_SESSION_ENDPOINT = f'{HTTP_BASE_URL}/sessions/new'
SESSION_INFO_ENDPOINT = f'{HTTP_BASE_URL}/sessions'
HEALTH_ENDPOINT = f'{HTTP_BASE_URL}/health'
STATS_ENDPOINT = f'{HTTP_BASE_URL}/stats'
DOCS_ENDPOINT = f'{HTTP_BASE_URL}/docs'
DEMO_ENDPOINT = f'{HTTP_BASE_URL}/demo'

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
    'connection_id': None
}

# WebSocket state
websocket_state = {
    'is_connected': False,
    'is_streaming': False,
    'current_response': '',
    'chunk_count': 0,
    'stream_start_time': None,
    'websocket': None,
    'event_loop': None,
    'handler_task': None,
    'should_stop': False,
    'waiting_for_input': False  # Add this flag
}

# Global lock for print operations
print_lock = threading.Lock()
input_event = threading.Event()  # Add event to signal when ready for input

def safe_print(*args, **kwargs):
    """
    Thread-safe print function
    """
    with print_lock:
        print(*args, **kwargs)

def print_banner():
    print(f"\n{Fore.GREEN}╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"               🔌 FASTAPI WEBSOCKET CHAT CLIENT 🔌             ")
    print(f"{Fore.GREEN}╠══════════════════════════════════════════════════════════════╣{Style.RESET_ALL}")
    print(f"  Server: {Fore.CYAN}{SERVER_URL:<47}{Style.RESET_ALL}  ")
    print(f"  Framework: {Fore.MAGENTA}FastAPI + WebSockets{' ' * 26}{Style.RESET_ALL}  ")
    print(f"  Multi-turn: {Fore.GREEN}ENABLED{' ' * 37}{Style.RESET_ALL}  ")
    print(f"  Real-time: {Fore.GREEN}BIDIRECTIONAL{' ' * 33}{Style.RESET_ALL}  ")
    print(f"  Status: {Fore.YELLOW}CONNECTING...{' ' * 35}{Style.RESET_ALL}  ")
    print(f"{Fore.GREEN}╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")

def check_server_health():
    """
    Check if the FastAPI server is running and healthy
    """
    print(f"{Fore.YELLOW}🔍 Checking FastAPI WebSocket server health...{Style.RESET_ALL}")
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            
            print(f"{Fore.GREEN}✅ FastAPI WebSocket server is healthy!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Model: {health_data.get('model', 'Unknown')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Ping: {health_data.get('ping_ms', 0):.1f}ms{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Server Requests: {health_data.get('total_requests', 0)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Active Sessions: {health_data.get('active_sessions', 0)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   WebSocket Connections: {health_data.get('websocket_connections', 0)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Framework: {health_data.get('framework', 'FastAPI + WebSockets')}{Style.RESET_ALL}")
            
            return True
        else:
            print(f"{Fore.RED}❌ Server health check failed (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Cannot connect to FastAPI WebSocket server at {HTTP_BASE_URL}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Make sure the server is running: python protocols/websocket/server.py{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error checking server health: {e}{Style.RESET_ALL}")
        return False

def print_websocket_connect():
    """
    Print WebSocket connection info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    safe_print(f"\n{Fore.GREEN}┌─ 🔌 WEBSOCKET CONNECTED [{timestamp}] ───────────────────────┐{Style.RESET_ALL}")
    safe_print(f"  Server: {Fore.CYAN}ws://{SERVER_URL}/ws{Style.RESET_ALL}")
    safe_print(f"  Framework: {Fore.MAGENTA}FastAPI + WebSockets{Style.RESET_ALL}")
    safe_print(f"  Protocol: WebSocket")
    safe_print(f"  Connection: {Fore.CYAN}{current_session['connection_id'][:8] if current_session['connection_id'] else 'Unknown'}...{Style.RESET_ALL}")
    safe_print(f"  Bidirectional: {Fore.GREEN}ENABLED{Style.RESET_ALL}")
    safe_print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_websocket_disconnect(reason: str = "Normal"):
    """
    Print WebSocket disconnection info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    safe_print(f"\n{Fore.YELLOW}┌─ 🔌 WEBSOCKET DISCONNECTED [{timestamp}] ─────────────────────┐{Style.RESET_ALL}")
    safe_print(f"  Reason: {reason}")
    safe_print(f"  Connection: {Fore.CYAN}{current_session['connection_id'][:8] if current_session['connection_id'] else 'Unknown'}...{Style.RESET_ALL}")
    safe_print(f"  Status: Disconnected")
    safe_print(f"{Fore.YELLOW}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_message_sent(message_type: str, content: str = ""):
    """
    Print outgoing WebSocket message info
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    safe_print(f"\n{Fore.BLUE}┌─ 📤 WEBSOCKET MESSAGE SENT [{timestamp}] ────────────────────┐{Style.RESET_ALL}")
    safe_print(f"  Type: {message_type}")
    safe_print(f"  Connection: {Fore.CYAN}{current_session['connection_id'][:8] if current_session['connection_id'] else 'Unknown'}...{Style.RESET_ALL}")
    
    if message_type == 'chat' and content:
        preview = content[:40] + ('...' if len(content) > 40 else '')
        safe_print(f"  Message: {Fore.WHITE}\"{preview}\"{Style.RESET_ALL}")
    
    safe_print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def display_ai_response_header(session_context: str = ""):
    """
    Display AI response header
    """
    safe_print(f"\n{Fore.CYAN}🤖 {Back.BLUE} AI Response (WebSocket Streaming) {Style.RESET_ALL} {session_context}")
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
    
    connection_status = f"{Fore.GREEN}Connected{Style.RESET_ALL}" if websocket_state['is_connected'] else f"{Fore.RED}Disconnected{Style.RESET_ALL}"
    print(f"  WebSocket Status: {connection_status}")
    
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
    print(f"{Fore.CYAN}  /docs{Style.RESET_ALL}     - Open API documentation in browser")
    print(f"{Fore.CYAN}  /demo{Style.RESET_ALL}     - Open WebSocket demo page in browser")
    print(f"{Fore.CYAN}  /clear{Style.RESET_ALL}    - Clear the screen")
    print(f"{Fore.CYAN}  /quit{Style.RESET_ALL}     - Exit the chat client")
    print()
    print(f"{Fore.YELLOW}🔌 WebSocket Commands:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  /connect{Style.RESET_ALL}  - Connect to WebSocket server")
    print(f"{Fore.CYAN}  /disconnect{Style.RESET_ALL} - Disconnect from WebSocket server")
    print(f"{Fore.CYAN}  /ping{Style.RESET_ALL}     - Send ping to server")
    print()
    print(f"{Fore.YELLOW}🔄 Session Management:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  /new{Style.RESET_ALL}      - Create a new chat session")
    print(f"{Fore.CYAN}  /info{Style.RESET_ALL}     - Show current session info")
    print(f"{Fore.CYAN}  /sessions{Style.RESET_ALL} - List all active sessions")

def get_server_stats():
    """
    Get and display server statistics
    """
    try:
        response = requests.get(STATS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            uptime_str = str(timedelta(seconds=stats['uptime_seconds']))
            
            print(f"\n{Fore.CYAN}┌─ 🖥️  WEBSOCKET SERVER STATISTICS ───────────────────────────┐{Style.RESET_ALL}")
            print(f"  Server Uptime: {uptime_str}")
            print(f"  Total Requests: {Fore.YELLOW}{stats['total_requests']}{Style.RESET_ALL}")
            print(f"  Successful: {Fore.GREEN}{stats['successful_requests']}{Style.RESET_ALL}")
            print(f"  Failed: {Fore.RED}{stats['failed_requests']}{Style.RESET_ALL}")
            print(f"  Active Sessions: {Fore.MAGENTA}{stats['active_sessions']}{Style.RESET_ALL}")
            print(f"  WebSocket Connections: {Fore.MAGENTA}{stats['websocket_connections']}{Style.RESET_ALL}")
            print(f"  Total Sessions Created: {Fore.MAGENTA}{stats['total_sessions_created']}{Style.RESET_ALL}")
            print(f"  Avg Response Time: {Fore.YELLOW}{stats['average_response_time']:.3f}s{Style.RESET_ALL}")
            print(f"  Model: {Fore.MAGENTA}{stats['model']}{Style.RESET_ALL}")
            print(f"  Framework: {Fore.MAGENTA}FastAPI + WebSockets{Style.RESET_ALL}")
            print(f"{Fore.CYAN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Failed to get server statistics{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting server stats: {e}{Style.RESET_ALL}")

def get_session_info():
    """
    Get information about current session via HTTP
    """
    try:
        if current_session['session_id'] is None:
            print(f"{Fore.RED}❌ No active session{Style.RESET_ALL}")
            return False
            
        response = requests.get(f"{SESSION_INFO_ENDPOINT}/{current_session['session_id']}", timeout=5)
        
        if response.status_code == 200:
            info = response.json()
            duration = timedelta(seconds=info['session_duration_seconds'])
            
            print(f"\n{Fore.CYAN}┌─ 📋 SESSION INFO ────────────────────────────────────────────┐{Style.RESET_ALL}")
            print(f"  Session ID: {info['session_id'][:8]}...")
            print(f"  Model: {info['model']}")
            print(f"  Total Messages: {info['message_count']}")
            print(f"  User Messages: {info['user_messages']}")
            print(f"  AI Messages: {info['model_messages']}")
            print(f"  Duration: {str(duration).split('.')[0]}")
            print(f"  Created: {datetime.fromisoformat(info['created_at']).strftime('%H:%M:%S')}")
            print(f"{Fore.CYAN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Failed to get session info (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting session info: {e}{Style.RESET_ALL}")
        return False

def list_all_sessions():
    """
    List all active sessions on the server
    """
    try:
        response = requests.get(SESSION_INFO_ENDPOINT, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            sessions = data['sessions']
            
            print(f"\n{Fore.CYAN}┌─ 📋 ALL ACTIVE SESSIONS ({data['active_sessions']}) ────────────────────────┐{Style.RESET_ALL}")
            
            if not sessions:
                print(f"  No active sessions")
            else:
                for i, session in enumerate(sessions, 1):
                    duration = timedelta(minutes=session['duration_minutes'])
                    created_time = datetime.fromisoformat(session['created_at']).strftime('%H:%M:%S')
                    is_current = session['session_id'] == current_session['session_id']
                    marker = " ← CURRENT" if is_current else ""
                    clients = session.get('connected_clients', 0)
                    
                    print(f"  {i}. {session['session_id'][:8]}... ({session['message_count']} msgs, {clients} clients, {str(duration).split('.')[0]}, {created_time}){Fore.GREEN}{marker}{Style.RESET_ALL}")
            
            print(f"{Fore.CYAN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Failed to list sessions (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error listing sessions: {e}{Style.RESET_ALL}")
        return False

def open_docs():
    """
    Open API documentation
    """
    import webbrowser
    try:
        webbrowser.open(DOCS_ENDPOINT)
        print(f"{Fore.GREEN}📖 Opening API documentation in your browser...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   URL: {DOCS_ENDPOINT}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Could not open browser: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Manually visit: {DOCS_ENDPOINT}{Style.RESET_ALL}")

def open_demo():
    """
    Open WebSocket demo page
    """
    import webbrowser
    try:
        webbrowser.open(DEMO_ENDPOINT)
        print(f"{Fore.GREEN}🔌 Opening WebSocket demo page in your browser...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   URL: {DEMO_ENDPOINT}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Could not open browser: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Manually visit: {DEMO_ENDPOINT}{Style.RESET_ALL}")

def show_input_prompt():
    """
    Display the input prompt
    """
    session_indicator = ""
    if current_session['session_id']:
        session_indicator = f" {Fore.CYAN}[{current_session['session_id'][:8]}...]{Style.RESET_ALL}"
    
    connection_indicator = f" {Fore.GREEN}●{Style.RESET_ALL}" if websocket_state['is_connected'] else f" {Fore.RED}●{Style.RESET_ALL}"
    
    with print_lock:
        print(f'\n{Fore.CYAN}You{session_indicator}{connection_indicator}{Style.RESET_ALL} {Fore.WHITE}›{Style.RESET_ALL} ', end='', flush=True)

async def websocket_handler():
    """
    Handle WebSocket connection and messages
    """
    session_stats['connection_attempts'] += 1
    
    while not websocket_state['should_stop']:
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                websocket_state['websocket'] = websocket
                websocket_state['is_connected'] = True
                
                print_websocket_connect()
                
                async for message in websocket:
                    if websocket_state['should_stop']:
                        break
                        
                    try:
                        data = json.loads(message)
                        message_type = data.get('type', 'unknown')
                        
                        if message_type == 'connected':
                            current_session['connection_id'] = data.get('connection_id')
                            safe_print(f"{Fore.GREEN}✅ {data.get('message', 'Connected')}{Style.RESET_ALL}")
                            if 'server_info' in data:
                                info = data['server_info']
                                safe_print(f"{Fore.CYAN}📡 Server: {info.get('framework', 'Unknown')} ({info.get('model', 'Unknown')}){Style.RESET_ALL}")
                            # Show prompt after connection
                            if websocket_state['waiting_for_input']:
                                show_input_prompt()
                        
                        elif message_type == 'session_created' or message_type == 'session_joined':
                            current_session['session_id'] = data.get('session_id')
                            current_session['model'] = data.get('model')
                            current_session['message_count'] = data.get('message_count', 0)
                            current_session['session_created_at'] = datetime.now()
                            
                            if message_type == 'session_created':
                                session_stats['sessions_created'] += 1
                                safe_print(f"{Fore.GREEN}✨ New session created: {current_session['session_id'][:8]}... ({current_session['model']}){Style.RESET_ALL}")
                            else:
                                safe_print(f"{Fore.GREEN}🔗 Joined session: {current_session['session_id'][:8]}... ({current_session['model']}){Style.RESET_ALL}")
                            
                            # Show prompt after session creation
                            if websocket_state['waiting_for_input']:
                                show_input_prompt()
                        
                        elif message_type == 'status':
                            session_context = f"(Context: {data.get('context_messages', 0)} messages)"
                            safe_print(f"{Fore.YELLOW}💭 {data.get('message', 'Processing...')} {session_context}{Style.RESET_ALL}")
                        
                        elif message_type == 'response_start':
                            websocket_state['is_streaming'] = True
                            websocket_state['current_response'] = ''
                            websocket_state['chunk_count'] = 0
                            websocket_state['stream_start_time'] = time.time()
                            session_stats['total_streams'] += 1
                            
                            session_context = f"({Fore.CYAN}{current_session['session_id'][:8] if current_session['session_id'] else 'Unknown'}...{Style.RESET_ALL} - {current_session['model'] or 'Unknown'})"
                            display_ai_response_header(session_context)
                        
                        elif message_type == 'chunk':
                            websocket_state['chunk_count'] += 1
                            session_stats['total_chunks_received'] += 1
                            chunk_text = data.get('text', '')
                            websocket_state['current_response'] += chunk_text + " "
                            
                            # Print chunk in real-time
                            with print_lock:
                                print(f"{Fore.WHITE}{chunk_text} {Style.RESET_ALL}", end='', flush=True)
                        
                        elif message_type == 'response_complete':
                            if websocket_state['is_streaming']:
                                safe_print()  # New line after response
                                display_ai_response_footer()
                            
                            # Update session info
                            current_session['message_count'] = data.get('message_count', 0)
                            
                            # Calculate timing
                            total_time = time.time() - (websocket_state['stream_start_time'] or time.time())
                            session_stats['total_response_time'] += total_time
                            session_stats['successful_requests'] += 1
                            
                            # Print completion info
                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            safe_print(f"\n{Fore.GREEN}┌─ 🔌 WEBSOCKET RESPONSE COMPLETED [{timestamp}] ──────────────┐{Style.RESET_ALL}")
                            safe_print(f"  Total Chunks: {data.get('total_chunks', 0)}")
                            safe_print(f"  Total Time: {Fore.YELLOW}{data.get('processing_time', 0):.3f}s{Style.RESET_ALL}")
                            safe_print(f"  Context Messages: {data.get('message_count', 0)}")
                            safe_print(f"  Protocol: WebSocket")
                            safe_print(f"  Status: {Fore.GREEN}SUCCESS{Style.RESET_ALL}")
                            safe_print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
                            
                            websocket_state['is_streaming'] = False
                            
                            # Show prompt after response completion - THIS IS THE KEY FIX
                            if websocket_state['waiting_for_input']:
                                show_input_prompt()
                        
                        elif message_type == 'session_update':
                            update_type = data.get('update_type')
                            if update_type == 'user_typing' and data.get('typing'):
                                safe_print(f"\n{Fore.CYAN}👤 Someone else is typing...{Style.RESET_ALL}")
                            elif update_type == 'message_added':
                                safe_print(f"\n{Fore.CYAN}📩 Session updated: {data.get('message_count', 0)} messages{Style.RESET_ALL}")
                            elif update_type == 'user_disconnected':
                                safe_print(f"\n{Fore.YELLOW}👋 Another user disconnected{Style.RESET_ALL}")
                            
                            # Show prompt after session updates
                            if websocket_state['waiting_for_input']:
                                show_input_prompt()
                        
                        elif message_type == 'error':
                            session_stats['failed_requests'] += 1
                            safe_print(f"\n{Fore.RED}❌ Server Error: {data.get('message', 'Unknown error')}{Style.RESET_ALL}")
                            
                            # Show prompt after error
                            if websocket_state['waiting_for_input']:
                                show_input_prompt()
                        
                        elif message_type == 'pong':
                            safe_print(f"{Fore.GREEN}🏓 Pong received from server{Style.RESET_ALL}")
                            
                            # Show prompt after pong
                            if websocket_state['waiting_for_input']:
                                show_input_prompt()
                        
                    except json.JSONDecodeError:
                        safe_print(f"{Fore.RED}❌ Invalid JSON received from server{Style.RESET_ALL}")
                        if websocket_state['waiting_for_input']:
                            show_input_prompt()
                    except Exception as e:
                        safe_print(f"{Fore.RED}❌ Error processing message: {e}{Style.RESET_ALL}")
                        if websocket_state['waiting_for_input']:
                            show_input_prompt()
        
        except websockets.exceptions.ConnectionClosed:
            print_websocket_disconnect("Connection closed by server")
        except Exception as e:
            print_websocket_disconnect(f"Error: {str(e)}")
            if "Connection refused" in str(e):
                session_stats['failed_requests'] += 1
        finally:
            websocket_state['is_connected'] = False
            websocket_state['websocket'] = None
            
            # Try to reconnect after a delay if not stopping
            if not websocket_state['should_stop']:
                await asyncio.sleep(2)
                session_stats['reconnections'] += 1
                safe_print(f"{Fore.YELLOW}🔄 Attempting to reconnect...{Style.RESET_ALL}")

def websocket_background_task():
    """
    Background task to run WebSocket operations
    """
    def run_websocket_loop():
        """
        Run the WebSocket event loop in a separate thread
        """
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            websocket_state['event_loop'] = loop
            
            # Run the WebSocket handler
            loop.run_until_complete(websocket_handler())
        except Exception as e:
            safe_print(f"{Fore.RED}❌ WebSocket background task error: {e}{Style.RESET_ALL}")
        finally:
            websocket_state['event_loop'] = None
    
    # Start WebSocket in background thread
    thread = threading.Thread(target=run_websocket_loop, daemon=True)
    thread.start()
    return thread

def connect_websocket():
    """
    Connect to WebSocket server
    """
    if websocket_state['is_connected']:
        print(f"{Fore.YELLOW}⚠️  Already connected to WebSocket server{Style.RESET_ALL}")
        return True
    
    print(f"{Fore.YELLOW}🔌 Connecting to WebSocket server...{Style.RESET_ALL}")
    
    try:
        # Start background WebSocket task
        websocket_background_task()
        
        # Wait for connection to establish
        for i in range(50):  # Wait up to 5 seconds
            time.sleep(0.1)
            if websocket_state['is_connected']:
                return True
        
        print(f"{Fore.RED}❌ Failed to connect to WebSocket server{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error connecting to WebSocket: {e}{Style.RESET_ALL}")
        return False

def disconnect_websocket():
    """
    Disconnect from WebSocket server
    """
    if not websocket_state['is_connected']:
        print(f"{Fore.YELLOW}⚠️  Not connected to WebSocket server{Style.RESET_ALL}")
        return
    
    print(f"{Fore.YELLOW}🔌 Disconnecting from WebSocket server...{Style.RESET_ALL}")
    
    try:
        websocket_state['should_stop'] = True
        
        # Close WebSocket if connected
        if websocket_state['websocket'] and websocket_state['event_loop']:
            future = asyncio.run_coroutine_threadsafe(
                websocket_state['websocket'].close(), 
                websocket_state['event_loop']
            )
            try:
                future.result(timeout=2)
            except:
                pass
        
        # Wait a bit for cleanup
        time.sleep(0.5)
        
    except Exception as e:
        print(f"{Fore.RED}❌ Error disconnecting: {e}{Style.RESET_ALL}")
    
    websocket_state['is_connected'] = False
    websocket_state['websocket'] = None

def send_websocket_message(message_type: str, data: dict = None):
    """
    Send a message via WebSocket
    """
    if not websocket_state['is_connected'] or not websocket_state['websocket']:
        print(f"{Fore.RED}❌ WebSocket not connected{Style.RESET_ALL}")
        return False
    
    message = {
        'type': message_type,
        'timestamp': datetime.now().isoformat()
    }
    
    if data:
        message.update(data)
    
    try:
        if websocket_state['event_loop']:
            future = asyncio.run_coroutine_threadsafe(
                websocket_state['websocket'].send(json.dumps(message)),
                websocket_state['event_loop']
            )
            future.result(timeout=1)
            return True
    except Exception as e:
        print(f"{Fore.RED}❌ Error sending WebSocket message: {e}{Style.RESET_ALL}")
        return False

def send_chat_message(user_message: str):
    """
    Send a chat message via WebSocket
    """
    if not websocket_state['is_connected']:
        print(f"{Fore.RED}❌ Not connected to WebSocket server. Use /connect first.{Style.RESET_ALL}")
        return
    
    session_stats['messages_sent'] += 1
    
    print_message_sent('chat', user_message)
    
    success = send_websocket_message('chat', {
        'message': user_message,
        'session_id': current_session['session_id']
    })
    
    if not success:
        session_stats['failed_requests'] += 1

def create_new_session():
    """
    Create a new chat session via WebSocket
    """
    if not websocket_state['is_connected']:
        print(f"{Fore.RED}❌ Not connected to WebSocket server. Use /connect first.{Style.RESET_ALL}")
        return
    
    print_message_sent('create_session')
    send_websocket_message('create_session')

def send_ping():
    """
    Send ping to server
    """
    if not websocket_state['is_connected']:
        print(f"{Fore.RED}❌ Not connected to WebSocket server{Style.RESET_ALL}")
        return
    
    print(f"{Fore.YELLOW}🏓 Sending ping to server...{Style.RESET_ALL}")
    send_websocket_message('ping')

def main():
    """
    Main chat loop
    """
    print_banner()
    
    # Check server health before starting
    if not check_server_health():
        print(f"\n{Fore.RED}Cannot connect to FastAPI WebSocket server. Exiting...{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.GREEN}🎉 FastAPI WebSocket server is available!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/help' for available commands{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/connect' to establish WebSocket connection{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/demo' to open the web-based WebSocket demo{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/quit' to exit{Style.RESET_ALL}")
    print(f"\n{Fore.WHITE}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔌 Real-time bidirectional communication enabled via WebSockets!{Style.RESET_ALL}")
    
    # Auto-connect on startup
    print(f"\n{Fore.CYAN}🚀 Auto-connecting to WebSocket server...{Style.RESET_ALL}")
    connect_websocket()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print(f"\n{Fore.YELLOW}👋 Shutting down gracefully...{Style.RESET_ALL}")
        websocket_state['waiting_for_input'] = False
        disconnect_websocket()
        print_session_stats()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while True:
            # Set flag that we're waiting for input
            websocket_state['waiting_for_input'] = True
            
            # Show the input prompt
            show_input_prompt()
            
            try:
                user_message = input().strip()  # Simplified input call
                websocket_state['waiting_for_input'] = False  # Clear flag after getting input
            except (EOFError, KeyboardInterrupt):
                break
            
            if not user_message:
                continue
            
            # Handle special commands
            if user_message.lower() == '/quit':
                print(f"\n{Fore.YELLOW}👋 Thanks for chatting with FastAPI WebSockets! Goodbye!{Style.RESET_ALL}")
                disconnect_websocket()
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
            
            elif user_message.lower() == '/docs':
                open_docs()
                continue
            
            elif user_message.lower() == '/demo':
                open_demo()
                continue
            
            elif user_message.lower() == '/clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
                continue
            
            elif user_message.lower() == '/connect':
                connect_websocket()
                continue
            
            elif user_message.lower() == '/disconnect':
                disconnect_websocket()
                continue
            
            elif user_message.lower() == '/ping':
                send_ping()
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
            
            # Send regular message via WebSocket
            send_chat_message(user_message)
    
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
    finally:
        print(f"\n{Fore.YELLOW}👋 Cleaning up...{Style.RESET_ALL}")
        websocket_state['waiting_for_input'] = False
        disconnect_websocket()
        print_session_stats()


if __name__ == '__main__':
    main()
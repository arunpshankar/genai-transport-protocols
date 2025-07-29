import requests
import json
import time
import threading
from datetime import datetime, timedelta
from colorama import Fore, Back, Style, init
import os
from typing import Optional

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configuration
SERVER_URL = 'http://localhost:8000'
CHAT_STREAM_ENDPOINT = f'{SERVER_URL}/chat/stream'
NEW_SESSION_ENDPOINT = f'{SERVER_URL}/sessions/new'
SESSION_INFO_ENDPOINT = f'{SERVER_URL}/sessions'
HEALTH_ENDPOINT = f'{SERVER_URL}/health'
STATS_ENDPOINT = f'{SERVER_URL}/stats'
DOCS_ENDPOINT = f'{SERVER_URL}/docs'
DEMO_ENDPOINT = f'{SERVER_URL}/demo'

# Session statistics
session_stats = {
    'messages_sent': 0,
    'total_response_time': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'session_start': datetime.now(),
    'sessions_created': 0,
    'total_chunks_received': 0,
    'total_streams': 0
}

# Current session state
current_session = {
    'session_id': None,
    'model': None,
    'message_count': 0,
    'session_created_at': None
}

# Stream state
stream_state = {
    'is_streaming': False,
    'current_response': '',
    'chunk_count': 0,
    'stream_start_time': None
}

def print_banner():
    """Print a beautiful startup banner"""
    banner = f"""
{Fore.MAGENTA}╔══════════════════════════════════════════════════════════════╗
║               🌊 FASTAPI SSE MULTI-TURN CHAT CLIENT 🌊        ║
╠══════════════════════════════════════════════════════════════╣
║  Server: {SERVER_URL:<47} ║
║  Framework: FastAPI + SSE{' ' * 37} ║
║  Multi-turn: {Fore.GREEN}ENABLED{Fore.MAGENTA}{' ' * 39} ║
║  Streaming: {Fore.GREEN}REAL-TIME{Fore.MAGENTA}{' ' * 38} ║
║  Status: {Fore.GREEN}CONNECTING...{Fore.MAGENTA}{' ' * 39} ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def check_server_health():
    """Check if server is healthy and display status"""
    try:
        print(f"{Fore.YELLOW}🔍 Checking FastAPI SSE server health...{Style.RESET_ALL}")
        
        start_time = time.time()
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        ping_time = time.time() - start_time
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"{Fore.GREEN}✅ FastAPI SSE server is healthy!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Model: {health_data.get('model', 'Unknown')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Ping: {ping_time*1000:.1f}ms{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Server Requests: {health_data.get('total_requests', 0)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Active Sessions: {health_data.get('active_sessions', 0)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Active Streams: {health_data.get('streaming_connections', 0)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Framework: FastAPI + SSE{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Server health check failed (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Cannot connect to FastAPI SSE server at {SERVER_URL}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Make sure the SSE server is running on port 8000{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Start with: python server.py{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Health check failed: {e}{Style.RESET_ALL}")
        return False

def create_new_session(model_id=None):
    """Create a new chat session"""
    try:
        payload = {}
        if model_id:
            payload['model_id'] = model_id
            
        response = requests.post(NEW_SESSION_ENDPOINT, json=payload, timeout=10)
        
        if response.status_code == 200:
            session_data = response.json()
            current_session['session_id'] = session_data['session_id']
            current_session['model'] = session_data['model']
            current_session['message_count'] = 0
            current_session['session_created_at'] = datetime.now()
            session_stats['sessions_created'] += 1
            
            print(f"\n{Fore.GREEN}✨ New session created successfully!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Session ID: {current_session['session_id'][:8]}...{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Model: {current_session['model']}{Style.RESET_ALL}")
            
            return True
        else:
            print(f"{Fore.RED}❌ Failed to create session (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error creating session: {e}{Style.RESET_ALL}")
        return False

def get_session_info(session_id=None):
    """Get information about current or specified session"""
    try:
        if session_id is None:
            session_id = current_session['session_id']
            
        if session_id is None:
            print(f"{Fore.RED}❌ No active session{Style.RESET_ALL}")
            return False
            
        response = requests.get(f"{SESSION_INFO_ENDPOINT}/{session_id}", timeout=5)
        
        if response.status_code == 200:
            info = response.json()
            duration = timedelta(seconds=info['session_duration_seconds'])
            
            print(f"\n{Fore.CYAN}┌─ 📋 SESSION INFO ────────────────────────────────────────────┐{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Session ID: {info['session_id'][:8]}...")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Model: {info['model']}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Messages: {info['message_count']}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} User Messages: {info['user_messages']}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} AI Messages: {info['model_messages']}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Duration: {str(duration).split('.')[0]}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Created: {datetime.fromisoformat(info['created_at']).strftime('%H:%M:%S')}")
            print(f"{Fore.CYAN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Failed to get session info (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting session info: {e}{Style.RESET_ALL}")
        return False

def list_all_sessions():
    """List all active sessions on the server"""
    try:
        response = requests.get(SESSION_INFO_ENDPOINT, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            sessions = data['sessions']
            
            print(f"\n{Fore.CYAN}┌─ 📋 ALL ACTIVE SESSIONS ({data['active_sessions']}) ────────────────────────┐{Style.RESET_ALL}")
            
            if not sessions:
                print(f"{Fore.CYAN}│{Style.RESET_ALL} No active sessions")
            else:
                for i, session in enumerate(sessions, 1):
                    duration = timedelta(minutes=session['duration_minutes'])
                    created_time = datetime.fromisoformat(session['created_at']).strftime('%H:%M:%S')
                    is_current = session['session_id'] == current_session['session_id']
                    marker = " ← CURRENT" if is_current else ""
                    
                    print(f"{Fore.CYAN}│{Style.RESET_ALL} {i}. {session['session_id'][:8]}... ({session['message_count']} msgs, {str(duration).split('.')[0]}, {created_time}){Fore.GREEN}{marker}{Style.RESET_ALL}")
            
            print(f"{Fore.CYAN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Failed to list sessions (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error listing sessions: {e}{Style.RESET_ALL}")
        return False

def clear_session_history():
    """Clear the history of the current session"""
    try:
        if current_session['session_id'] is None:
            print(f"{Fore.RED}❌ No active session to clear{Style.RESET_ALL}")
            return False
            
        response = requests.post(f"{SESSION_INFO_ENDPOINT}/{current_session['session_id']}/clear", timeout=5)
        
        if response.status_code == 200:
            current_session['message_count'] = 0
            print(f"{Fore.GREEN}✅ Session history cleared successfully{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Failed to clear session (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error clearing session: {e}{Style.RESET_ALL}")
        return False

def delete_current_session():
    """Delete the current session"""
    try:
        if current_session['session_id'] is None:
            print(f"{Fore.RED}❌ No active session to delete{Style.RESET_ALL}")
            return False
            
        response = requests.delete(f"{SESSION_INFO_ENDPOINT}/{current_session['session_id']}", timeout=5)
        
        if response.status_code == 200:
            print(f"{Fore.GREEN}✅ Session deleted successfully{Style.RESET_ALL}")
            current_session['session_id'] = None
            current_session['model'] = None
            current_session['message_count'] = 0
            current_session['session_created_at'] = None
            return True
        else:
            print(f"{Fore.RED}❌ Failed to delete session (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error deleting session: {e}{Style.RESET_ALL}")
        return False

def log_stream_start(message: str, session_info: str):
    """Log the start of an SSE stream"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.BLUE}┌─ 🌊 STARTING SSE STREAM [{timestamp}] ───────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Endpoint: {Fore.CYAN}POST {CHAT_STREAM_ENDPOINT}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Framework: {Fore.MAGENTA}FastAPI + SSE{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Session: {session_info}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Message Length: {len(message)} characters")
    
    # Show message preview
    message_preview = (message[:50] + '...') if len(message) > 50 else message
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Message: {Fore.WHITE}\"{message_preview}\"{Style.RESET_ALL}")
    print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def log_stream_chunk(chunk_num: int, chunk_text: str):
    """Log individual stream chunks"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    preview = chunk_text[:40].replace('\n', ' ') + ('...' if len(chunk_text) > 40 else '')
    
    print(f"{Fore.YELLOW}🌊 [{timestamp}] Chunk #{chunk_num}: \"{preview}\"{Style.RESET_ALL}")

def log_stream_complete(total_chunks: int, total_time: float, message_count: int):
    """Log stream completion"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.GREEN}┌─ 🌊 SSE STREAM COMPLETED [{timestamp}] ──────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Total Chunks: {total_chunks}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Total Time: {Fore.YELLOW}{total_time:.3f}s{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Context Messages: {message_count}")
    print(f"{Fore.GREEN}│{Style.RESET_ALL} Status: {Fore.GREEN}SUCCESS{Style.RESET_ALL}")
    print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def display_ai_response_header(session_context: str = ""):
    """Display AI response header"""
    print(f"\n{Fore.CYAN}🤖 {Back.BLUE} AI Response (Streaming) {Style.RESET_ALL} {session_context}")
    print(f"{Fore.WHITE}{'─' * 60}{Style.RESET_ALL}")

def display_ai_response_footer():
    """Display AI response footer"""
    print(f"{Fore.WHITE}{'─' * 60}{Style.RESET_ALL}")

def print_session_stats():
    """Print current session statistics"""
    uptime = datetime.now() - session_stats['session_start']
    avg_response_time = (session_stats['total_response_time'] / session_stats['successful_requests'] 
                        if session_stats['successful_requests'] > 0 else 0)
    avg_chunks = (session_stats['total_chunks_received'] / session_stats['total_streams']
                 if session_stats['total_streams'] > 0 else 0)
    
    print(f"\n{Fore.MAGENTA}┌─ 📊 CLIENT SESSION STATISTICS ──────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Client Session Duration: {str(uptime).split('.')[0]}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Messages Sent: {Fore.YELLOW}{session_stats['messages_sent']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Successful Streams: {Fore.GREEN}{session_stats['successful_requests']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Failed Streams: {Fore.RED}{session_stats['failed_requests']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Total Chunks Received: {Fore.CYAN}{session_stats['total_chunks_received']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Avg Chunks per Stream: {Fore.CYAN}{avg_chunks:.1f}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Sessions Created: {Fore.CYAN}{session_stats['sessions_created']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Avg Response Time: {Fore.YELLOW}{avg_response_time:.3f}s{Style.RESET_ALL}")
    
    if current_session['session_id']:
        print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Current Session: {Fore.CYAN}{current_session['session_id'][:8]}...{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Session Messages: {Fore.CYAN}{current_session['message_count']}{Style.RESET_ALL}")
    else:
        print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Current Session: {Fore.RED}None{Style.RESET_ALL}")
    
    print(f"{Fore.MAGENTA}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_help():
    """Print available commands"""
    print(f"\n{Fore.YELLOW}📋 Available Commands:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  /help{Style.RESET_ALL}     - Show this help message")
    print(f"{Fore.CYAN}  /stats{Style.RESET_ALL}    - Show client session statistics")
    print(f"{Fore.CYAN}  /server{Style.RESET_ALL}   - Show server statistics")
    print(f"{Fore.CYAN}  /health{Style.RESET_ALL}   - Check server health")
    print(f"{Fore.CYAN}  /docs{Style.RESET_ALL}     - Open API documentation in browser")
    print(f"{Fore.CYAN}  /demo{Style.RESET_ALL}     - Open SSE demo page in browser")
    print(f"{Fore.CYAN}  /clear{Style.RESET_ALL}    - Clear the screen")
    print(f"{Fore.CYAN}  /quit{Style.RESET_ALL}     - Exit the chat client")
    print()
    print(f"{Fore.YELLOW}🔄 Session Management:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  /new{Style.RESET_ALL}      - Create a new chat session")
    print(f"{Fore.CYAN}  /info{Style.RESET_ALL}     - Show current session info")
    print(f"{Fore.CYAN}  /sessions{Style.RESET_ALL} - List all active sessions")
    print(f"{Fore.CYAN}  /reset{Style.RESET_ALL}    - Clear current session history")
    print(f"{Fore.CYAN}  /delete{Style.RESET_ALL}   - Delete current session")

def get_server_stats():
    """Get and display server statistics"""
    try:
        response = requests.get(STATS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            uptime_str = str(timedelta(seconds=stats['uptime_seconds']))
            
            print(f"\n{Fore.CYAN}┌─ 🖥️  SSE SERVER STATISTICS ──────────────────────────────────┐{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Server Uptime: {uptime_str}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Requests: {Fore.YELLOW}{stats['total_requests']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Successful: {Fore.GREEN}{stats['successful_requests']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Failed: {Fore.RED}{stats['failed_requests']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Active Sessions: {Fore.MAGENTA}{stats['active_sessions']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Active Streams: {Fore.MAGENTA}{stats['streaming_connections']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Sessions Created: {Fore.MAGENTA}{stats['total_sessions_created']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Avg Response Time: {Fore.YELLOW}{stats['average_response_time']:.3f}s{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Model: {Fore.MAGENTA}{stats['model']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Framework: {Fore.MAGENTA}FastAPI + SSE{Style.RESET_ALL}")
            print(f"{Fore.CYAN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Failed to get server statistics{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting server stats: {e}{Style.RESET_ALL}")

def open_docs():
    """Open API documentation"""
    import webbrowser
    try:
        webbrowser.open(DOCS_ENDPOINT)
        print(f"{Fore.GREEN}📖 Opening API documentation in your browser...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   URL: {DOCS_ENDPOINT}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Could not open browser: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Manually visit: {DOCS_ENDPOINT}{Style.RESET_ALL}")

def open_demo():
    """Open SSE demo page"""
    import webbrowser
    try:
        webbrowser.open(DEMO_ENDPOINT)
        print(f"{Fore.GREEN}🌊 Opening SSE demo page in your browser...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   URL: {DEMO_ENDPOINT}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Could not open browser: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Manually visit: {DEMO_ENDPOINT}{Style.RESET_ALL}")

def send_message_stream(user_message: str):
    """Send message to server and handle SSE stream response"""
    session_stats['messages_sent'] += 1
    session_stats['total_streams'] += 1
    
    # Prepare request
    payload = {'message': user_message}
    
    # Include session_id if we have one
    if current_session['session_id']:
        payload['session_id'] = current_session['session_id']
    
    # Session info for logging
    if current_session['session_id']:
        session_info = f"{Fore.CYAN}{current_session['session_id'][:8]}...{Style.RESET_ALL} (msg #{current_session['message_count'] + 1})"
    else:
        session_info = f"{Fore.YELLOW}Creating new session...{Style.RESET_ALL}"
    
    # Log stream start
    log_stream_start(user_message, session_info)
    
    # Initialize stream state
    stream_state['is_streaming'] = True
    stream_state['current_response'] = ''
    stream_state['chunk_count'] = 0
    stream_state['stream_start_time'] = time.time()
    
    try:
        # Send POST request for SSE stream
        response = requests.post(
            CHAT_STREAM_ENDPOINT, 
            json=payload, 
            stream=True,
            timeout=60,
            headers={'Accept': 'text/event-stream'}
        )
        
        if response.status_code == 200:
            session_context = ""
            ai_response = ""
            response_started = False
            
            # Process SSE events using simpler line-by-line approach
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                    
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith(':'):
                    continue
                
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    
                    # Skip empty data lines
                    if not data_str.strip():
                        continue
                        
                    try:
                        data = json.loads(data_str)
                        
                        if data['type'] == 'session_info':
                            # Update session info
                            if current_session['session_id'] != data['session_id']:
                                current_session['session_id'] = data['session_id']
                                current_session['model'] = data['model']
                                current_session['session_created_at'] = datetime.now()
                                session_stats['sessions_created'] += 1
                            
                            session_context = f"({Fore.CYAN}{data['session_id'][:8]}...{Style.RESET_ALL} - {data['model']})"
                            
                        elif data['type'] == 'status':
                            print(f"{Fore.YELLOW}💭 {data['message']} (Context: {data['context_messages']} messages){Style.RESET_ALL}")
                            
                        elif data['type'] == 'chunk':
                            if not response_started:
                                display_ai_response_header(session_context)
                                response_started = True
                            
                            stream_state['chunk_count'] += 1
                            session_stats['total_chunks_received'] += 1
                            chunk_text = data['text']
                            ai_response += chunk_text + " "
                            
                            # Print chunk in real-time
                            print(f"{Fore.WHITE}{chunk_text} {Style.RESET_ALL}", end='', flush=True)
                            
                            # Log chunk details (less verbose)
                            # log_stream_chunk(data['chunk_number'], chunk_text)
                            
                        elif data['type'] == 'complete':
                            if response_started:
                                print()  # New line after response
                                display_ai_response_footer()
                            
                            # Update session info
                            current_session['message_count'] = data['message_count']
                            
                            # Calculate timing
                            total_time = time.time() - stream_state['stream_start_time']
                            session_stats['total_response_time'] += total_time
                            session_stats['successful_requests'] += 1
                            
                            # Log completion
                            log_stream_complete(data['total_chunks'], data['processing_time'], data['message_count'])
                            break  # Stream is complete
                            
                        elif data['type'] == 'error':
                            print(f"\n{Fore.RED}❌ Server Error: {data['message']}{Style.RESET_ALL}")
                            session_stats['failed_requests'] += 1
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"{Fore.RED}❌ JSON Error: {e}{Style.RESET_ALL}")
                        print(f"   Raw line: '{line}'")
                        print(f"   Data part: '{data_str}'")
            
        else:
            session_stats['failed_requests'] += 1
            print(f"\n{Fore.RED}❌ Server Error: HTTP {response.status_code}{Style.RESET_ALL}")
            if response.text:
                try:
                    error_data = response.json()
                    print(f"{Fore.RED}   Details: {error_data.get('detail', 'Unknown error')}{Style.RESET_ALL}")
                except:
                    print(f"{Fore.RED}   Response: {response.text[:100]}{Style.RESET_ALL}")
            
    except requests.exceptions.Timeout:
        session_stats['failed_requests'] += 1
        print(f"\n{Fore.RED}⏰ Request timed out. The server might be busy.{Style.RESET_ALL}")
        
    except requests.exceptions.ConnectionError:
        session_stats['failed_requests'] += 1
        print(f"\n{Fore.RED}🔌 Connection failed. Is the FastAPI SSE server running?{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Start the server with: python server.py{Style.RESET_ALL}")
        
    except Exception as e:
        session_stats['failed_requests'] += 1
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
    
    finally:
        # Reset stream state
        stream_state['is_streaming'] = False
        stream_state['current_response'] = ''
        stream_state['chunk_count'] = 0
        stream_state['stream_start_time'] = None

def main():
    """Main chat loop"""
    print_banner()
    
    # Check server health before starting
    if not check_server_health():
        print(f"\n{Fore.RED}Cannot connect to FastAPI SSE server. Exiting...{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.GREEN}🎉 Connected to FastAPI SSE server successfully!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/help' for available commands{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/new' to create a session or just start chatting{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/demo' to open the web-based SSE demo{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/quit' to exit{Style.RESET_ALL}")
    print(f"\n{Fore.WHITE}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🌊 Real-time streaming enabled - responses will appear as they're generated!{Style.RESET_ALL}")
    
    # Main chat loop
    while True:
        try:
            # Get user input with a nice prompt
            session_indicator = ""
            if current_session['session_id']:
                session_indicator = f" {Fore.CYAN}[{current_session['session_id'][:8]}...]{Style.RESET_ALL}"
            
            if stream_state['is_streaming']:
                # Don't accept input while streaming
                time.sleep(0.1)
                continue
            
            user_message = input(f'\n{Fore.CYAN}You{session_indicator}{Style.RESET_ALL} {Fore.WHITE}›{Style.RESET_ALL} ').strip()
            
            if not user_message:
                continue
                
            # Handle special commands
            if user_message.lower() == '/quit':
                print(f"\n{Fore.YELLOW}👋 Thanks for chatting with FastAPI SSE! Goodbye!{Style.RESET_ALL}")
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
                
            elif user_message.lower() == '/new':
                create_new_session()
                continue
                
            elif user_message.lower() == '/info':
                get_session_info()
                continue
                
            elif user_message.lower() == '/sessions':
                list_all_sessions()
                continue
                
            elif user_message.lower() == '/reset':
                clear_session_history()
                continue
                
            elif user_message.lower() == '/delete':
                delete_current_session()
                continue
            
            # Send regular message with streaming
            send_message_stream(user_message)
            
        except KeyboardInterrupt:
            if stream_state['is_streaming']:
                print(f"\n{Fore.YELLOW}🛑 Stream interrupted{Style.RESET_ALL}")
                stream_state['is_streaming'] = False
                continue
            else:
                print(f"\n\n{Fore.YELLOW}👋 Chat interrupted. Goodbye!{Style.RESET_ALL}")
                print_session_stats()
                break
        except EOFError:
            print(f"\n\n{Fore.YELLOW}👋 Input stream ended. Goodbye!{Style.RESET_ALL}")
            print_session_stats()
            break

if __name__ == '__main__':
    main()
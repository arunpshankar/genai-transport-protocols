from datetime import timedelta
from datetime import datetime
from colorama import Style
from colorama import Fore
from colorama import Back
from colorama import init
import requests
import json
import time
import os


# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configuration
SERVER_URL = 'http://localhost:8000'
CHAT_ENDPOINT = f'{SERVER_URL}/chat'
NEW_SESSION_ENDPOINT = f'{SERVER_URL}/sessions/new'
SESSION_INFO_ENDPOINT = f'{SERVER_URL}/sessions'
HEALTH_ENDPOINT = f'{SERVER_URL}/health'
STATS_ENDPOINT = f'{SERVER_URL}/stats'
DOCS_ENDPOINT = f'{SERVER_URL}/docs'

# Session statistics
session_stats = {
    'messages_sent': 0,
    'total_response_time': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'session_start': datetime.now(),
    'sessions_created': 0
}

# Current session state
current_session = {
    'session_id': None,
    'model': None,
    'message_count': 0,
    'session_created_at': None
}

def print_banner():
    banner = f"""
{Fore.MAGENTA}╔══════════════════════════════════════════════════════════════╗
║               💬 HTTP REST MULTI-TURN CHAT CLIENT 💬           ║
╠══════════════════════════════════════════════════════════════╣
║  Server: {SERVER_URL:<47} ║
║  Framework: FastAPI{' ' * 41} ║
║  Multi-turn: {Fore.GREEN}ENABLED{Fore.MAGENTA}{' ' * 39} ║
║  Status: {Fore.GREEN}CONNECTING...{Fore.MAGENTA}{' ' * 39} ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def check_server_health():
    """
    Check if server is healthy and display status
    """
    try:
        print(f"{Fore.YELLOW}🔍 Checking HTTP REST multi-turn server health...{Style.RESET_ALL}")
        
        start_time = time.time()
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        ping_time = time.time() - start_time
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"{Fore.GREEN}✅ HTTP REST server is healthy!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Model: {health_data.get('model', 'Unknown')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Ping: {ping_time*1000:.1f}ms{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Server Requests: {health_data.get('total_requests', 0)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Active Sessions: {health_data.get('active_sessions', 0)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Framework: FastAPI (Multi-turn){Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Server health check failed (Status: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Cannot connect to HTTP REST server at {SERVER_URL}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Make sure the multi-turn server is running on port 8000{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Start with: python server.py{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Health check failed: {e}{Style.RESET_ALL}")
        return False

def create_new_session(model_id=None):
    """
    Create a new chat session
    """
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
    """
    Get information about current or specified session
    """
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
    """
    Clear the history of the current session
    """
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
    """
    Delete the current session
    """
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

def log_request_details(message: str, request_size: int, session_info: str):
    """
    Log outgoing request details
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{Fore.BLUE}┌─ 📤 SENDING REQUEST [{timestamp}] ────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Endpoint: {Fore.CYAN}POST {CHAT_ENDPOINT}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Framework: {Fore.MAGENTA}FastAPI (Multi-turn){Style.RESET_ALL}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Session: {session_info}")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Message Length: {len(message)} characters")
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Payload Size: {request_size} bytes")
    
    # Show message preview
    message_preview = (message[:50] + '...') if len(message) > 50 else message
    print(f"{Fore.BLUE}│{Style.RESET_ALL} Message: {Fore.WHITE}\"{message_preview}\"{Style.RESET_ALL}")
    print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def log_response_details(response_data: dict, http_status: int, response_time: float, response_size: int):
    """
    Log incoming response details
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    if http_status == 200:
        print(f"\n{Fore.GREEN}┌─ 📥 RESPONSE RECEIVED [{timestamp}] ──────────────────────────┐{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│{Style.RESET_ALL} HTTP Status: {Fore.GREEN}{http_status} OK{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│{Style.RESET_ALL} Response Time: {Fore.YELLOW}{response_time:.3f}s{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│{Style.RESET_ALL} Response Size: {response_size} bytes")
        
        if 'processing_time' in response_data:
            print(f"{Fore.GREEN}│{Style.RESET_ALL} Server Processing: {Fore.YELLOW}{response_data['processing_time']}s{Style.RESET_ALL}")
        
        if 'model' in response_data:
            print(f"{Fore.GREEN}│{Style.RESET_ALL} AI Model: {Fore.CYAN}{response_data['model']}{Style.RESET_ALL}")
            
        if 'session_id' in response_data:
            session_id = response_data['session_id']
            print(f"{Fore.GREEN}│{Style.RESET_ALL} Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
            
        if 'message_count' in response_data:
            print(f"{Fore.GREEN}│{Style.RESET_ALL} Context Messages: {response_data['message_count']}")
            
        if 'is_new_session' in response_data and response_data['is_new_session']:
            print(f"{Fore.GREEN}│{Style.RESET_ALL} Status: {Fore.YELLOW}NEW SESSION CREATED{Style.RESET_ALL}")
        
        if 'timestamp' in response_data:
            server_time = datetime.fromisoformat(response_data['timestamp'].replace('Z', '+00:00'))
            print(f"{Fore.GREEN}│{Style.RESET_ALL} Server Time: {Fore.CYAN}{server_time.strftime('%H:%M:%S')}{Style.RESET_ALL}")
            
        print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}┌─ ❌ ERROR RESPONSE [{timestamp}] ─────────────────────────────┐{Style.RESET_ALL}")
        print(f"{Fore.RED}│{Style.RESET_ALL} HTTP Status: {Fore.RED}{http_status}{Style.RESET_ALL}")
        print(f"{Fore.RED}│{Style.RESET_ALL} Response Time: {Fore.YELLOW}{response_time:.3f}s{Style.RESET_ALL}")
        print(f"{Fore.RED}│{Style.RESET_ALL} Response Size: {response_size} bytes")
        
        if isinstance(response_data, dict):
            if 'detail' in response_data:
                detail = response_data['detail']
                if isinstance(detail, dict) and 'error' in detail:
                    print(f"{Fore.RED}│{Style.RESET_ALL} Error: {Fore.RED}{detail['error']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}│{Style.RESET_ALL} Error: {Fore.RED}{detail}{Style.RESET_ALL}")
            
        print(f"{Fore.RED}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def display_ai_response(response_text: str, session_context: str = ""):
    """
    Display AI response in a beautiful format
    """
    print(f"\n{Fore.CYAN}🤖 {Back.BLUE} AI Response {Style.RESET_ALL} {session_context}")
    print(f"{Fore.WHITE}{'─' * 60}{Style.RESET_ALL}")
    
    # Split response into lines and add some formatting
    lines = response_text.split('\n')
    for line in lines:
        if line.strip():
            print(f"{Fore.WHITE}{line}{Style.RESET_ALL}")
        else:
            print()  # Empty line
    
    print(f"{Fore.WHITE}{'─' * 60}{Style.RESET_ALL}")

def print_session_stats():
    """
    Print current session statistics
    """
    uptime = datetime.now() - session_stats['session_start']
    avg_response_time = (session_stats['total_response_time'] / session_stats['successful_requests'] 
                        if session_stats['successful_requests'] > 0 else 0)
    
    print(f"\n{Fore.MAGENTA}┌─ 📊 CLIENT SESSION STATISTICS ──────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Client Session Duration: {str(uptime).split('.')[0]}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Messages Sent: {Fore.YELLOW}{session_stats['messages_sent']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Successful: {Fore.GREEN}{session_stats['successful_requests']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Failed: {Fore.RED}{session_stats['failed_requests']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Sessions Created: {Fore.CYAN}{session_stats['sessions_created']}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Avg Response Time: {Fore.YELLOW}{avg_response_time:.3f}s{Style.RESET_ALL}")
    
    if current_session['session_id']:
        print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Current Session: {Fore.CYAN}{current_session['session_id'][:8]}...{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Session Messages: {Fore.CYAN}{current_session['message_count']}{Style.RESET_ALL}")
    else:
        print(f"{Fore.MAGENTA}│{Style.RESET_ALL} Current Session: {Fore.RED}None{Style.RESET_ALL}")
    
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
    """
    Get and display server statistics
    """
    try:
        response = requests.get(STATS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            uptime_str = str(timedelta(seconds=stats['uptime_seconds']))
            
            print(f"\n{Fore.CYAN}┌─ 🖥️  SERVER STATISTICS ──────────────────────────────────────┐{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Server Uptime: {uptime_str}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Requests: {Fore.YELLOW}{stats['total_requests']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Successful: {Fore.GREEN}{stats['successful_requests']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Failed: {Fore.RED}{stats['failed_requests']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Active Sessions: {Fore.MAGENTA}{stats['active_sessions']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Total Sessions Created: {Fore.MAGENTA}{stats['total_sessions_created']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Avg Response Time: {Fore.YELLOW}{stats['average_response_time']:.3f}s{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Model: {Fore.MAGENTA}{stats['model']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Framework: {Fore.MAGENTA}FastAPI (Multi-turn){Style.RESET_ALL}")
            print(f"{Fore.CYAN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Failed to get server statistics{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error getting server stats: {e}{Style.RESET_ALL}")

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

def send_message(user_message: str):
    """
    Send message to server and handle response
    """
    session_stats['messages_sent'] += 1
    
    # Prepare request
    payload = {'message': user_message}
    
    # Include session_id if we have one
    if current_session['session_id']:
        payload['session_id'] = current_session['session_id']
    
    payload_json = json.dumps(payload)
    request_size = len(payload_json.encode('utf-8'))
    
    # Session info for logging
    if current_session['session_id']:
        session_info = f"{Fore.CYAN}{current_session['session_id'][:8]}...{Style.RESET_ALL} (msg #{current_session['message_count'] + 1})"
    else:
        session_info = f"{Fore.YELLOW}Creating new session...{Style.RESET_ALL}"
    
    # Log request details
    log_request_details(user_message, request_size, session_info)
    
    try:
        start_time = time.time()
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
        response_time = time.time() - start_time
        
        response_size = len(response.content)
        
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {'error': 'Invalid JSON response'}
        
        # Log response details
        log_response_details(response_data, response.status_code, response_time, response_size)
        
        if response.status_code == 200:
            session_stats['successful_requests'] += 1
            session_stats['total_response_time'] += response_time
            
            # Update current session info
            if 'session_id' in response_data:
                if current_session['session_id'] != response_data['session_id']:
                    # New session was created
                    current_session['session_id'] = response_data['session_id']
                    current_session['model'] = response_data.get('model', 'Unknown')
                    current_session['session_created_at'] = datetime.now()
                    if response_data.get('is_new_session'):
                        session_stats['sessions_created'] += 1
                        
                current_session['message_count'] = response_data.get('message_count', 0)
            
            ai_response = response_data.get('response', '')
            
            # Session context for display
            context = f"({Fore.CYAN}{current_session['message_count']}{Style.RESET_ALL} messages)"
            
            # Display the AI response beautifully
            display_ai_response(ai_response, context)
            
        else:
            session_stats['failed_requests'] += 1
            if isinstance(response_data, dict) and 'detail' in response_data:
                detail = response_data['detail']
                if isinstance(detail, dict) and 'error' in detail:
                    error_msg = detail['error']
                else:
                    error_msg = str(detail)
            else:
                error_msg = 'Unknown error'
            print(f"\n{Fore.RED}❌ Server Error: {error_msg}{Style.RESET_ALL}")
            
    except requests.exceptions.Timeout:
        session_stats['failed_requests'] += 1
        print(f"\n{Fore.RED}⏰ Request timed out. The server might be busy.{Style.RESET_ALL}")
        
    except requests.exceptions.ConnectionError:
        session_stats['failed_requests'] += 1
        print(f"\n{Fore.RED}🔌 Connection failed. Is the HTTP REST server running?{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Start the server with: python server.py{Style.RESET_ALL}")
        
    except Exception as e:
        session_stats['failed_requests'] += 1
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")

def main():
    """
    Main chat loop
    """
    print_banner()
    
    # Check server health before starting
    if not check_server_health():
        print(f"\n{Fore.RED}Cannot connect to HTTP REST server. Exiting...{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.GREEN}🎉 Connected to HTTP REST multi-turn server successfully!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/help' for available commands{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/new' to create a session or just start chatting{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/docs' to open API documentation{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Type '/quit' to exit{Style.RESET_ALL}")
    print(f"\n{Fore.WHITE}{'═' * 60}{Style.RESET_ALL}")
    
    # Main chat loop
    while True:
        try:
            # Get user input with a nice prompt
            session_indicator = ""
            if current_session['session_id']:
                session_indicator = f" {Fore.CYAN}[{current_session['session_id'][:8]}...]{Style.RESET_ALL}"
            
            user_message = input(f'\n{Fore.CYAN}You{session_indicator}{Style.RESET_ALL} {Fore.WHITE}›{Style.RESET_ALL} ').strip()
            
            if not user_message:
                continue
                
            # Handle special commands
            if user_message.lower() == '/quit':
                print(f"\n{Fore.YELLOW}👋 Thanks for chatting! Goodbye!{Style.RESET_ALL}")
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
            
            # Send regular message
            send_message(user_message)
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}👋 Chat interrupted. Goodbye!{Style.RESET_ALL}")
            print_session_stats()
            break
        except EOFError:
            print(f"\n\n{Fore.YELLOW}👋 Input stream ended. Goodbye!{Style.RESET_ALL}")
            print_session_stats()
            break


if __name__ == '__main__':
    main()
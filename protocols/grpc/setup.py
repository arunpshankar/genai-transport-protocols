from colorama import Style
from colorama import Fore
from colorama import Back
from colorama import init 
from pathlib import Path
import subprocess
import sys
import os


# Initialize colorama for cross-platform colored output
init(autoreset=True)

"""
gRPC Multi-turn Chat Setup Script

This script handles the complete setup for the gRPC implementation:
1. Check and install dependencies
2. Create proto file if needed
3. Generate gRPC code
4. Verify setup
"""

def check_python_version():
    """
    Check if Python version is compatible
    """
    if sys.version_info < (3, 8):
        print(f"{Fore.RED}❌ Python 3.8 or higher is required{Style.RESET_ALL}")
        return False
    print(f"{Fore.GREEN}✅ Python {sys.version_info.major}.{sys.version_info.minor} detected{Style.RESET_ALL}")
    return True

def install_dependencies():
    """
    Install required dependencies
    """
    print(f"{Fore.YELLOW}📦 Installing gRPC dependencies...{Style.RESET_ALL}")
    
    dependencies = [
        "grpcio>=1.60.0",
        "grpcio-tools>=1.60.0", 
        "protobuf>=4.25.0",
        "colorama>=0.4.6"
    ]
    
    try:
        for dep in dependencies:
            print(f"{Fore.CYAN}  Installing {dep}...{Style.RESET_ALL}")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", dep
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"{Fore.GREEN}✅ Dependencies installed successfully{Style.RESET_ALL}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}❌ Failed to install dependencies: {e}{Style.RESET_ALL}")
        return False

def create_proto_file():
    """
    Create the proto file if it doesn't exist
    """
    current_dir = Path(__file__).parent
    proto_file = current_dir / "chat.proto"
    
    if proto_file.exists():
        print(f"{Fore.GREEN}✅ Proto file already exists: {proto_file.name}{Style.RESET_ALL}")
        return True
    
    print(f"{Fore.YELLOW}📝 Creating proto file: {proto_file.name}{Style.RESET_ALL}")
    
    proto_content = '''syntax = "proto3";

package chat;

// The Chat service definition
service ChatService {
  // Create a new chat session
  rpc CreateSession(CreateSessionRequest) returns (CreateSessionResponse);
  
  // Get session information
  rpc GetSessionInfo(SessionInfoRequest) returns (SessionInfoResponse);
  
  // List all active sessions
  rpc ListSessions(ListSessionsRequest) returns (ListSessionsResponse);
  
  // Delete a session
  rpc DeleteSession(DeleteSessionRequest) returns (DeleteSessionResponse);
  
  // Get server statistics
  rpc GetServerStats(ServerStatsRequest) returns (ServerStatsResponse);
  
  // Bidirectional streaming chat
  rpc Chat(stream ChatRequest) returns (stream ChatResponse);
}

// Session Management Messages
message CreateSessionRequest {
  string model_id = 1;  // Optional, defaults to gemini-2.0-flash
}

message CreateSessionResponse {
  string session_id = 1;
  string model = 2;
  bool success = 3;
  string message = 4;
}

message SessionInfoRequest {
  string session_id = 1;
}

message SessionInfoResponse {
  bool success = 1;
  string message = 2;
  string session_id = 3;
  string model = 4;
  int32 message_count = 5;
  int32 user_messages = 6;
  int32 model_messages = 7;
  int32 duration_seconds = 8;
  string created_at = 9;
}

message ListSessionsRequest {
  // Empty for now, could add pagination in the future
}

message SessionSummary {
  string session_id = 1;
  string model = 2;
  int32 message_count = 3;
  int32 duration_minutes = 4;
  string created_at = 5;
}

message ListSessionsResponse {
  repeated SessionSummary sessions = 1;
  int32 active_sessions = 2;
}

message DeleteSessionRequest {
  string session_id = 1;
}

message DeleteSessionResponse {
  bool success = 1;
  string message = 2;
}

message ServerStatsRequest {
  // Empty for now
}

message ServerStatsResponse {
  int32 uptime_seconds = 1;
  int32 total_requests = 2;
  int32 successful_requests = 3;
  int32 failed_requests = 4;
  int32 active_sessions = 5;
  int32 total_sessions_created = 6;
  double average_response_time = 7;
  string model = 8;
  string framework = 9;
}

// Chat Streaming Messages
message ChatRequest {
  enum Type {
    MESSAGE = 0;
    PING = 1;
    TYPING_START = 2;
    TYPING_STOP = 3;
  }
  
  Type type = 1;
  string session_id = 2;
  string message = 3;  // For MESSAGE type
  string timestamp = 4;
}

message ChatResponse {
  enum Type {
    STATUS = 0;
    RESPONSE_START = 1;
    CHUNK = 2;
    RESPONSE_COMPLETE = 3;
    ERROR = 4;
    PONG = 5;
    SESSION_UPDATE = 6;
  }
  
  Type type = 1;
  string session_id = 2;
  
  // Status message
  string status_message = 3;
  int32 context_messages = 4;
  
  // Chunk data
  string chunk_text = 5;
  int32 chunk_number = 6;
  bool is_final = 7;
  
  // Response completion
  int32 total_chunks = 8;
  double processing_time = 9;
  int32 message_count = 10;
  
  // Error handling
  string error_message = 11;
  
  // Session updates
  string update_type = 12;
  string update_data = 13;
  
  // Timestamp
  string timestamp = 14;
}

// Health Check Messages
message HealthRequest {
  // Empty for now
}

message HealthResponse {
  bool healthy = 1;
  string message = 2;
  string model = 3;
  double ping_ms = 4;
  int32 active_sessions = 5;
  string framework = 6;
}
'''
    
    try:
        with open(proto_file, 'w') as f:
            f.write(proto_content)
        print(f"{Fore.GREEN}✅ Proto file created: {proto_file.name}{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to create proto file: {e}{Style.RESET_ALL}")
        return False

def generate_grpc_code():
    """
    Generate gRPC Python code from proto file
    """
    current_dir = Path(__file__).parent
    proto_file = current_dir / "chat.proto"
    
    if not proto_file.exists():
        print(f"{Fore.RED}❌ Proto file not found: {proto_file}{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.YELLOW}🔧 Generating gRPC code from {proto_file.name}...{Style.RESET_ALL}")
    
    try:
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={current_dir}",
            f"--python_out={current_dir}",
            f"--grpc_python_out={current_dir}",
            str(proto_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Check if files were created
            pb2_file = current_dir / "chat_pb2.py"
            grpc_file = current_dir / "chat_pb2_grpc.py"
            
            if pb2_file.exists() and grpc_file.exists():
                print(f"{Fore.GREEN}✅ Generated: {pb2_file.name}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}✅ Generated: {grpc_file.name}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ Generated files not found{Style.RESET_ALL}")
                return False
        else:
            print(f"{Fore.RED}❌ Error generating gRPC code:{Style.RESET_ALL}")
            if result.stderr:
                print(f"{Fore.RED}STDERR: {result.stderr}{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error generating gRPC code: {e}{Style.RESET_ALL}")
        return False

def verify_setup():
    """
    Verify that the setup is complete and working
    """
    print(f"{Fore.YELLOW}🔍 Verifying gRPC setup...{Style.RESET_ALL}")
    
    current_dir = Path(__file__).parent
    
    # Check required files
    required_files = [
        "chat.proto",
        "chat_pb2.py", 
        "chat_pb2_grpc.py",
        "server.py",
        "client.py"
    ]
    
    missing_files = []
    for filename in required_files:
        file_path = current_dir / filename
        if file_path.exists():
            print(f"{Fore.GREEN}  ✅ {filename}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}  ❌ {filename}{Style.RESET_ALL}")
            missing_files.append(filename)
    
    if missing_files:
        print(f"{Fore.RED}❌ Missing files: {', '.join(missing_files)}{Style.RESET_ALL}")
        return False
    
    # Test imports
    try:
        import grpc
        import chat_pb2
        import chat_pb2_grpc
        print(f"{Fore.GREEN}✅ All imports working{Style.RESET_ALL}")
    except ImportError as e:
        print(f"{Fore.RED}❌ Import error: {e}{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.GREEN}✅ gRPC setup verification complete!{Style.RESET_ALL}")
    return True

def print_banner():
    print(f""" {Fore.GREEN}══════════════════════════════════════════════════════════════
               🚀 GRPC MULTI-TURN CHAT SETUP 🚀               
══════════════════════════════════════════════════════════════
  Protocol: gRPC + Protocol Buffers                          
  Framework: High-performance bidirectional streaming        
  Type Safety: Strongly-typed Protocol Buffers               
  Performance: Optimized for production workloads            
══════════════════════════════════════════════════════════════{Style.RESET_ALL} """)

def print_usage_instructions():
    """
    Print usage instructions after successful setup
    """
    print(f"""
{Fore.GREEN}🎉 gRPC Multi-turn Chat Setup Complete!{Style.RESET_ALL}

{Fore.YELLOW}📋 Next Steps:{Style.RESET_ALL}

{Fore.CYAN}1. Start the gRPC server:{Style.RESET_ALL}
   python protocols/grpc/server.py

{Fore.CYAN}2. In another terminal, start the client:{Style.RESET_ALL}
   python protocols/grpc/client.py

{Fore.CYAN}3. Try these commands in the client:{Style.RESET_ALL}
   /help      - Show all commands
   /new       - Create a new session
   /sessions  - List active sessions
   /stats     - Show statistics
   /server    - Show server stats

{Fore.MAGENTA}🚀 Features Available:{Style.RESET_ALL}
• High-performance bidirectional streaming
• Multi-turn context preservation
• Type-safe Protocol Buffers communication
• Real-time message streaming
• Comprehensive session management
• Production-ready error handling

{Fore.CYAN}📖 For more information, see the README.md file.{Style.RESET_ALL}
""")

def print_setup_progress():
    """
    Print setup progress info
    """
    print(f"\n{Fore.CYAN}┌─ 🔧 GRPC SETUP PROGRESS ─────────────────────────────────────┐{Style.RESET_ALL}")
    print(f"  Phase 1: Checking Python version compatibility")
    print(f"  Phase 2: Installing required dependencies")
    print(f"  Phase 3: Creating Protocol Buffer definitions")
    print(f"  Phase 4: Generating gRPC Python code")
    print(f"  Phase 5: Verifying complete setup")
    print(f"{Fore.CYAN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_completion_summary():
    """
    Print completion summary
    """
    print(f"\n{Fore.GREEN}┌─ ✅ SETUP COMPLETED SUCCESSFULLY ───────────────────────────────┐{Style.RESET_ALL}")
    print(f"  Protocol Buffers: chat.proto")
    print(f"  Generated Code: chat_pb2.py, chat_pb2_grpc.py")
    print(f"  Server: server.py")
    print(f"  Client: client.py")
    print(f"  Dependencies: grpcio, grpcio-tools, protobuf, colorama")
    print(f"{Fore.GREEN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def main():
    """
    Main setup function
    """
    print_banner()
    print_setup_progress()
    
    # Check Python version
    print(f"\n{Fore.YELLOW}Phase 1: Checking Python compatibility...{Style.RESET_ALL}")
    if not check_python_version():
        return 1
    
    # Install dependencies
    print(f"\n{Fore.YELLOW}Phase 2: Installing dependencies...{Style.RESET_ALL}")
    if not install_dependencies():
        return 1
    
    # Create proto file
    print(f"\n{Fore.YELLOW}Phase 3: Setting up Protocol Buffers...{Style.RESET_ALL}")
    if not create_proto_file():
        return 1
    
    # Generate gRPC code
    print(f"\n{Fore.YELLOW}Phase 4: Generating gRPC code...{Style.RESET_ALL}")
    if not generate_grpc_code():
        return 1
    
    # Verify setup
    print(f"\n{Fore.YELLOW}Phase 5: Verifying setup...{Style.RESET_ALL}")
    if not verify_setup():
        return 1
    
    print_completion_summary()
    print_usage_instructions()
    return 0


if __name__ == "__main__":
    sys.exit(main())
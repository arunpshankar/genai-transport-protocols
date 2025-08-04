#!/usr/bin/env python3
"""
gRPC Code Generation Script

This script generates Python code from the Protocol Buffers definition.
Run this script before starting the gRPC server or client.
"""

import subprocess
import sys
import os
from pathlib import Path
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

def generate_grpc_code():
    """Generate gRPC Python code from proto file"""
    
    # Get the current directory
    current_dir = Path(__file__).parent
    proto_file = current_dir / "chat.proto"
    
    if not proto_file.exists():
        print(f"{Fore.RED}❌ Proto file not found: {proto_file}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please create the chat.proto file first.{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.YELLOW}🔧 Generating gRPC code from {proto_file}...{Style.RESET_ALL}")
    
    try:
        # Generate Python code from proto file
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={current_dir}",
            f"--python_out={current_dir}",
            f"--grpc_python_out={current_dir}",
            str(proto_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{Fore.GREEN}✅ gRPC code generated successfully!{Style.RESET_ALL}")
            
            # Check if files were created
            pb2_file = current_dir / "chat_pb2.py"
            grpc_file = current_dir / "chat_pb2_grpc.py"
            
            if pb2_file.exists() and grpc_file.exists():
                print(f"{Fore.CYAN}📄 Created: {pb2_file.name}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}📄 Created: {grpc_file.name}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  Generated files not found{Style.RESET_ALL}")
                return False
        else:
            print(f"{Fore.RED}❌ Error generating gRPC code:{Style.RESET_ALL}")
            if result.stdout:
                print(f"{Fore.RED}STDOUT: {result.stdout}{Style.RESET_ALL}")
            if result.stderr:
                print(f"{Fore.RED}STDERR: {result.stderr}{Style.RESET_ALL}")
            return False
            
    except FileNotFoundError:
        print(f"{Fore.RED}❌ grpc_tools.protoc not found.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please install grpcio-tools:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}pip install grpcio-tools{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print(f"{Fore.YELLOW}🔍 Checking gRPC dependencies...{Style.RESET_ALL}")
    
    try:
        import grpc
        import grpc_tools
        print(f"{Fore.GREEN}✅ gRPC dependencies found{Style.RESET_ALL}")
        return True
    except ImportError as e:
        print(f"{Fore.RED}❌ Missing gRPC dependencies: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please install required packages:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}pip install grpcio grpcio-tools{Style.RESET_ALL}")
        return False

def print_banner():
    """Print the script banner"""
    print(f"""
{Fore.GREEN}╔══════════════════════════════════════════════════════════════╗
║              🔧 GRPC CODE GENERATION SCRIPT 🔧               ║
╠══════════════════════════════════════════════════════════════╣
║  Purpose: Generate Python code from Protocol Buffers       ║
║  Input: chat.proto                                          ║
║  Output: chat_pb2.py, chat_pb2_grpc.py                      ║
║  Tool: grpc_tools.protoc                                    ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

def print_success_instructions():
    """Print success message and usage instructions"""
    print(f"""
{Fore.GREEN}🎉 gRPC setup completed successfully!{Style.RESET_ALL}

{Fore.YELLOW}📋 Next Steps:{Style.RESET_ALL}

{Fore.CYAN}1. Start the gRPC server:{Style.RESET_ALL}
   python protocols/grpc/server.py

{Fore.CYAN}2. In another terminal, start the client:{Style.RESET_ALL}
   python protocols/grpc/client.py

{Fore.MAGENTA}🚀 Generated Files:{Style.RESET_ALL}
• chat_pb2.py - Protocol Buffer classes
• chat_pb2_grpc.py - gRPC service stubs and servicers

{Fore.CYAN}📖 For more information, see the documentation.{Style.RESET_ALL}
""")

def print_generation_progress():
    """Print generation progress info"""
    print(f"\n{Fore.CYAN}┌─ 🔧 CODE GENERATION PROGRESS ───────────────────────────────┐{Style.RESET_ALL}")
    print(f"  Step 1: Checking required dependencies")
    print(f"  Step 2: Locating Protocol Buffer definition")
    print(f"  Step 3: Running protoc compiler")
    print(f"  Step 4: Verifying generated files")
    print(f"{Fore.CYAN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def print_completion_summary(success: bool):
    """Print completion summary"""
    if success:
        print(f"\n{Fore.GREEN}┌─ ✅ CODE GENERATION COMPLETED ──────────────────────────────┐{Style.RESET_ALL}")
        print(f"  Protocol Buffers: chat.proto")
        print(f"  Generated Classes: chat_pb2.py")
        print(f"  Generated Services: chat_pb2_grpc.py")
        print(f"  Status: Ready for use")
        print(f"{Fore.GREEN}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}┌─ ❌ CODE GENERATION FAILED ─────────────────────────────────┐{Style.RESET_ALL}")
        print(f"  Please check the error messages above")
        print(f"  Ensure all dependencies are installed")
        print(f"  Verify chat.proto file exists and is valid")
        print(f"{Fore.RED}└──────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

def main():
    """Main function"""
    print_banner()
    print_generation_progress()
    
    # Check dependencies
    print(f"\n{Fore.YELLOW}Step 1: Checking dependencies...{Style.RESET_ALL}")
    if not check_dependencies():
        print_completion_summary(False)
        return 1
    
    # Generate code
    print(f"\n{Fore.YELLOW}Step 2-4: Generating gRPC code...{Style.RESET_ALL}")
    success = generate_grpc_code()
    
    print_completion_summary(success)
    
    if success:
        print_success_instructions()
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
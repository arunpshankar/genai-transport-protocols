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

def generate_grpc_code():
    """Generate gRPC Python code from proto file"""
    
    # Get the current directory
    current_dir = Path(__file__).parent
    proto_file = current_dir / "chat.proto"
    
    if not proto_file.exists():
        print(f"❌ Proto file not found: {proto_file}")
        print("Please create the chat.proto file first.")
        return False
    
    print(f"🔧 Generating gRPC code from {proto_file}...")
    
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
            print("✅ gRPC code generated successfully!")
            
            # Check if files were created
            pb2_file = current_dir / "chat_pb2.py"
            grpc_file = current_dir / "chat_pb2_grpc.py"
            
            if pb2_file.exists() and grpc_file.exists():
                print(f"📄 Created: {pb2_file.name}")
                print(f"📄 Created: {grpc_file.name}")
                return True
            else:
                print("⚠️  Generated files not found")
                return False
        else:
            print(f"❌ Error generating gRPC code:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ grpc_tools.protoc not found.")
        print("Please install grpcio-tools:")
        print("pip install grpcio-tools")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import grpc
        import grpc_tools
        print("✅ gRPC dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing gRPC dependencies: {e}")
        print("Please install required packages:")
        print("pip install grpcio grpcio-tools")
        return False

def main():
    """Main function"""
    print("🚀 gRPC Code Generation Script")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Generate code
    if generate_grpc_code():
        print("\n🎉 gRPC setup completed successfully!")
        print("\nYou can now run:")
        print("  python protocols/grpc/server.py")
        print("  python protocols/grpc/client.py")
        return 0
    else:
        print("\n❌ gRPC setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
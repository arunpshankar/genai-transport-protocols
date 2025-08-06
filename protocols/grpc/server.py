from shared.setup import initialize_genai_client
from shared.llm import ChatSession
from typing import AsyncGenerator 
from concurrent import futures
from datetime import timedelta 
from datetime import datetime
from colorama import Style
from colorama import Fore
from colorama import Back
from colorama import init 
from typing import Optional
from typing import List 
from typing import Dict
import chat_pb2_grpc  # import generated gRPC code
import threading
import chat_pb2  # import generated gRPC code
import asyncio
import time
import uuid
import grpc
import json
import sys
import os


# Initialize colorama for cross-platform colored output
init(autoreset=True)

class ChatServiceServicer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.session_metadata: Dict[str, dict] = {}
        self.server_start_time = datetime.now()
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_sessions_created': 0,
            'active_sessions': 0
        }
        self.lock = threading.RLock()
        
        # Setup GenAI client
        try:
            self.genai_client = initialize_genai_client()
            print(f"{Fore.GREEN}✅ GenAI client initialized successfully for gRPC server{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to initialize GenAI client: {e}{Style.RESET_ALL}")
            raise

    def print_banner(self):
        print(f"\n{Fore.GREEN}══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
        print(f"               🚀 GRPC MULTI-TURN CHAT SERVER 🚀               ")
        print(f"{Fore.GREEN}══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
        print(f"  Model: {Fore.CYAN}gemini-2.0-flash{' ' * 37}{Style.RESET_ALL}  ")
        print(f"  Framework: {Fore.MAGENTA}gRPC + Async Streaming{' ' * 28}{Style.RESET_ALL}  ")
        print(f"  Multi-turn: {Fore.GREEN}ENABLED{' ' * 37}{Style.RESET_ALL}  ")
        print(f"  Streaming: {Fore.GREEN}BIDIRECTIONAL{' ' * 33}{Style.RESET_ALL}  ")
        print(f"  Status: {Fore.GREEN}READY{' ' * 41}{Style.RESET_ALL}  ")
        print(f"{Fore.GREEN}══════════════════════════════════════════════════════════════{Style.RESET_ALL}")
        print()
        print(f"{Fore.YELLOW}🚀 gRPC Multi-turn Chat Server starting up...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🌐 Server endpoint: localhost:50051{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📡 Protocol: gRPC with bidirectional streaming{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔧 Use Ctrl+C to stop the server{Style.RESET_ALL}")
        print()

    def print_request(self, method: str, session_id: str = None, message: str = None):
        """
        Print incoming gRPC requests info
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        print(f"\n{Fore.BLUE}┌─ 📨 GRPC REQUEST [{timestamp}] ────────────────────────────────┐{Style.RESET_ALL}")
        print(f"  Method: {Fore.CYAN}{method}{Style.RESET_ALL}")
        if session_id:
            print(f"  Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
        if message:
            preview = message[:40] + ('...' if len(message) > 40 else '')
            print(f"  Message: {Fore.WHITE}\"{preview}\"{Style.RESET_ALL}")
        print(f"{Fore.BLUE}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

    def print_response_start(self, session_id: str, context_messages: int):
        """Print response generation start info"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        print(f"\n{Fore.GREEN}┌─ 🧠 GENERATING RESPONSE [{timestamp}] ────────────────────────┐{Style.RESET_ALL}")
        print(f"  Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
        print(f"  Context Messages: {context_messages}")
        print(f"  Model: gemini-2.0-flash")
        print(f"  Protocol: gRPC Stream")
        print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")

    def print_chunk_sent(self, chunk_num: int, chunk_text: str, session_id: str):
        """
        Print individual chunks sent info
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        preview = chunk_text[:30].replace('\n', ' ') + ('...' if len(chunk_text) > 30 else '')
        
        print(f"{Fore.YELLOW}🚀 [{timestamp}] Chunk #{chunk_num} → {session_id[:8]}...: \"{preview}\"{Style.RESET_ALL}")

    def CreateSession(self, request, context):
        """
        Create a new chat session
        """
        with self.lock:
            self.stats['total_requests'] += 1
            
            session_id = str(uuid.uuid4())
            model_id = request.model_id or "gemini-2.0-flash"
            
            self.print_request("CreateSession", message=f"Model: {model_id}")
            
            try:
                # Create new chat session
                chat_session = ChatSession(
                    client=self.genai_client,
                    model_id=model_id
                )
                
                self.sessions[session_id] = chat_session
                self.session_metadata[session_id] = {
                    'session_id': session_id,
                    'model': model_id,
                    'created_at': datetime.now(),
                    'message_count': 0,
                    'user_messages': 0,
                    'model_messages': 0
                }
                
                self.stats['total_sessions_created'] += 1
                self.stats['active_sessions'] += 1
                self.stats['successful_requests'] += 1
                
                print(f"{Fore.GREEN}✨ Created new session {session_id[:8]}... with model {model_id}{Style.RESET_ALL}")
                
                return chat_pb2.CreateSessionResponse(
                    session_id=session_id,
                    model=model_id,
                    success=True,
                    message="Session created successfully"
                )
                
            except Exception as e:
                self.stats['failed_requests'] += 1
                print(f"{Fore.RED}❌ Error creating session: {e}{Style.RESET_ALL}")
                return chat_pb2.CreateSessionResponse(
                    session_id="",
                    model="",
                    success=False,
                    message=f"Failed to create session: {str(e)}"
                )

    def GetSessionInfo(self, request, context):
        """
        Get information about a session
        """
        with self.lock:
            self.stats['total_requests'] += 1
            
            session_id = request.session_id
            self.print_request("GetSessionInfo", session_id)
            
            if session_id not in self.session_metadata:
                self.stats['failed_requests'] += 1
                return chat_pb2.SessionInfoResponse(
                    success=False,
                    message="Session not found"
                )
            
            metadata = self.session_metadata[session_id]
            duration = datetime.now() - metadata['created_at']
            
            self.stats['successful_requests'] += 1
            
            return chat_pb2.SessionInfoResponse(
                success=True,
                session_id=session_id,
                model=metadata['model'],
                message_count=metadata['message_count'],
                user_messages=metadata['user_messages'],
                model_messages=metadata['model_messages'],
                duration_seconds=int(duration.total_seconds()),
                created_at=metadata['created_at'].isoformat()
            )

    def ListSessions(self, request, context):
        """
        List all active sessions
        """
        with self.lock:
            self.stats['total_requests'] += 1
            self.print_request("ListSessions")
            
            sessions = []
            for session_id, metadata in self.session_metadata.items():
                duration = datetime.now() - metadata['created_at']
                sessions.append(chat_pb2.SessionSummary(
                    session_id=session_id,
                    model=metadata['model'],
                    message_count=metadata['message_count'],
                    duration_minutes=int(duration.total_seconds() / 60),
                    created_at=metadata['created_at'].isoformat()
                ))
            
            self.stats['successful_requests'] += 1
            
            return chat_pb2.ListSessionsResponse(
                sessions=sessions,
                active_sessions=len(sessions)
            )

    def DeleteSession(self, request, context):
        """
        Delete a session
        """
        with self.lock:
            self.stats['total_requests'] += 1
            
            session_id = request.session_id
            self.print_request("DeleteSession", session_id)
            
            if session_id not in self.sessions:
                self.stats['failed_requests'] += 1
                return chat_pb2.DeleteSessionResponse(
                    success=False,
                    message="Session not found"
                )
            
            del self.sessions[session_id]
            del self.session_metadata[session_id]
            self.stats['active_sessions'] -= 1
            self.stats['successful_requests'] += 1
            
            print(f"{Fore.GREEN}🗑️ Deleted session {session_id[:8]}...{Style.RESET_ALL}")
            
            return chat_pb2.DeleteSessionResponse(
                success=True,
                message="Session deleted successfully"
            )

    def GetServerStats(self, request, context):
        """
        Get server statistics
        """
        with self.lock:
            self.stats['total_requests'] += 1
            self.print_request("GetServerStats")
            
            uptime = datetime.now() - self.server_start_time
            avg_response_time = 0  # TODO: Implement response time tracking
            
            self.stats['successful_requests'] += 1
            
            return chat_pb2.ServerStatsResponse(
                uptime_seconds=int(uptime.total_seconds()),
                total_requests=self.stats['total_requests'],
                successful_requests=self.stats['successful_requests'],
                failed_requests=self.stats['failed_requests'],
                active_sessions=self.stats['active_sessions'],
                total_sessions_created=self.stats['total_sessions_created'],
                average_response_time=avg_response_time,
                model="gemini-2.0-flash",
                framework="gRPC + Async Streaming"
            )

    def Chat(self, request_iterator, context):
        """
        Bidirectional streaming chat
        """
        session_id = None
        chat_session = None
        
        try:
            for request in request_iterator:
                with self.lock:
                    self.stats['total_requests'] += 1
                
                # Handle session setup
                if request.session_id:
                    session_id = request.session_id
                    if session_id not in self.sessions:
                        yield chat_pb2.ChatResponse(
                            type=chat_pb2.ChatResponse.ERROR,
                            error_message="Session not found"
                        )
                        return
                    
                    chat_session = self.sessions[session_id]
                    metadata = self.session_metadata[session_id]
                
                # Handle different request types
                if request.type == chat_pb2.ChatRequest.PING:
                    yield chat_pb2.ChatResponse(
                        type=chat_pb2.ChatResponse.PONG,
                        session_id=session_id
                    )
                    continue
                
                elif request.type == chat_pb2.ChatRequest.MESSAGE:
                    if not chat_session:
                        yield chat_pb2.ChatResponse(
                            type=chat_pb2.ChatResponse.ERROR,
                            error_message="No session established"
                        )
                        continue
                    
                    user_message = request.message
                    self.print_request("Chat", session_id, user_message)
                    
                    # Update session metadata
                    with self.lock:
                        metadata['message_count'] += 1
                        metadata['user_messages'] += 1
                    
                    # Send status update
                    yield chat_pb2.ChatResponse(
                        type=chat_pb2.ChatResponse.STATUS,
                        session_id=session_id,
                        status_message="Generating response...",
                        context_messages=metadata['message_count']
                    )
                    
                    # Print response generation start
                    self.print_response_start(session_id, metadata['message_count'])
                    
                    # Send response start
                    yield chat_pb2.ChatResponse(
                        type=chat_pb2.ChatResponse.RESPONSE_START,
                        session_id=session_id
                    )
                    
                    # Generate and stream response
                    try:
                        chunk_count = 0
                        start_time = time.time()
                        
                        # Generate the complete response using the chat session
                        full_response = chat_session.generate_response(user_message)
                        
                        # Split the response into words for streaming simulation
                        words = full_response.split()
                        
                        # Stream the response word by word
                        for i, word in enumerate(words):
                            chunk_count += 1
                            
                            # Add space after word (except for last word)
                            chunk_text = word + (" " if i < len(words) - 1 else "")
                            
                            # Print chunk info
                            self.print_chunk_sent(chunk_count, chunk_text, session_id)
                            
                            # Send chunk
                            yield chat_pb2.ChatResponse(
                                type=chat_pb2.ChatResponse.CHUNK,
                                session_id=session_id,
                                chunk_text=chunk_text,
                                chunk_number=chunk_count
                            )
                            
                            # Add a small delay to simulate real-time streaming
                            time.sleep(0.05)  # 50ms delay between words
                        
                        # Update session metadata
                        with self.lock:
                            metadata['message_count'] += 1
                            metadata['model_messages'] += 1
                            self.stats['successful_requests'] += 1
                        
                        # Send completion
                        processing_time = time.time() - start_time
                        yield chat_pb2.ChatResponse(
                            type=chat_pb2.ChatResponse.RESPONSE_COMPLETE,
                            session_id=session_id,
                            total_chunks=chunk_count,
                            processing_time=processing_time,
                            message_count=metadata['message_count']
                        )
                        
                        # Print completion info
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"\n{Fore.GREEN}┌─ 🚀 GRPC RESPONSE COMPLETED [{timestamp}] ────────────────────┐{Style.RESET_ALL}")
                        print(f"  Session: {Fore.CYAN}{session_id[:8]}...{Style.RESET_ALL}")
                        print(f"  Total Chunks: {chunk_count}")
                        print(f"  Processing Time: {Fore.YELLOW}{processing_time:.3f}s{Style.RESET_ALL}")
                        print(f"  Context Messages: {metadata['message_count']}")
                        print(f"  Protocol: gRPC Stream")
                        print(f"  Status: {Fore.GREEN}SUCCESS{Style.RESET_ALL}")
                        print(f"{Fore.GREEN}└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}")
                        
                    except Exception as e:
                        with self.lock:
                            self.stats['failed_requests'] += 1
                        
                        print(f"{Fore.RED}❌ Error generating response: {e}{Style.RESET_ALL}")
                        yield chat_pb2.ChatResponse(
                            type=chat_pb2.ChatResponse.ERROR,
                            session_id=session_id,
                            error_message=f"Error generating response: {str(e)}"
                        )
        
        except Exception as e:
            print(f"{Fore.RED}❌ Error in chat stream: {e}{Style.RESET_ALL}")
            yield chat_pb2.ChatResponse(
                type=chat_pb2.ChatResponse.ERROR,
                error_message=f"Stream error: {str(e)}"
            )

def serve():
    """
    Start the gRPC server
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = ChatServiceServicer()
    chat_pb2_grpc.add_ChatServiceServicer_to_server(servicer, server)
    
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    servicer.print_banner()
    
    return server

def main():
    """
    Main server function
    """
    try:
        server = serve()
        server.start()
        
        print(f"{Fore.GREEN}✅ gRPC server started successfully!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🌐 Listening on: localhost:50051{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📡 Protocol: gRPC with bidirectional streaming{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔧 Press Ctrl+C to stop{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'═' * 60}{Style.RESET_ALL}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}👋 gRPC server shutting down gracefully...{Style.RESET_ALL}")
            server.stop(grace=5)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 gRPC server shutting down gracefully...{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error starting gRPC server: {e}{Style.RESET_ALL}")


if __name__ == '__main__':
    main()
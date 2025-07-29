from shared.setup import initialize_genai_client
from typing import Optional
from colorama import Style 
from colorama import Fore
from colorama import init 
from google import genai
from typing import Dict 
from typing import List 
from typing import Any 
import time

# Initialize colorama
init(autoreset=True)


class ChatSession:
    """
    A reusable class to manage multi-turn chat conversations with context preservation.
    Designed to be imported and used in other modules.
    """
    
    def __init__(self, client: genai.Client, model_id: str):
        """
        Initialize the chat session.
        
        Args:
            client (genai.Client): The GenAI client.
            model_id (str): The model ID to use for generation.
        """
        self.client = client
        self.model_id = model_id
        self.chat_history: List[Dict[str, Any]] = []
        self.session_start_time = time.time()
        print(f"{Fore.GREEN}Chat session initialized with model: {model_id}{Style.RESET_ALL}")
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the chat history.
        
        Args:
            role (str): The role of the message sender ('user' or 'model').
            content (str): The content of the message.
        """
        self.chat_history.append({
            "role": role,
            "parts": [{"text": content}]
        })
        print(f"{Fore.CYAN}Added {role} message to chat history{Style.RESET_ALL}")
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """
        Get the current chat history.
        
        Returns:
            List[Dict[str, Any]]: The chat history.
        """
        return self.chat_history.copy()
    
    def generate_response(self, user_input: str) -> str:
        """
        Generate a response to user input while maintaining context.
        
        Args:
            user_input (str): The user's input message.
            
        Returns:
            str: The generated response text.
            
        Raises:
            Exception: If content generation fails.
        """
        try:
            # Add user message to history
            self.add_message("user", user_input)
            
            print(f"{Fore.BLUE}Generating response for message (length: {len(user_input)} chars){Style.RESET_ALL}")
            start_time = time.time()
            
            # Generate response with full chat history for context
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=self.chat_history
            )
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            response_text = response.text.strip()
            
            # Add model response to history
            self.add_message("model", response_text)
            
            print(f"{Fore.GREEN}Response generated in {elapsed_time:.2f} seconds{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Response: {response_text[:100]}{'...' if len(response_text) > 100 else ''}{Style.RESET_ALL}")
            
            return response_text
            
        except Exception as e:
            print(f"{Fore.RED}Failed to generate response{Style.RESET_ALL}")
            print(f"{Fore.RED}Exception details: {e}{Style.RESET_ALL}")
            raise
    
    def clear_history(self) -> None:
        """Clear the chat history."""
        self.chat_history.clear()
        print(f"{Fore.YELLOW}Chat history cleared{Style.RESET_ALL}")
    
    def get_message_count(self) -> int:
        """Get the number of messages in the chat history."""
        return len(self.chat_history)
    
    def get_session_duration(self) -> float:
        """Get the session duration in seconds."""
        return time.time() - self.session_start_time
    
    def get_last_response(self) -> Optional[str]:
        """
        Get the last model response.
        
        Returns:
            Optional[str]: The last response or None if no responses exist.
        """
        for message in reversed(self.chat_history):
            if message["role"] == "model":
                return message["parts"][0]["text"]
        return None
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the conversation.
        
        Returns:
            Dict[str, Any]: Summary including message count, duration, etc.
        """
        user_messages = sum(1 for msg in self.chat_history if msg["role"] == "user")
        model_messages = sum(1 for msg in self.chat_history if msg["role"] == "model")
        
        return {
            "model_id": self.model_id,
            "total_messages": len(self.chat_history),
            "user_messages": user_messages,
            "model_messages": model_messages,
            "session_duration_seconds": round(self.get_session_duration(), 2),
            "session_duration_minutes": round(self.get_session_duration() / 60, 2)
        }


def create_chat_session(model_id: str = "gemini-2.0-flash") -> ChatSession:
    """
    Factory function to create a new chat session.
    
    Args:
        model_id (str): The model ID to use for generation.
        
    Returns:
        ChatSession: A new chat session instance.
    """
    try:
        client = initialize_genai_client()
        return ChatSession(client, model_id)
    except Exception as e:
        print(f"{Fore.RED}Failed to create chat session: {e}{Style.RESET_ALL}")
        raise

def generate_single_response(prompt: str, model_id: str = "gemini-2.0-flash") -> str:
    """
    Generate a single response without maintaining context (original functionality).
    
    Args:
        prompt (str): The prompt for content generation.
        model_id (str): The model ID to use for generation.
    
    Returns:
        str: The generated content.
    
    Raises:
        Exception: If content generation fails.
    """
    try:
        client = initialize_genai_client()
        print(f"{Fore.BLUE}Generating single-turn content using model: {model_id}{Style.RESET_ALL}")
        start_time = time.time()
        
        response = client.models.generate_content(model=model_id, contents=prompt)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        response_text = response.text.strip()
        print(f"{Fore.GREEN}Content generated successfully in {elapsed_time:.2f} seconds{Style.RESET_ALL}")
        
        return response_text
        
    except Exception as e:
        print(f"{Fore.RED}Failed to generate content{Style.RESET_ALL}")
        print(f"{Fore.RED}Exception details: {e}{Style.RESET_ALL}")
from shared.setup import initialize_genai_client
from shared.logger import logger
from typing import Optional
from google import genai
from typing import Dict 
from typing import List 
from typing import Any 
import time


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
        logger.info(f"Chat session initialized with model: {model_id}")
    
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
        logger.debug(f"Added {role} message to chat history")
    
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
            
            logger.info(f"Generating response for message (length: {len(user_input)} chars)")
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
            
            logger.info(f"Response generated in {elapsed_time:.2f} seconds")
            logger.debug(f"Response: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
            
            return response_text
            
        except Exception as e:
            logger.error("Failed to generate response")
            logger.error(f"Exception details: {e}")
            raise
    
    def clear_history(self) -> None:
        """Clear the chat history."""
        self.chat_history.clear()
        logger.info("Chat history cleared")
    
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
        logger.error(f"Failed to create chat session: {e}")
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
        logger.info(f"Generating single-turn content using model: {model_id}")
        start_time = time.time()
        
        response = client.models.generate_content(model=model_id, contents=prompt)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        response_text = response.text.strip()
        logger.info(f"Content generated successfully in {elapsed_time:.2f} seconds")
        
        return response_text
        
    except Exception as e:
        logger.error("Failed to generate content")
        logger.error(f"Exception details: {e}")
        raise


if __name__ == "__main__":
    try:
        # Example 1: Single response
        response = generate_single_response("What's the largest planet in our solar system?")
        print(f"Single response: {response}")
        
        # Example 2: Multi-turn chat
        chat = create_chat_session()
        
        response1 = chat.generate_response("Hello, what's your name?")
        print(f"Response 1: {response1}")
        
        response2 = chat.generate_response("Can you remember what I just asked you?")
        print(f"Response 2: {response2}")
        
        # Get conversation summary
        summary = chat.get_conversation_summary()
        print(f"Conversation summary: {summary}")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
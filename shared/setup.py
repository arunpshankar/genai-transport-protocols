from shared.logger import logger
from shared.io import load_yaml
from google import genai
from typing import Dict
from typing import Any
import os


# Configuration Constants
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT: str = os.path.dirname(os.path.dirname(BASE_DIR))
CREDENTIALS_FILE: str = os.path.join(PROJECT_ROOT, 'genai-multi-transport-demo', 'credentials', 'api.yml')
# Global Configuration
CONFIG: Dict[str, Any] = load_yaml(CREDENTIALS_FILE)

def get_google_api_key(config: Dict[str, Any] = CONFIG) -> str:
    """
    Extract the Google API key from the configuration.

    Args:
        config (Dict[str, Any]): The loaded configuration dictionary.

    Returns:
        str: The Google API key.

    Raises:
        ValueError: If the Google API key is missing.
    """
    # Fixed: Access nested dictionary correctly
    google_config = config.get("google")
    if not google_config:
        logger.error("'google' section is missing in the configuration.")
        raise ValueError("'google' section not found in the configuration.")
    
    api_key = google_config.get("api_key")
    if not api_key:
        logger.error("Google API key is missing in the configuration.")
        raise ValueError("Google API key not found in the configuration.")
    
    # Debug logging to verify we got a string
    logger.info(f"API key type: {type(api_key)}")
    logger.info(f"API key length: {len(api_key) if isinstance(api_key, str) else 'N/A'}")
    
    return api_key

def initialize_genai_client(config: Dict[str, Any] = CONFIG) -> genai.Client:
    """
    Initializes the GenAI client using the Google API key from the configuration.

    Args:
        config (Dict[str, Any]): The loaded configuration dictionary.

    Returns:
        genai.Client: The initialized GenAI client.

    Raises:
        Exception: If the client initialization fails.
    """
    try:
        logger.info("Extracting Google API key from configuration.")
        google_api_key = get_google_api_key(config)

        logger.info("Initializing GenAI client.")
        client = genai.Client(api_key=google_api_key)
        logger.info("GenAI client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize GenAI client: {e}")
        raise
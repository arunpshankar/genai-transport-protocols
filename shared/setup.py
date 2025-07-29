from shared.io import load_yaml
from colorama import Style
from colorama import Fore
from colorama import init 
from google import genai
from typing import Dict
from typing import Any 
import os

# Initialize colorama for cross-platform colored output
init(autoreset=True)

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
        print(f"{Fore.RED}ERROR: 'google' section is missing in the configuration.{Style.RESET_ALL}")
        raise ValueError("'google' section not found in the configuration.")

    api_key = google_config.get("api_key")
    if not api_key:
        print(f"{Fore.RED}ERROR: Google API key is missing in the configuration.{Style.RESET_ALL}")
        raise ValueError("Google API key not found in the configuration.")

    # Debug output to verify we got a string
    print(f"{Fore.CYAN}INFO: API key type: {type(api_key)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}INFO: API key length: {len(api_key) if isinstance(api_key, str) else 'N/A'}{Style.RESET_ALL}")

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
        print(f"{Fore.CYAN}INFO: Extracting Google API key from configuration.{Style.RESET_ALL}")
        google_api_key = get_google_api_key(config)

        print(f"{Fore.CYAN}INFO: Initializing GenAI client.{Style.RESET_ALL}")
        client = genai.Client(api_key=google_api_key)
        print(f"{Fore.GREEN}SUCCESS: GenAI client initialized successfully.{Style.RESET_ALL}")
        return client
    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to initialize GenAI client: {e}{Style.RESET_ALL}")
        raise
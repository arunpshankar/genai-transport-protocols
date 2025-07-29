from typing import Optional
from colorama import Style
from colorama import Fore
from colorama import init 
from typing import Dict
from typing import Any
import json
import yaml

# Initialize colorama
init(autoreset=True)


def load_yaml(filename: str) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents.

    Args:
        filename (str): The path to the YAML file.

    Returns:
        Dict[str, Any]: The parsed YAML object.

    Raises:
        FileNotFoundError: If the file is not found.
        yaml.YAMLError: If there is an error parsing the YAML file.
        Exception: For any other exceptions.
    """
    try:
        with open(filename, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"{Fore.RED}File '{filename}' not found.{Style.RESET_ALL}")
        raise
    except yaml.YAMLError as e:
        print(f"{Fore.RED}Error parsing YAML file '{filename}': {e}{Style.RESET_ALL}")
        raise
    except Exception as e:
        print(f"{Fore.RED}Error loading YAML file: {e}{Style.RESET_ALL}")
        raise


def load_json(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file and return its contents.

    Args:
        filename (str): The path to the JSON file.

    Returns:
        Optional[Dict[str, Any]]: The parsed JSON object, or None if an error occurs.

    Raises:
        FileNotFoundError: If the file is not found.
        json.JSONDecodeError: If there is an error parsing the JSON file.
        Exception: For any other exceptions.
    """
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"{Fore.RED}File '{filename}' not found.{Style.RESET_ALL}")
        return None
    except json.JSONDecodeError:
        print(f"{Fore.RED}File '{filename}' contains invalid JSON.{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}Error loading JSON file: {e}{Style.RESET_ALL}")
        raise


def read_file(path: str) -> Optional[str]:
    """
    Reads the content of a markdown file and returns it as a text object.

    Args:
        path (str): The path to the markdown file.

    Returns:
        Optional[str]: The content of the file as a string, or None if the file could not be read.
    """
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content: str = file.read()
        return content
    except FileNotFoundError:
        print(f"{Fore.BLUE}File not found: {path}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.BLUE}Error reading file: {e}{Style.RESET_ALL}")
        return None


def write_to_file(path: str, content: str) -> None:
    """
    Writes content to a specified file. Appends to the file if it already exists.

    Args:
        path (str): The path to the file.
        content (str): The content to write to the file.

    Raises:
        Exception: For any other exceptions encountered during file writing.
    """
    try:
        with open(path, 'a', encoding='utf-8') as file:
            file.write(content)
        print(f"{Fore.GREEN}Content written to file: {path}{Style.RESET_ALL}")
    except FileNotFoundError:
        print(f"{Fore.RED}File not found: {path}{Style.RESET_ALL}")
        raise
    except Exception as e:
        print(f"{Fore.RED}Error writing to file '{path}': {e}{Style.RESET_ALL}")
        raise
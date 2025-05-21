#!/usr/bin/env python3

import argparse
import os
import configparser
from pathlib import Path
from colorama import Fore, init
from .ui_utils import create_box

# Initialize colorama
init(autoreset=True)

# Configuration file path
CONFIG_DIR = Path.home() / ".config" / "gitai"
CONFIG_FILE = CONFIG_DIR / "config.ini"

# Default values
DEFAULT_SUMMARY_MODEL = "gpt-4o-mini"
DEFAULT_SUMMARY_MAX_TOKENS = 300
DEFAULT_DESCRIPTION_MODEL = "gpt-4o-mini"
DEFAULT_DESCRIPTION_MAX_TOKENS = 400

def ensure_config_dir_exists():
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_config(config_data):
    """Save the configuration to the INI file."""
    ensure_config_dir_exists()
    config = configparser.ConfigParser()

    # Read existing config if it exists, to preserve other settings
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE)

    # Update OpenAI section
    if 'OpenAI' not in config:
        config['OpenAI'] = {}
    config['OpenAI']['api_key'] = config_data.get('api_key', '')

    # Update AI section
    if 'AI' not in config:
        config['AI'] = {}
    config['AI']['summary_model'] = config_data.get('summary_model', DEFAULT_SUMMARY_MODEL)
    config['AI']['summary_max_tokens'] = str(config_data.get('summary_max_tokens', DEFAULT_SUMMARY_MAX_TOKENS))
    config['AI']['description_model'] = config_data.get('description_model', DEFAULT_DESCRIPTION_MODEL)
    config['AI']['description_max_tokens'] = str(config_data.get('description_max_tokens', DEFAULT_DESCRIPTION_MAX_TOKENS))

    try:
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print(f"{Fore.GREEN}✓ Configuration saved successfully to {CONFIG_FILE}")
    except IOError as e:
        print(f"{Fore.RED}✗ Failed to save configuration: {e}")
        return False
    return True

def get_input_with_default(prompt, default):
    """Helper function to get input with a default value shown."""
    user_input = input(f"{Fore.WHITE}{prompt} [{default}]: ").strip()
    return user_input if user_input else default

def get_int_input_with_default(prompt, default):
    """Helper function to get integer input with a default."""
    while True:
        user_input = input(f"{Fore.WHITE}{prompt} [{default}]: ").strip()
        if not user_input:
            return default
        try:
            return int(user_input)
        except ValueError:
            print(f"{Fore.RED}"
                  f"✗ Please enter a valid integer.")

def main():
    parser = argparse.ArgumentParser(description="Set up the Git AI Toolkit configuration.")
    parser.add_argument("--key", type=str, help="Directly set the OpenAI API key.")
    # TODO: Add arguments for AI settings if non-interactive setup is needed
    args = parser.parse_args()

    print(create_box("Git AI Toolkit Setup"))

    # --- API Key --- 
    api_key = args.key
    if not api_key:
        print(f"\n{Fore.CYAN}--- OpenAI API Key ---")
        print(f"{Fore.YELLOW}Please enter your OpenAI API key.")
        print(f"{Fore.YELLOW}You can find your key at: https://platform.openai.com/api-keys")
        api_key = input(f"{Fore.WHITE}> ").strip()

    if not api_key:
        print(f"{Fore.RED}✗ API key cannot be empty. Setup aborted.")
        return
    if not api_key.startswith("sk-"):
         print(f"{Fore.YELLOW}⚠ Warning: API key does not look like a standard OpenAI key (should start with 'sk-').")

    # --- AI Settings --- 
    print(f"\n{Fore.CYAN}--- AI Model Configuration ---")
    print(f"{Fore.YELLOW}Enter the model names and max tokens for AI generation.")
    print(f"{Fore.YELLOW}Press Enter to accept the default value shown in brackets.")

    summary_model = get_input_with_default(
        "Model for commit summary", DEFAULT_SUMMARY_MODEL
    )
    summary_max_tokens = get_int_input_with_default(
        "Max tokens for summary", DEFAULT_SUMMARY_MAX_TOKENS
    )
    description_model = get_input_with_default(
        "Model for extended description", DEFAULT_DESCRIPTION_MODEL
    )
    description_max_tokens = get_int_input_with_default(
        "Max tokens for description", DEFAULT_DESCRIPTION_MAX_TOKENS
    )

    # --- Save Configuration --- 
    config_data = {
        "api_key": api_key,
        "summary_model": summary_model,
        "summary_max_tokens": summary_max_tokens,
        "description_model": description_model,
        "description_max_tokens": description_max_tokens,
    }
    save_config(config_data)

    # TODO: Add validation step here

if __name__ == "__main__":
    main()


#!/usr/bin/env python3

import os
import sys
import subprocess
import platform
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def check_openai_key_env():
    """Check if the OpenAI API key is set in environment variables."""
    return "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"]

def get_shell_config_file():
    """Determine the appropriate shell configuration file for the user's system."""
    system = platform.system()
    shell = os.environ.get('SHELL', '').lower()
    home = str(Path.home())
    
    if system == 'Darwin' or system == 'Linux':  # macOS or Linux
        if 'zsh' in shell:
            return os.path.join(home, '.zshrc'), 'zsh'
        elif 'bash' in shell:
            if system == 'Darwin':  # macOS uses .bash_profile by convention
                return os.path.join(home, '.bash_profile'), 'bash'
            return os.path.join(home, '.bashrc'), 'bash'
        else:
            return None, None
    elif system == 'Windows':
        return None, None  # Windows uses different methods
    
    return None, None

def add_key_to_shell_config(api_key):
    """Add the OpenAI API key to the shell configuration file."""
    config_file, shell_type = get_shell_config_file()
    
    if not config_file or not shell_type:
        print(f"{Fore.YELLOW}Automatic configuration not supported for your shell.")
        print(f"{Fore.YELLOW}Please manually add the following to your shell configuration file:")
        print(f"{Fore.GREEN}export OPENAI_API_KEY=\"{api_key}\"")
        return False
    
    try:
        # Check if file exists
        config_path = Path(config_file)
        if not config_path.exists():
            config_path.touch()
        
        # Read file content to check if key already exists
        with open(config_file, 'r') as f:
            content = f.read()
        
        if f"OPENAI_API_KEY" in content:
            print(f"{Fore.YELLOW}OpenAI API key already exists in {config_file}.")
            choice = input(f"{Fore.CYAN}Do you want to update it? (y/n): ").strip().lower()
            if choice != 'y':
                return False
        
        # Add key to file
        with open(config_file, 'a') as f:
            f.write(f"\n# Git AI Toolkit OpenAI API key\nexport OPENAI_API_KEY=\"{api_key}\"\n")
        
        print(f"{Fore.GREEN}✅ API key added to {config_file}")
        
        # Source the file to update current session
        if shell_type == 'zsh':
            print(f"{Fore.YELLOW}Please run: {Fore.WHITE}source {config_file}")
        elif shell_type == 'bash':
            print(f"{Fore.YELLOW}Please run: {Fore.WHITE}source {config_file}")
        
        return True
    except Exception as e:
        print(f"{Fore.RED}Error updating shell config: {e}")
        return False

def setup_windows_env_var(api_key):
    """Set environment variable on Windows."""
    try:
        # Use setx to set the user environment variable permanently
        subprocess.run(['setx', 'OPENAI_API_KEY', api_key], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        
        print(f"{Fore.GREEN}✅ API key added to Windows environment variables.")
        print(f"{Fore.YELLOW}Please restart your command prompt for the changes to take effect.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error setting environment variable: {e}")
        return False
    except Exception as e:
        print(f"{Fore.RED}Error: {e}")
        return False

def validate_openai_key(api_key):
    """Basic validation of the OpenAI API key format."""
    # OpenAI keys usually start with "sk-" and are 51 characters long
    if not api_key.startswith("sk-") or len(api_key) < 20:
        return False
    return True

def test_openai_connection(api_key):
    """Test the OpenAI API key by making a simple API call."""
    import openai
    
    try:
        # Create a temporary client with the provided key
        client = openai.OpenAI(api_key=api_key)
        
        # Make a simple API call
        print(f"{Fore.YELLOW}Testing API key connection...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API key is working!' in one short sentence."}
            ],
            max_tokens=10
        )
        
        if response.choices and response.choices[0].message:
            print(f"{Fore.GREEN}✅ API key is valid and working!")
            return True
        else:
            print(f"{Fore.RED}❌ API key test failed: No valid response received.")
            return False
    except openai.AuthenticationError:
        print(f"{Fore.RED}❌ API key authentication failed. Please check your API key.")
        return False
    except openai.APIConnectionError:
        print(f"{Fore.RED}❌ Could not connect to OpenAI API. Please check your internet connection.")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ API key test failed: {e}")
        return False

def setup_api_key():
    """Guide the user through setting up their OpenAI API key."""
    print(f"{Fore.CYAN}{'='*50}")
    print(f"{Fore.CYAN}{'Git AI Toolkit Setup':^50}")
    print(f"{Fore.CYAN}{'='*50}")
    
    # Check if key is already set
    if check_openai_key_env():
        print(f"{Fore.GREEN}✅ OpenAI API key is already set in your environment.")
        choice = input(f"{Fore.CYAN}Do you want to update it? (y/n): ").strip().lower()
        if choice != 'y':
            return True
    
    # Prompt for API key
    print(f"\n{Fore.CYAN}Please enter your OpenAI API key.")
    print(f"{Fore.YELLOW}You can find or create your API key at: {Fore.WHITE}https://platform.openai.com/api-keys")
    api_key = input(f"{Fore.CYAN}API Key: ").strip()
    
    # Basic validation
    if not validate_openai_key(api_key):
        print(f"{Fore.RED}❌ The API key format appears to be invalid.")
        print(f"{Fore.YELLOW}OpenAI API keys typically start with 'sk-' and are at least 20 characters long.")
        choice = input(f"{Fore.CYAN}Continue anyway? (y/n): ").strip().lower()
        if choice != 'y':
            return False
    
    # Set environment variable for current session
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Test connection with the key
    key_works = test_openai_connection(api_key)
    
    if not key_works:
        choice = input(f"{Fore.CYAN}Continue with setup anyway? (y/n): ").strip().lower()
        if choice != 'y':
            return False
    
    # Save key to configuration based on platform
    system = platform.system()
    if system == 'Windows':
        setup_windows_env_var(api_key)
    else:  # macOS or Linux
        add_key_to_shell_config(api_key)
    
    print(f"\n{Fore.GREEN}✅ Setup complete!")
    print(f"{Fore.YELLOW}You can now use the Git AI Toolkit commands like 'gitai'.")
    return True

def main():
    """Main entry point for the setup command."""
    try:
        setup_api_key()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Setup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
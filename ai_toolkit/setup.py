#!/usr/bin/env python3

import os
import sys
import subprocess
import platform
import argparse
import time
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Progress indicators
class Spinner:
    """Simple spinner for showing progress during long-running operations."""
    def __init__(self, message="Working", delay=0.1):
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.message = message
        self.delay = delay
        self.running = False
        self.spinner_index = 0
        
    def start(self):
        self.running = True
        print(f"\r{Fore.YELLOW}{self.message} {self.spinner_chars[0]}", end="")
        self.spinner_index = 0
        
    def update(self):
        if not self.running:
            return
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
        print(f"\r{Fore.YELLOW}{self.message} {self.spinner_chars[self.spinner_index]}", end="")
        sys.stdout.flush()
        time.sleep(self.delay)
        
    def stop(self, success=True, message=None):
        self.running = False
        icon = f"{Fore.GREEN}✓" if success else f"{Fore.RED}✗"
        final_message = message if message else self.message
        print(f"\r{icon} {final_message}{' ' * 20}")

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
    spinner = Spinner("Updating shell configuration")
    spinner.start()
    
    config_file, shell_type = get_shell_config_file()
    
    if not config_file or not shell_type:
        spinner.stop(False, "Automatic configuration not supported")
        print(f"{Fore.YELLOW}⚠ Automatic configuration not supported for your shell.")
        print(f"{Fore.YELLOW}  → Please manually add the following to your shell configuration file:")
        print(f"{Fore.CYAN}╭─{'─' * 48}╮")
        print(f"{Fore.CYAN}│ {Style.BRIGHT}Add to your shell config file{' ' * 21}│")
        print(f"{Fore.CYAN}╰─{'─' * 48}╯")
        print(f"{Fore.GREEN}export OPENAI_API_KEY=\"{api_key}\"")
        return False
    
    try:
        # Check if file exists
        config_path = Path(config_file)
        if not config_path.exists():
            spinner.update()
            config_path.touch()
        
        # Read file content to check if key already exists
        with open(config_file, 'r') as f:
            content = f.read()
        
        spinner.update()
        
        if f"OPENAI_API_KEY" in content:
            spinner.stop(False, "API key already exists in config")
            print(f"{Fore.YELLOW}⚠ OpenAI API key already exists in {config_file}.")
            print(f"{Fore.CYAN}Would you like to update it? (y/n): ", end="")
            choice = input().strip().lower()
            if choice != 'y':
                return False
            spinner = Spinner("Updating existing API key")
            spinner.start()
        
        # Add key to file
        with open(config_file, 'a') as f:
            f.write(f"\n# Git AI Toolkit OpenAI API key\nexport OPENAI_API_KEY=\"{api_key}\"\n")
        
        spinner.stop(True, f"API key added to {config_file}")
        
        # Source the file to update current session
        if shell_type == 'zsh' or shell_type == 'bash':
            print(f"{Fore.YELLOW}➤ To activate the key in your current shell, run:")
            print(f"{Fore.WHITE}  source {config_file}")
        
        return True
    except Exception as e:
        spinner.stop(False, "Error updating shell config")
        print(f"{Fore.RED}✗ Error updating shell configuration: {e}")
        print(f"{Fore.YELLOW}  → Try adding the key manually to your shell configuration")
        return False

def setup_windows_env_var(api_key):
    """Set environment variable on Windows."""
    spinner = Spinner("Setting Windows environment variable")
    spinner.start()
    
    try:
        # Use setx to set the user environment variable permanently
        subprocess.run(['setx', 'OPENAI_API_KEY', api_key], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        
        spinner.stop(True, "API key added to Windows environment variables")
        print(f"{Fore.YELLOW}➤ Please restart your command prompt for the changes to take effect.")
        return True
    except subprocess.CalledProcessError as e:
        spinner.stop(False, "Error setting environment variable")
        print(f"{Fore.RED}✗ Error setting environment variable: {e}")
        print(f"{Fore.YELLOW}  → Check if you have sufficient permissions")
        return False
    except Exception as e:
        spinner.stop(False, "Unexpected error")
        print(f"{Fore.RED}✗ Error: {e}")
        return False

def validate_openai_key(api_key):
    """Basic validation of the OpenAI API key format."""
    # OpenAI keys usually start with "sk-" and are 51 characters long
    if not api_key.startswith("sk-") or len(api_key) < 20:
        return False
    return True

def test_openai_connection(api_key):
    """Test the OpenAI API key by making a simple API call."""
    spinner = Spinner("Testing API key connection")
    spinner.start()
    
    try:
        import openai
        
        # Create a temporary client with the provided key
        client = openai.OpenAI(api_key=api_key)
        
        # Make a simple API call
        spinner.update()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API key is working!' in one short sentence."}
            ],
            max_tokens=10
        )
        
        if response.choices and response.choices[0].message:
            spinner.stop(True, "API key is valid and working!")
            return True
        else:
            spinner.stop(False, "API key test failed")
            print(f"{Fore.RED}✗ API key test failed: No valid response received.")
            print(f"{Fore.YELLOW}  → Check if your account has sufficient credits")
            return False
    except ImportError:
        spinner.stop(False, "OpenAI package not installed")
        print(f"{Fore.RED}✗ OpenAI package not installed properly.")
        print(f"{Fore.YELLOW}  → Run: pip install openai>=1.37.0")
        return False
    except openai.AuthenticationError:
        spinner.stop(False, "Authentication failed")
        print(f"{Fore.RED}✗ API key authentication failed.")
        print(f"{Fore.YELLOW}  → Double-check your API key at platform.openai.com")
        return False
    except openai.APIConnectionError:
        spinner.stop(False, "Connection error")
        print(f"{Fore.RED}✗ Could not connect to OpenAI API.")
        print(f"{Fore.YELLOW}  → Check your internet connection and try again")
        return False
    except Exception as e:
        spinner.stop(False, "API key test failed")
        print(f"{Fore.RED}✗ API key test failed: {e}")
        return False

def create_parser():
    """Create argument parser for setup CLI."""
    parser = argparse.ArgumentParser(
        description="Set up the Git AI Toolkit by configuring your OpenAI API key.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitai-setup                     # Interactive setup
  gitai-setup --key sk-xxx        # Directly set API key
  gitai-setup --skip-validation   # Skip API validation check
  
For more information, visit: https://github.com/maximilianlemberg-awl/git-ai-toolkit
"""
    )
    
    # Main options
    parser.add_argument("--key", "-k", type=str, 
                        help="Your OpenAI API key (if provided, skips prompt)")
    parser.add_argument("--skip-validation", "-s", action="store_true", 
                        help="Skip API key validation and testing")
    parser.add_argument("--version", "-v", action="store_true",
                        help="Show version information and exit")
    
    return parser

def print_version():
    """Print version information."""
    print(f"{Fore.CYAN}Git AI Toolkit Setup v0.2.3")
    print(f"{Fore.WHITE}A toolkit for using OpenAI models to assist with Git workflows")
    print(f"{Fore.WHITE}https://github.com/maximilianlemberg-awl/git-ai-toolkit")

def setup_api_key(api_key=None, skip_validation=False):
    """Guide the user through setting up their OpenAI API key."""
    print(f"{Fore.CYAN}╭─{'─' * 48}╮")
    print(f"{Fore.CYAN}│ {Style.BRIGHT}Git AI Toolkit Setup{' ' * 30}│")
    print(f"{Fore.CYAN}╰─{'─' * 48}╯")
    
    # Check if key is already set
    if check_openai_key_env() and api_key is None:
        print(f"{Fore.GREEN}✓ OpenAI API key is already set in your environment.")
        print(f"{Fore.CYAN}Would you like to update it? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            return True
    
    # Use provided key or prompt for one
    if api_key is None:
        # Prompt for API key
        print(f"\n{Fore.CYAN}Please enter your OpenAI API key:")
        print(f"{Fore.YELLOW}➤ You can find or create your API key at: {Style.BRIGHT}platform.openai.com/api-keys")
        print(f"{Fore.WHITE}> ", end="")
        api_key = input().strip()
    
    # Basic validation
    if not validate_openai_key(api_key) and not skip_validation:
        print(f"{Fore.RED}✗ The API key format appears to be invalid.")
        print(f"{Fore.YELLOW}  → OpenAI API keys typically start with 'sk-' and are at least 20 characters long.")
        print(f"{Fore.CYAN}Continue anyway? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            return False
    
    # Set environment variable for current session
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Test connection with the key
    key_works = True
    if not skip_validation:
        key_works = test_openai_connection(api_key)
    
    if not key_works and not skip_validation:
        print(f"{Fore.CYAN}Continue with setup anyway? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            return False
    
    # Save key to configuration based on platform
    system = platform.system()
    if system == 'Windows':
        success = setup_windows_env_var(api_key)
    else:  # macOS or Linux
        success = add_key_to_shell_config(api_key)
    
    if success:
        print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
        print(f"{Fore.CYAN}│ {Style.BRIGHT}Setup Complete{' ' * 34}│")
        print(f"{Fore.CYAN}╰─{'─' * 48}╯")
        print(f"{Fore.GREEN}✓ API key has been configured successfully!")
        print(f"{Fore.YELLOW}➤ You can now use Git AI Toolkit commands:")
        print(f"{Fore.WHITE}  gitai               {Fore.CYAN}# Generate AI commit messages")
        print(f"{Fore.WHITE}  gitai --help        {Fore.CYAN}# Show all available options")
        return True
    
    return False

def main():
    """Main entry point for the setup command."""
    try:
        # Parse arguments
        parser = create_parser()
        args = parser.parse_args()
        
        # Handle version flag
        if args.version:
            print_version()
            return
        
        # Run setup with provided arguments
        setup_api_key(args.key, args.skip_validation)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}✗ Setup cancelled by user (Ctrl+C).")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}✗ An unexpected error occurred: {e}")
        print(f"{Fore.YELLOW}  → Please report this issue on GitHub")
        sys.exit(1)

if __name__ == "__main__":
    main()
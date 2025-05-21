import openai
import os
from colorama import Fore, init

from .ui_utils import Spinner
from .config_manager import load_config

# Initialize colorama
init(autoreset=True)

# Initialize OpenAI client reference
client = None

def check_api_key():
    """Lazily initialize and verify the OpenAI client using API key."""
    global client
    if client is None:
        config = load_config()
        api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                client = openai.OpenAI(api_key=api_key)
                return True
            except Exception as e:
                print(f"{Fore.RED}✗ Failed to initialize OpenAI client: {e}")
                print(f"{Fore.YELLOW}  → Ensure your OPENAI_API_KEY environment variable is set.")
                print(f"{Fore.YELLOW}  → Run 'gitai-setup' or set the key manually.")
                return False
        else:
            print(f"{Fore.RED}✗ OpenAI API key is not configured.")
            print(f"{Fore.YELLOW}  → Ensure your OPENAI_API_KEY environment variable is set.")
            print(f"{Fore.YELLOW}  → Run 'gitai-setup' or set the key manually.")
            return False
    return True

def summarize_diff(user_prompt, system_prompt, model=None, max_tokens=None):
    """Generate a commit message using the OpenAI API, using configured model and tokens."""
    if not check_api_key():
        return None

    spinner = Spinner("Generating commit message with AI")
    spinner.start()

    try:
        # Load configuration and apply defaults if not provided
        config = load_config()
        if model is None:
            model = config['summary_model']
        if max_tokens is None:
            max_tokens = config['summary_max_tokens']
        response = client.chat.completions.create(  # type: ignore
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens
        )
        summary = response.choices[0].message.content
        spinner.stop(True, "Commit message generated")
        return summary
    except openai.APIConnectionError:
        spinner.stop(False, "Connection error")
        print(f"{Fore.RED}✗ Unable to connect to the OpenAI API.")
        print(f"{Fore.YELLOW}  → Please check your network connection")
        print(f"{Fore.YELLOW}  → Try again or run with '--offline' to manually write your commit")
    except openai.AuthenticationError:
        spinner.stop(False, "Authentication error")
        print(f"{Fore.RED}✗ Authentication failed with OpenAI.")
        print(f"{Fore.YELLOW}  → Your API key appears to be invalid")
        print(f"{Fore.YELLOW}  → Run 'gitai-setup' to update your API key")
    except openai.BadRequestError as e:
        spinner.stop(False, "Invalid request")
        print(f"{Fore.RED}✗ Bad request to OpenAI API: {e}")
        print(f"{Fore.YELLOW}  → This might be due to an issue with the request parameters")
    except Exception as e:
        spinner.stop(False, f"An unexpected error occurred: {e}")
        print(f"{Fore.RED}✗ Unexpected API error: {e}")
    
    return None # Return None on error

def generate_extended_description(diff_text):
    """Generates a more detailed description based on the diff using a secondary AI call."""
    if not check_api_key():
        return None

    spinner = Spinner("Generating extended description with AI")
    spinner.start()
    
    system_prompt = """Analyze the following code diff and provide a detailed explanation of the changes, focusing on the 'why' behind them. 
    Explain the purpose of the refactoring, the bug being fixed, or the feature being added. 
    Keep the description concise but informative, suitable for a git commit body.
    Do not include a commit subject line or type prefix.
    Wrap lines at 72 characters.
    """
    user_prompt = f"DIFF:\n{diff_text}\n\nDETAILED DESCRIPTION:"

    try:
        # Load configuration and apply defaults
        config = load_config()
        model = config.get('description_model')
        max_tokens = config.get('description_max_tokens')
        response = client.chat.completions.create(  # type: ignore
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens
        )
        description = response.choices[0].message.content.strip()
        spinner.stop(True, "Extended description generated")
        return description
    except Exception as e:
        spinner.stop(False, f"Failed to generate extended description: {e}")
        print(f"{Fore.RED}✗ Error generating extended description: {e}")
        return None


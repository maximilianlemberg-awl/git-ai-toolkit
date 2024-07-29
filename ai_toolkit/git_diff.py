#!/usr/bin/env python3

import os
import subprocess
import openai
from colorama import Fore, Style

client = openai.OpenAI()

def find_git_root():
    current_dir = os.getcwd()
    while current_dir != '/':
        if '.git' in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    print(f"{Fore.RED}No Git repository found.")
    return None

def get_git_diff(repo_path):
    result = subprocess.run(['git', '-C', repo_path, 'diff'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"{Fore.RED}Error: {result.stderr.decode('utf-8')}")
        return None
    return result.stdout.decode('utf-8')

def summarize_diff(diff_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at writing concise and informative git commit messages. Summarize the given diff in a single line of 50-72 characters, starting with an imperative verb. Focus on the 'why' behind the change, not just the 'what'. Avoid parentheses and unnecessary details. Use the present tense."},
                {"role": "user", "content": f"""Generate a concise git commit message for this diff:

                                                {diff_text}
                                                
                                                Guidelines:
                                                
                                                Start with an imperative verb (e.g., "Add", "Fix", "Refactor").
                                                Limit the message to 50-72 characters.
                                                Explain the reason for the change, focusing on the intent rather than the specific modifications.
                                                Use present tense.
                                                Be specific but concise, providing enough context for understanding.
                                                Avoid redundancy (e.g., "This commit...")."""}
            ],
            max_tokens=100
        )
        summary = response.choices[0].message.content
        return summary
    except openai.APIConnectionError:
        print(f"{Fore.RED}Error: Unable to connect to the OpenAI API. Please check your network connection.")
    except openai.AuthenticationError:
        print(f"{Fore.RED}Error: Authentication failed. Please check your API key.")
    except openai.BadRequestError as e:
        print(f"{Fore.RED}Error: Bad request - {e}. Please check the request parameters.")
    except openai.ConflictError:
        print(f"{Fore.RED}Error: Conflict detected. The resource may have been updated by another request.")
    except openai.InternalServerError:
        print(f"{Fore.RED}Error: Internal server error. Please try again later.")
    except openai.NotFoundError:
        print(f"{Fore.RED}Error: The requested resource was not found.")
    except openai.PermissionDeniedError:
        print(f"{Fore.RED}Error: Permission denied. You do not have access to the requested resource.")
    except openai.RateLimitError:
        print(f"{Fore.RED}Error: Rate limit exceeded. Please pace your requests.")
    except openai.UnprocessableEntityError:
        print(f"{Fore.RED}Error: The request could not be processed. Please try again.")
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred: {e}")
    return None

def main():
    repo_path = find_git_root()
    if not repo_path:
        return
    diff_text = get_git_diff(repo_path)
    if diff_text:
        summary = summarize_diff(diff_text)
        if summary is None:
            return
        print(f"{Fore.GREEN}Suggested commit message:\n\n{Style.BRIGHT}{summary}")

        confirm = input(f"{Fore.CYAN}Do you want to commit the changes with the above message? (y/n): ").strip().lower()
        if confirm == 'y':
            print(f"{Fore.YELLOW}Adding and committing changes...")
            subprocess.run(['git', '-C', repo_path, 'add', '-A'])
            subprocess.run(['git', '-C', repo_path, 'commit', '-m', summary])
            print(f"{Fore.GREEN}✅ Changes committed successfully.")

            confirm_push = input(
                f"{Fore.CYAN}Do you want to push the changes to the remote repository? (y/n): ").strip().lower()
            if confirm_push == 'y':
                print(f"{Fore.YELLOW}Pushing changes...")
                subprocess.run(['git', '-C', repo_path, 'push'])
                print(f"{Fore.GREEN}✅ Changes pushed successfully.")
            else:
                print(f"{Fore.RED}❌ Push canceled.")
        else:
            print(f"{Fore.RED}❌ Commit canceled.")
    else:
        print(f"{Fore.RED}No changes detected or an error occurred.")

if __name__ == "__main__":
    main()

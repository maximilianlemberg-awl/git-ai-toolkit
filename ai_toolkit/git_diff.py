#!/usr/bin/env python3

import os
import subprocess
import openai
from colorama import Fore, Style, init

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
    # Call the OpenAI API to get a summary
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who can succinctly summarize code changes. Summarize the given diff in a sentence of less than 80 characters. You should always avoid using pharenthesis in your summary."},
            {"role": "user", "content": f"Please summarize the following git diff for a commit message:\n\n{diff_text}"}
        ],
        max_tokens=100
    )
    summary = response.choices[0].message.content
    return summary


def main():
    repo_path = find_git_root()
    if not repo_path:
        return
    diff_text = get_git_diff(repo_path)
    if diff_text:
        summary = summarize_diff(diff_text)
        print(f"{Fore.GREEN}Suggested commit message:\n\n{Style.BRIGHT}{summary}")

        confirm = input(f"{Fore.CYAN}Do you want to commit the changes with the above message? (y/n): ").strip().lower()
        if confirm == 'y':
            print(f"{Fore.YELLOW}Adding and committing changes...")
            subprocess.run(['git', '-C', repo_path, 'add', '-A'])
            subprocess.run(['git', '-C', repo_path, 'commit', '-m', summary])
            print(f"{Fore.GREEN}✅ Changes committed successfully.")

            # Ask for second confirmation before pushing
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


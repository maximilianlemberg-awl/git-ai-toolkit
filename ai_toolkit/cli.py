#!/usr/bin/env python3

import argparse
import sys
import subprocess
import re # Import re for push output parsing
from colorama import Fore, init, Style

# Local imports
from . import __version__
from .git_utils import find_git_root, get_repository_context, get_git_changes, stage_specific_files
from .ai_service import summarize_diff, generate_extended_description, check_api_key
from .ui_utils import create_box, format_commit_display
from .utils import parse_commit_message, create_diff_prompt
from .config_manager import load_config

# Initialize colorama
init(autoreset=True)

def create_parser():
    """Create argument parser for CLI."""
    # Load configuration defaults
    config = load_config()
    default_model = config['summary_model']
    default_max_tokens = config['summary_max_tokens']
    default_behavior = config.get('default_command_behavior', 'default')
    # Determine default flags
    initial_stage = default_behavior in ['stage', 'stage_push']
    initial_push = default_behavior == 'stage_push'

    parser = argparse.ArgumentParser(
        description="Generate AI-powered Git commit messages and streamline your Git workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  gitai                    # Generate commit message for all changes
  gitai --stage            # Stage all changes and generate commit
  gitai --offline          # Skip AI generation and write manually
  gitai --push             # Automatically push after committing
  gitai --model gpt-4o     # Use a specific OpenAI model

Version: {__version__}
For more information, visit: https://github.com/maximilianlemberg-awl/git-ai-toolkit
"""
    )

    # Main options (respect config defaults)
    parser.add_argument("--stage", "-s", action=argparse.BooleanOptionalAction, default=initial_stage,
                        help=f"Stage all unstaged files before generating commit (default: {'on' if initial_stage else 'off'})")
    parser.add_argument("--push", "-p", action=argparse.BooleanOptionalAction, default=initial_push,
                        help=f"Push changes after committing (default: {'on' if initial_push else 'off'})")
    parser.add_argument("--offline", "-o", action="store_true",
                        help="Skip AI generation and craft commit message manually")

    # Advanced options
    advanced = parser.add_argument_group("Advanced options")
    advanced.add_argument("--model", "-m", type=str, default=default_model,
                        help=f"OpenAI model to use (default: {default_model})")
    advanced.add_argument("--max-tokens", type=int, default=default_max_tokens,
                        help=f"Maximum tokens for AI response (default: {default_max_tokens})")
    advanced.add_argument("--debug", action="store_true",
                        help="Show detailed debug information")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}",
                        help="Show version information and exit")

    return parser

def create_commit_manual(parsed_commit=None):
    """Create a commit message manually, optionally pre-filling from parsed AI suggestion."""
    print("\n" + create_box("Manual Commit Message Edit"))

    initial_subject = parsed_commit['title'] if parsed_commit else ""
    initial_body = parsed_commit['body'] if parsed_commit else ""

    print(f"{Fore.YELLOW}Enter subject line (max 50 chars recommended):")
    print(f"{Fore.WHITE}> {initial_subject}", end="")
    subject = input().strip()
    if not subject and initial_subject: # Keep initial if user enters nothing
        subject = initial_subject
    elif not subject: # Handle case where initial was also empty
        print(f"{Fore.RED}✗ Subject cannot be empty.")
        return None # Indicate failure

    print(f"\n{Fore.YELLOW}Enter commit body (optional, press Enter on empty line to finish):")
    print(f"{Fore.YELLOW}Initial body:")
    print(Fore.WHITE + initial_body.replace("\n", "\n" + Fore.WHITE)) # Print initial body
    print(f"{Fore.YELLOW}Type your edits below (leave empty to keep initial body, type '-' to clear):")

    body_lines = []
    first_line = True
    while True:
        print(f"{Fore.WHITE}> ", end="")
        line = input().rstrip()
        if not line and first_line:
            if initial_body:
                 user_choice = input(f"{Fore.CYAN}Keep initial body? [Y/n/- (clear)]: ").strip().lower()
                 if user_choice == 'n':
                     print(f"{Fore.YELLOW}Enter new body:")
                     first_line = False
                     continue
                 elif user_choice == '-':
                     body_lines = []
                     break
                 else:
                    body_lines = initial_body.splitlines()
                    break
            else:
                 break
        elif not line:
             break

        body_lines.append(line)
        first_line = False

    body = "\n".join(body_lines).strip()
    full_message = subject
    if body:
        full_message += f"\n\n{body}"

    # Reparse to get type/prefix if subject changed
    reparsed = parse_commit_message(full_message)

    return {
        "title": reparsed['title'],
        "body": reparsed['body'],
        "type": reparsed['type'],
        "prefix": reparsed['prefix'],
        "full_message": full_message
    }

def main():
    try:
        parser = create_parser()
        args = parser.parse_args()
        # If pushing is enabled and staging disabled but not explicitly disabled, enable staging
        if args.push and not args.stage and '--no-stage' not in sys.argv:
            args.stage = True
            print(f"{Fore.CYAN}ℹ Enabling staging because push is enabled.")

        # Find git repository
        repo_path = find_git_root()
        if not repo_path:
            sys.exit(1)

        # Get repository context
        repo_context = get_repository_context(repo_path)

        # Auto-stage changes if requested (use lightweight name-only check to avoid duplicate full diffs)
        if args.stage:
            names_result = subprocess.run(['git', '-C', repo_path, 'diff', '--name-only'],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            unstaged_names = names_result.stdout.splitlines()
            if unstaged_names:
                if stage_specific_files(repo_path):
                    pass
                else:
                    print(f"{Fore.RED}✗ Failed to stage changes. Aborting.")
                    sys.exit(1)
            else:
                print(f"{Fore.YELLOW}⚠ No unstaged changes to stage.")

        # Collect full staged/unstaged diffs once
        changes = get_git_changes(repo_path)

        # Verify changes exist
        if not changes["has_staged"] and not changes["has_unstaged"]:
            print(f"{Fore.YELLOW}⚠ No changes detected in the repository.")
            print(f"{Fore.YELLOW}  → Make some changes or stage existing ones.")
            sys.exit(0)

        # Ensure staged changes before proceeding (unless offline)
        if not changes["has_staged"] and not args.offline:
            print(f"{Fore.YELLOW}⚠ No changes staged for commit.")
            print(f"{Fore.YELLOW}  → Stage changes using 'git add <files>' or use 'gitai --stage'.")
            sys.exit(0)

        # Handle modes
        parsed_commit = None
        if args.offline:
            if not changes["has_staged"]:
                 print(f"{Fore.YELLOW}⚠ No staged changes. In offline mode, you must stage changes manually first.")
                 sys.exit(1)
            parsed_commit = create_commit_manual()
            if not parsed_commit:
                print(f"{Fore.RED}✗ Commit creation cancelled or failed.")
                sys.exit(1)
        else:
            # Online mode
            if not check_api_key():
                sys.exit(1)

            system_prompt, user_prompt = create_diff_prompt(repo_context, changes)
            if not system_prompt:
                print(f"{Fore.YELLOW}⚠ No changes found to generate commit message for.")
                sys.exit(0)

            ai_summary = summarize_diff(user_prompt, system_prompt,
                                       model=args.model,
                                       max_tokens=args.max_tokens)
            if not ai_summary:
                print(f"{Fore.RED}✗ Failed to generate commit message summary.")
                sys.exit(1)

            parsed_commit = parse_commit_message(ai_summary)
            parsed_commit["full_message"] = ai_summary # Store original full message

        # Confirmation loop
        while True:
            print("\n" + format_commit_display(parsed_commit))

            subject_len = len(parsed_commit['title'])
            subject_status = f"{Fore.GREEN}✓" if subject_len <= 50 else f"{Fore.RED}✗"
            print(f"{subject_status} Subject line: {subject_len}/50 characters")

            print(f"\n{Fore.CYAN}Commit this message? [Y/e/n] (Yes / Edit / No): ", end="")
            confirm = input().strip().lower()

            if confirm == 'y' or confirm == '':
                break
            elif confirm == 'e':
                edited_commit = create_commit_manual(parsed_commit)
                if edited_commit:
                    parsed_commit = edited_commit
                else:
                    print(f"{Fore.YELLOW}⚠ Edit cancelled. Keeping previous message.")
            elif confirm == 'n':
                print(f"{Fore.RED}✗ Commit aborted by user.")
                sys.exit(0)
            else:
                print(f"{Fore.RED}✗ Invalid choice. Please enter Y, e, or n.")

        try:
            commit_cmd = ['git', '-C', repo_path, 'commit', '-m', parsed_commit["full_message"]]
            result = subprocess.run(commit_cmd, capture_output=True, text=True, check=True)
            print(f"{Fore.GREEN}✓ Commit successful!")
            print(result.stdout.strip())

            # Push if requested
            if args.push:
                print(f"{Fore.CYAN}Pushing changes...")
                push_cmd = ['git', '-C', repo_path, 'push']
                push_result = subprocess.run(push_cmd, capture_output=True, text=True)
                if push_result.returncode == 0:
                    print(f"{Fore.GREEN}✓ Changes pushed successfully!")
                    print(push_result.stdout.strip())
                else:
                    print(f"{Fore.RED}✗ Failed to push changes:")
                    print(push_result.stderr.strip())
                    # Suggest PR/MR URLs
                    pr_patterns = [
                        r"(https://github.com/[^/]+/[^/]+/pull/new/\S+)",
                        r"(https://gitlab.com/[^/]+/[^/]+/-/merge_requests/new\?merge_request%5Bsource_branch%5D=\S+)"
                    ]
                    for pattern in pr_patterns:
                        match = re.search(pattern, push_result.stderr)
                        if match:
                            print(f"{Fore.YELLOW}  → Create Pull/Merge Request: {match.group(1)}")
                            break

        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}✗ Failed to commit changes:")
            print(e.stderr.strip())
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}✗ An unexpected error occurred during commit/push: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Operation cancelled by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()


#!/usr/bin/env python3

import os
import subprocess
import openai
import json
import sys
import argparse
import time
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Initialize OpenAI client
try:
    client = openai.OpenAI()
except Exception:
    client = None

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

def find_git_root():
    """Find the root directory of the Git repository."""
    current_dir = os.getcwd()
    while current_dir != '/':
        if '.git' in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    print(f"{Fore.RED}✗ No Git repository found in current directory or its parents.")
    return None

def get_repository_context(repo_path):
    """Get contextual information about the repository and its changes."""
    spinner = Spinner("Analyzing repository context")
    spinner.start()
    
    try:
        # Get current branch name
        branch_result = subprocess.run(['git', '-C', repo_path, 'branch', '--show-current'], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        current_branch = branch_result.stdout.decode('utf-8').strip() if branch_result.returncode == 0 else "unknown"
        spinner.update()
        
        # Get file statistics for better context
        stats_result = subprocess.run(['git', '-C', repo_path, 'diff', '--stat'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stats = stats_result.stdout.decode('utf-8') if stats_result.returncode == 0 else ""
        spinner.update()
        
        # Get modified file types for context
        files_result = subprocess.run(['git', '-C', repo_path, 'diff', '--name-only'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        changed_files = files_result.stdout.decode('utf-8').splitlines() if files_result.returncode == 0 else []
        spinner.update()
        
        # Extract file extensions to understand languages/components being modified
        file_types = {}
        for file in changed_files:
            ext = os.path.splitext(file)[1]
            if ext:
                file_types[ext] = file_types.get(ext, 0) + 1
        
        result = {
            "branch": current_branch,
            "stats": stats,
            "file_types": file_types,
            "changed_files": changed_files
        }
        
        spinner.stop(True, "Repository context analyzed")
        return result
    except Exception as e:
        spinner.stop(False, f"Failed to analyze repository context: {e}")
        return {
            "branch": "unknown",
            "stats": "",
            "file_types": {},
            "changed_files": []
        }

def get_git_changes(repo_path):
    """Get comprehensive diff information including both staged and unstaged changes."""
    spinner = Spinner("Collecting Git changes")
    spinner.start()
    
    try:
        # Get unstaged changes
        unstaged_result = subprocess.run(['git', '-C', repo_path, 'diff'], 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        unstaged = unstaged_result.stdout.decode('utf-8') if unstaged_result.returncode == 0 else ""
        spinner.update()
        
        # Get staged changes
        staged_result = subprocess.run(['git', '-C', repo_path, 'diff', '--staged'], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        staged = staged_result.stdout.decode('utf-8') if staged_result.returncode == 0 else ""
        
        result = {
            "unstaged": unstaged,
            "staged": staged,
            "has_unstaged": bool(unstaged.strip()),
            "has_staged": bool(staged.strip())
        }
        
        spinner.stop(True, "Git changes collected")
        return result
    except Exception as e:
        spinner.stop(False, f"Failed to collect Git changes: {e}")
        return {
            "unstaged": "",
            "staged": "",
            "has_unstaged": False,
            "has_staged": False
        }

def create_diff_prompt(context, changes):
    """Create a comprehensive, context-rich prompt for the AI model."""
    # Combine staged and unstaged changes
    diff_content = ""
    if changes["has_staged"]:
        diff_content += f"STAGED CHANGES:\n{changes['staged']}\n\n"
    if changes["has_unstaged"]:
        diff_content += f"UNSTAGED CHANGES:\n{changes['unstaged']}"
    
    if not diff_content.strip():
        return None
    
    # Enhanced system prompt with clear formatting guidelines
    system_prompt = """You are an expert at writing high-quality git commit messages following best practices:

1. Format Requirements:
   - Start with an imperative verb (Add, Fix, Update, Refactor, etc.)
   - First line must be under 50 characters
   - No period at end of summary line
   - Only capitalize first word and proper nouns
   - Include a more detailed body when relevant, wrapped at 72 characters

2. Commit Classification (use appropriate type):
   - feat: New feature addition
   - fix: Bug fix
   - docs: Documentation changes
   - style: Code style/formatting changes (not affecting logic)
   - refactor: Code changes that neither fix bugs nor add features
   - perf: Performance improvements
   - test: Adding or modifying tests
   - chore: Maintenance tasks, dependency updates, etc.

Focus on WHY the change was made rather than just describing WHAT changed.
"""

    # Context-rich user prompt
    user_prompt = f"""Generate a clear, informative commit message for these changes:

REPOSITORY CONTEXT:
- Branch: {context['branch']}
- Files changed: {len(context['changed_files'])}
- File types modified: {', '.join([f'{ext} ({count})' for ext, count in context['file_types'].items()])}

FILE CHANGES:
{context['stats']}

DIFF:
{diff_content}

Format your response as:
1. A type prefix (feat/fix/docs/etc)
2. A clear subject line under 50 chars starting with imperative verb
3. An optional detailed body explaining the WHY of the changes

Example:
feat: Add authentication to API endpoints

Implement JWT-based authentication to secure API endpoints.
This prevents unauthorized access and supports role-based
permissions for different user types.
"""
    return system_prompt, user_prompt

def summarize_diff(user_prompt, system_prompt):
    """Generate a commit message using the OpenAI API."""
    spinner = Spinner("Generating commit message with AI")
    spinner.start()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300
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
        print(f"{Fore.YELLOW}  → Try again with smaller changes or run with '--debug' for details")
    except openai.ConflictError:
        spinner.stop(False, "API conflict")
        print(f"{Fore.RED}✗ Conflict detected with OpenAI API.")
        print(f"{Fore.YELLOW}  → The resource may have been updated by another request")
        print(f"{Fore.YELLOW}  → Please try again")
    except openai.InternalServerError:
        spinner.stop(False, "OpenAI server error")
        print(f"{Fore.RED}✗ OpenAI internal server error.")
        print(f"{Fore.YELLOW}  → This is an issue on OpenAI's end")
        print(f"{Fore.YELLOW}  → Please try again later or use '--offline' mode")
    except openai.NotFoundError:
        spinner.stop(False, "Resource not found")
        print(f"{Fore.RED}✗ OpenAI resource not found.")
        print(f"{Fore.YELLOW}  → The requested resource was not found")
        print(f"{Fore.YELLOW}  → Check if you're using a valid model ID")
    except openai.PermissionDeniedError:
        spinner.stop(False, "Permission denied")
        print(f"{Fore.RED}✗ Permission denied for OpenAI API.")
        print(f"{Fore.YELLOW}  → Your account may not have access to the requested model")
        print(f"{Fore.YELLOW}  → Check your account tier at platform.openai.com")
    except openai.RateLimitError:
        spinner.stop(False, "Rate limit exceeded")
        print(f"{Fore.RED}✗ OpenAI API rate limit exceeded.")
        print(f"{Fore.YELLOW}  → You've hit your rate limit or quota")
        print(f"{Fore.YELLOW}  → Wait a minute before retrying or check your usage limits")
    except openai.UnprocessableEntityError:
        spinner.stop(False, "Unprocessable request")
        print(f"{Fore.RED}✗ OpenAI could not process the request.")
        print(f"{Fore.YELLOW}  → The request format may be invalid")
        print(f"{Fore.YELLOW}  → Try again with a simplified diff or smaller changes")
    except Exception as e:
        spinner.stop(False, "Error generating message")
        print(f"{Fore.RED}✗ An unexpected error occurred: {e}")
        print(f"{Fore.YELLOW}  → Try again or use '--offline' mode to write your commit manually")
    return None

def parse_commit_message(message):
    """Parse and structure the AI-generated commit message."""
    lines = message.strip().split('\n')
    if not lines:
        return {"subject": "", "body": ""}
    
    # Extract the subject line (first line)
    subject = lines[0].strip()
    
    # Extract commit type if present
    commit_type = "unknown"
    type_prefixes = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore"]
    for prefix in type_prefixes:
        if subject.startswith(f"{prefix}:") or subject.startswith(f"{prefix}("):
            commit_type = prefix
            break
    
    # Extract body (everything after first line)
    body = "\n".join(lines[1:]).strip()
    if body and not lines[1]:  # Ensure proper formatting with blank line after subject
        body = body.lstrip('\n')
    
    return {
        "subject": subject,
        "body": body,
        "type": commit_type,
        "full_message": message.strip()
    }

def format_commit_display(parsed_commit):
    """Format the commit message for display with color-coding by type."""
    type_colors = {
        "feat": Fore.GREEN,
        "fix": Fore.RED,
        "docs": Fore.BLUE,
        "style": Fore.MAGENTA,
        "refactor": Fore.YELLOW,
        "perf": Fore.CYAN,
        "test": Fore.BLUE,
        "chore": Fore.WHITE,
        "unknown": Fore.WHITE
    }
    
    color = type_colors.get(parsed_commit["type"], Fore.WHITE)
    
    # Format the display with colored type
    display = f"{color}{Style.BRIGHT}{parsed_commit['subject']}{Style.RESET_ALL}"
    
    if parsed_commit["body"]:
        display += f"\n\n{parsed_commit['body']}"
    
    return display

def load_project_conventions(repo_path):
    """Load project-specific conventions from config or learn from commit history."""
    spinner = Spinner("Loading project conventions")
    spinner.start()
    
    # Try to load config file if exists
    config_path = os.path.join(repo_path, '.git-ai-config.json')
    config = {
        "max_subject_length": 50,
        "wrap_body_at": 72,
        "preferred_types": ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore"]
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
                spinner.update()
        except Exception as e:
            spinner.update()
            print(f"{Fore.YELLOW}⚠ Could not load config: {e}")
    
    # Learn from commit history
    try:
        # Get recent commit messages
        result = subprocess.run(
            ['git', '-C', repo_path, 'log', '-15', '--pretty=format:%s'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        spinner.update()
        
        if result.returncode == 0:
            history = result.stdout.decode('utf-8').splitlines()
            
            # Extract most common verbs and commit types
            verbs = []
            types = []
            
            for msg in history:
                # Extract type if conventional commit format
                type_match = msg.split(':', 1)[0].strip() if ':' in msg else None
                if type_match and type_match in config["preferred_types"]:
                    types.append(type_match)
                
                # Extract first word as verb
                parts = msg.split(':', 1)
                message = parts[1].strip() if len(parts) > 1 else parts[0]
                first_word = message.split(' ', 1)[0].lower() if message else ""
                if first_word and first_word[0].isalpha():
                    verbs.append(first_word)
            
            # Count frequencies
            verb_counts = {}
            for verb in verbs:
                verb_counts[verb] = verb_counts.get(verb, 0) + 1
            
            type_counts = {}
            for type_str in types:
                type_counts[type_str] = type_counts.get(type_str, 0) + 1
            
            # Store the most common ones
            config["common_verbs"] = [v for v, c in sorted(verb_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
            config["common_types"] = [t for t, c in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
            
    except Exception as e:
        spinner.update()
        print(f"{Fore.YELLOW}⚠ Could not analyze commit history: {e}")
    
    spinner.stop(True, "Project conventions loaded")
    return config

def stage_specific_files(repo_path, files=None):
    """Stage specific files instead of all changes."""
    if files is None:
        # Get list of all unstaged files
        result = subprocess.run(['git', '-C', repo_path, 'diff', '--name-only'], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            files = result.stdout.decode('utf-8').splitlines()
    
    if not files:
        print(f"{Fore.YELLOW}⚠ No files to stage.")
        return False
    
    # Display files that can be staged
    print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
    print(f"{Fore.CYAN}│ {Style.BRIGHT}Files with changes{' ' * 31}│")
    print(f"{Fore.CYAN}├─{'─' * 48}┤")
    
    for i, file in enumerate(files, 1):
        # Truncate filename if too long
        display_file = file
        if len(file) > 45:
            display_file = "..." + file[-42:]
        print(f"{Fore.CYAN}│ {Fore.WHITE}{i}. {display_file}{' ' * (47 - len(display_file) - len(str(i)))}│")
    
    print(f"{Fore.CYAN}╰─{'─' * 48}╯")
    
    print(f"\n{Fore.CYAN}Enter file numbers to stage (comma-separated, 'a' for all, or 'q' to cancel):")
    print(f"{Fore.WHITE}> ", end="")
    selection = input().strip().lower()
    
    if selection == 'q':
        print(f"{Fore.YELLOW}⚠ Staging cancelled.")
        return False
    elif selection == 'a':
        # Stage all files
        spinner = Spinner("Staging all files")
        spinner.start()
        subprocess.run(['git', '-C', repo_path, 'add', '-A'])
        spinner.stop(True, "All files staged successfully")
        return True
    else:
        try:
            # Stage selected files
            selected_indices = [int(idx.strip()) - 1 for idx in selection.split(',') if idx.strip()]
            if not selected_indices:
                print(f"{Fore.RED}✗ No valid selection made.")
                return False
                
            spinner = Spinner("Staging selected files")
            spinner.start()
            
            staged_count = 0
            for idx in selected_indices:
                if 0 <= idx < len(files):
                    subprocess.run(['git', '-C', repo_path, 'add', files[idx]])
                    staged_count += 1
                    spinner.update()
            
            if staged_count > 0:
                spinner.stop(True, f"{staged_count} file{'s' if staged_count != 1 else ''} staged successfully")
                return True
            else:
                spinner.stop(False, "No files were staged")
                return False
        except Exception as e:
            print(f"{Fore.RED}✗ Error parsing selection: {e}")
            print(f"{Fore.YELLOW}  → Please enter comma-separated numbers (e.g., 1,3,5)")
            return False

def generate_extended_description(diff_text):
    """Generate a more detailed commit description for complex changes."""
    if not diff_text or len(diff_text) < 500:  # Only for substantial changes
        return None
        
    spinner = Spinner("Generating extended description")
    spinner.start()
    
    prompt = f"""Analyze this diff and generate an extended commit description:

{diff_text[:4000]}  # Limit to avoid token issues

Focus on:
1. What problem this change solves
2. How it implements the solution
3. Any notable technical details
4. Potential impacts on other parts of the codebase
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate a detailed but concise explanation of code changes, suitable for a commit message body."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250
        )
        result = response.choices[0].message.content
        spinner.stop(True, "Extended description generated")
        return result
    except Exception as e:
        spinner.stop(False, f"Could not generate extended description")
        print(f"{Fore.YELLOW}⚠ Error generating extended description: {e}")
        return None

def check_api_key():
    """Check if the OpenAI API key is properly set and guide the user to set it up if not."""
    if not os.environ.get("OPENAI_API_KEY"):
        print(f"{Fore.RED}✗ OpenAI API key is not set in your environment variables.")
        print(f"{Fore.YELLOW}  → You can set up your API key by running: {Fore.WHITE}gitai-setup")
        choice = input(f"{Fore.CYAN}Would you like to run the setup now? (y/n): ").strip().lower()
        if choice == 'y':
            try:
                from ai_toolkit.setup import setup_api_key
                if setup_api_key():
                    # Reinitialize the client with the new key
                    global client
                    client = openai.OpenAI()
                    return True
                else:
                    return False
            except ImportError:
                print(f"{Fore.RED}✗ Setup module not found.")
                print(f"{Fore.YELLOW}  → Try running {Fore.WHITE}gitai-setup{Fore.YELLOW} manually")
                return False
        else:
            return False
    return True

def create_parser():
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Generate AI-powered Git commit messages and streamline your Git workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitai                    # Generate commit message for all changes
  gitai --stage            # Stage all changes and generate commit
  gitai --offline          # Skip AI generation and write manually
  gitai --push             # Automatically push after committing
  gitai --model gpt-4o     # Use a specific OpenAI model
  
For more information, visit: https://github.com/maximilianlemberg-awl/git-ai-toolkit
"""
    )
    
    # Main options
    parser.add_argument("--stage", "-s", action="store_true", 
                        help="Stage all unstaged files before generating commit")
    parser.add_argument("--push", "-p", action="store_true", 
                        help="Push changes after committing")
    parser.add_argument("--offline", "-o", action="store_true", 
                        help="Skip AI generation and craft commit message manually")
    
    # Advanced options
    advanced = parser.add_argument_group("Advanced options")
    advanced.add_argument("--model", "-m", type=str, default="gpt-4o-mini",
                        help="OpenAI model to use (default: gpt-4o-mini)")
    advanced.add_argument("--max-tokens", type=int, default=300,
                        help="Maximum tokens for AI response (default: 300)")
    advanced.add_argument("--debug", action="store_true",
                        help="Show detailed debug information")
    advanced.add_argument("--version", "-v", action="store_true",
                        help="Show version information and exit")
    
    return parser

def print_version():
    """Print version information."""
    print(f"{Fore.CYAN}Git AI Toolkit v0.2.3")
    print(f"{Fore.WHITE}A toolkit for using OpenAI models to assist with Git workflows")
    print(f"{Fore.WHITE}https://github.com/maximilianlemberg-awl/git-ai-toolkit")

def create_commit_manual():
    """Create a commit message manually when in offline mode."""
    print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
    print(f"{Fore.CYAN}│ {Style.BRIGHT}Manual Commit Message{' ' * 29}│")
    print(f"{Fore.CYAN}╰─{'─' * 48}╯")
    
    print(f"{Fore.YELLOW}Enter commit subject (first line, max 50 chars):")
    print(f"{Fore.WHITE}> ", end="")
    subject = input().strip()
    
    print(f"\n{Fore.YELLOW}Enter commit body (optional, press Enter on empty line to finish):")
    body_lines = []
    while True:
        print(f"{Fore.WHITE}> ", end="")
        line = input().rstrip()
        if not line:
            break
        body_lines.append(line)
    
    body = "\n".join(body_lines)
    full_message = subject
    if body:
        full_message += f"\n\n{body}"
    
    return {
        "subject": subject,
        "body": body,
        "type": subject.split(':', 1)[0] if ':' in subject else "unknown",
        "full_message": full_message
    }

def main():
    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle version flag
    if args.version:
        print_version()
        return
    
    # Check for API key configuration (skip if offline mode)
    if not args.offline and not check_api_key():
        return
    
    # Find git repository
    repo_path = find_git_root()
    if not repo_path:
        return
    
    # Get repository context and changes
    repo_context = get_repository_context(repo_path)
    changes = get_git_changes(repo_path)
    
    # Verify we have changes to commit
    if not changes["has_staged"] and not changes["has_unstaged"]:
        print(f"{Fore.YELLOW}⚠ No changes detected in the repository.")
        print(f"{Fore.YELLOW}  → First make some changes before running gitai")
        return
    
    # Auto-stage changes if requested
    if args.stage and changes["has_unstaged"]:
        print(f"{Fore.CYAN}Auto-staging all changes as requested...")
        subprocess.run(['git', '-C', repo_path, 'add', '-A'])
        # Refresh changes after staging
        changes = get_git_changes(repo_path)
        print(f"{Fore.GREEN}✓ All changes staged successfully")
    
    # Allow user to stage specific files if needed
    if changes["has_unstaged"] and not changes["has_staged"] and not args.offline:
        print(f"{Fore.CYAN}You have unstaged changes but nothing is staged yet.")
        print(f"{Fore.CYAN}Would you like to stage changes now? (y/n): ", end="")
        if input().strip().lower() == 'y':
            stage_specific_files(repo_path)
            # Refresh changes after staging
            changes = get_git_changes(repo_path)
    
    # Ensure we have staged changes to commit
    if not changes["has_staged"]:
        if args.offline:
            print(f"{Fore.YELLOW}⚠ No staged changes. You need to stage some changes first.")
            print(f"{Fore.CYAN}Would you like to stage all changes? (y/n): ", end="")
            if input().strip().lower() == 'y':
                subprocess.run(['git', '-C', repo_path, 'add', '-A'])
                # Refresh changes
                changes = get_git_changes(repo_path)
            else:
                print(f"{Fore.RED}✗ Cannot proceed without staged changes.")
                return
        else:
            print(f"{Fore.YELLOW}⚠ No staged changes. You need to stage some changes first.")
            print(f"{Fore.YELLOW}  → Use 'git add <files>' to stage specific files")
            print(f"{Fore.YELLOW}  → Or use 'gitai --stage' to automatically stage all changes")
            return
    
    # Use manual mode or AI generation
    if args.offline:
        parsed_commit = create_commit_manual()
        formatted_display = format_commit_display(parsed_commit)
    else:
        # Load project conventions
        conventions = load_project_conventions(repo_path)
        
        # Create diff content
        diff_prompt = create_diff_prompt(repo_context, changes)
        if not diff_prompt:
            print(f"{Fore.RED}✗ No diff content to analyze.")
            return
        
        # Generate commit message
        system_prompt, user_prompt = diff_prompt
        
        # Show debug information if requested
        if args.debug:
            print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
            print(f"{Fore.CYAN}│ {Style.BRIGHT}Debug Information{' ' * 31}│")
            print(f"{Fore.CYAN}╰─{'─' * 48}╯")
            print(f"{Fore.CYAN}Repository: {repo_path}")
            print(f"{Fore.CYAN}Branch: {repo_context['branch']}")
            print(f"{Fore.CYAN}Files changed: {len(repo_context['changed_files'])}")
            print(f"{Fore.CYAN}Model: {args.model}")
            print(f"{Fore.CYAN}Max tokens: {args.max_tokens}")
        
        summary = summarize_diff(user_prompt, system_prompt)
        if summary is None:
            # Offer to switch to offline mode
            print(f"{Fore.CYAN}Would you like to switch to offline mode and write manually? (y/n): ", end="")
            if input().strip().lower() == 'y':
                parsed_commit = create_commit_manual()
                formatted_display = format_commit_display(parsed_commit)
            else:
                return
        else:
            # Parse and format the generated message
            parsed_commit = parse_commit_message(summary)
            formatted_display = format_commit_display(parsed_commit)
            
            # Generate extended description for complex changes
            combined_diff = changes["staged"] + changes["unstaged"]
            if len(combined_diff) > 1000 and not parsed_commit["body"]:  # Only for substantial changes without existing body
                print(f"{Fore.YELLOW}Generating extended description for complex changes...")
                extended_desc = generate_extended_description(combined_diff)
                if extended_desc:
                    parsed_commit["body"] = extended_desc
                    parsed_commit["full_message"] = f"{parsed_commit['subject']}\n\n{extended_desc}"
                    formatted_display = format_commit_display(parsed_commit)
    
    # Display the suggestion
    print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
    print(f"{Fore.CYAN}│ {Style.BRIGHT}Commit Message{' ' * 35}│")
    print(f"{Fore.CYAN}╰─{'─' * 48}╯")
    
    # Display with highlighting for length guidance
    subject = parsed_commit['subject']
    if len(subject) > 50:
        subject_display = f"{subject[:50]}{Fore.RED}{Style.BRIGHT}{subject[50:]}"
    else:
        subject_display = subject
    
    print(f"\n{subject_display}")
    
    if parsed_commit["body"]:
        print(f"\n{parsed_commit['body']}")
    
    print("\n")
    
    # Show character count for subject line
    subject_len = len(parsed_commit['subject'])
    subject_status = f"{Fore.GREEN}✓" if subject_len <= 50 else f"{Fore.RED}✗"
    print(f"{subject_status} Subject line: {subject_len}/50 characters")
    
    # Prompt user for confirmation or edits
    print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
    print(f"{Fore.CYAN}│ {Style.BRIGHT}Options{' ' * 41}│")
    print(f"{Fore.CYAN}├─{'─' * 48}┤")
    print(f"{Fore.CYAN}│ {Fore.WHITE}y{Fore.CYAN} - Accept and commit{' ' * 29}│")
    print(f"{Fore.CYAN}│ {Fore.WHITE}e{Fore.CYAN} - Edit message before committing{' ' * 19}│")
    print(f"{Fore.CYAN}│ {Fore.WHITE}n{Fore.CYAN} - Cancel{' ' * 40}│")
    print(f"{Fore.CYAN}╰─{'─' * 48}╯")
    
    print(f"{Fore.CYAN}Your choice: ", end="")
    choice = input().strip().lower()
    
    if choice == 'e':
        print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
        print(f"{Fore.CYAN}│ {Style.BRIGHT}Edit Commit Message{' ' * 31}│")
        print(f"{Fore.CYAN}╰─{'─' * 48}╯")
        
        print(f"{Fore.YELLOW}Enter subject line (max 50 chars recommended):")
        print(f"{Fore.WHITE}> ", end="")
        subject = input().strip() or parsed_commit["subject"]
        
        print(f"\n{Fore.YELLOW}Enter commit body (press Enter on empty line to finish):")
        body_lines = []
        while True:
            print(f"{Fore.WHITE}> ", end="")
            line = input().rstrip()
            if not line:
                break
            body_lines.append(line)
        
        body = "\n".join(body_lines)
        commit_message = subject
        if body:
            commit_message += f"\n\n{body}"
        
        parsed_commit["full_message"] = commit_message
        parsed_commit["subject"] = subject
        parsed_commit["body"] = body
        
    if choice in ('y', 'e'):
        # Stage any remaining files if needed and explicitly requested
        if changes["has_unstaged"] and args.stage:
            spinner = Spinner("Staging remaining changes")
            spinner.start()
            subprocess.run(['git', '-C', repo_path, 'add', '-A'])
            spinner.stop(True, "All changes staged")
        
        # Commit changes
        spinner = Spinner("Creating commit")
        spinner.start()
        commit_result = subprocess.run(
            ['git', '-C', repo_path, 'commit', '-m', parsed_commit["full_message"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if commit_result.returncode == 0:
            # Get the commit hash for display
            hash_result = subprocess.run(
                ['git', '-C', repo_path, 'rev-parse', '--short', 'HEAD'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            commit_hash = hash_result.stdout.decode('utf-8').strip() if hash_result.returncode == 0 else "unknown"
            
            spinner.stop(True, f"Commit created successfully [{commit_hash}]")
            
            # Push if requested or prompt
            should_push = args.push
            if not should_push:
                print(f"{Fore.CYAN}Push changes to remote? (y/n): ", end="")
                should_push = input().strip().lower() == 'y'
            
            if should_push:
                spinner = Spinner("Pushing changes to remote")
                spinner.start()
                push_result = subprocess.run(['git', '-C', repo_path, 'push'], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE)
                
                if push_result.returncode == 0:
                    spinner.stop(True, "Changes pushed successfully")
                    
                    # Suggest next steps
                    print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
                    print(f"{Fore.CYAN}│ {Style.BRIGHT}Next Steps{' ' * 38}│")
                    print(f"{Fore.CYAN}╰─{'─' * 48}╯")
                    print(f"{Fore.GREEN}✓ Changes committed and pushed!")
                    print(f"{Fore.YELLOW}  → Create a pull request: git request-pull")
                    print(f"{Fore.YELLOW}  → Continue working on another task")
                else:
                    spinner.stop(False, "Push failed")
                    print(f"{Fore.RED}✗ Push failed: {push_result.stderr.decode('utf-8')}")
                    print(f"{Fore.YELLOW}  → You can push later with: git push")
            else:
                # Suggest next steps when not pushing
                print(f"\n{Fore.CYAN}╭─{'─' * 48}╮")
                print(f"{Fore.CYAN}│ {Style.BRIGHT}Next Steps{' ' * 38}│")
                print(f"{Fore.CYAN}╰─{'─' * 48}╯")
                print(f"{Fore.GREEN}✓ Changes committed locally!")
                print(f"{Fore.YELLOW}  → Push your changes: git push")
                print(f"{Fore.YELLOW}  → Continue making more changes")
        else:
            spinner.stop(False, "Commit failed")
            print(f"{Fore.RED}✗ Commit failed: {commit_result.stderr.decode('utf-8')}")
            print(f"{Fore.YELLOW}  → Check if you need to resolve conflicts")
            print(f"{Fore.YELLOW}  → Ensure all files are properly staged")
    else:
        print(f"{Fore.RED}✗ Operation cancelled.")
        print(f"{Fore.YELLOW}  → Your changes are still staged and ready to commit")
        print(f"{Fore.YELLOW}  → Run 'gitai' again when you're ready")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}✗ Operation cancelled by user (Ctrl+C).")
        sys.exit(1)
#!/usr/bin/env python3

import os
import subprocess
import openai
import json
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Initialize OpenAI client
try:
    client = openai.OpenAI()
except Exception:
    client = None

def find_git_root():
    """Find the root directory of the Git repository."""
    current_dir = os.getcwd()
    while current_dir != '/':
        if '.git' in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    print(f"{Fore.RED}No Git repository found.")
    return None

def get_repository_context(repo_path):
    """Get contextual information about the repository and its changes."""
    # Get current branch name
    branch_result = subprocess.run(['git', '-C', repo_path, 'branch', '--show-current'], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    current_branch = branch_result.stdout.decode('utf-8').strip() if branch_result.returncode == 0 else "unknown"
    
    # Get file statistics for better context
    stats_result = subprocess.run(['git', '-C', repo_path, 'diff', '--stat'], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stats = stats_result.stdout.decode('utf-8') if stats_result.returncode == 0 else ""
    
    # Get modified file types for context
    files_result = subprocess.run(['git', '-C', repo_path, 'diff', '--name-only'], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    changed_files = files_result.stdout.decode('utf-8').splitlines() if files_result.returncode == 0 else []
    
    # Extract file extensions to understand languages/components being modified
    file_types = {}
    for file in changed_files:
        ext = os.path.splitext(file)[1]
        if ext:
            file_types[ext] = file_types.get(ext, 0) + 1
    
    return {
        "branch": current_branch,
        "stats": stats,
        "file_types": file_types,
        "changed_files": changed_files
    }

def get_git_changes(repo_path):
    """Get comprehensive diff information including both staged and unstaged changes."""
    # Get unstaged changes
    unstaged_result = subprocess.run(['git', '-C', repo_path, 'diff'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    unstaged = unstaged_result.stdout.decode('utf-8') if unstaged_result.returncode == 0 else ""
    
    # Get staged changes
    staged_result = subprocess.run(['git', '-C', repo_path, 'diff', '--staged'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    staged = staged_result.stdout.decode('utf-8') if staged_result.returncode == 0 else ""
    
    return {
        "unstaged": unstaged,
        "staged": staged,
        "has_unstaged": bool(unstaged.strip()),
        "has_staged": bool(staged.strip())
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
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not load config: {e}")
    
    # Learn from commit history
    try:
        # Get recent commit messages
        result = subprocess.run(
            ['git', '-C', repo_path, 'log', '-15', '--pretty=format:%s'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
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
        print(f"{Fore.YELLOW}Warning: Could not analyze commit history: {e}")
    
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
        print(f"{Fore.YELLOW}No files to stage.")
        return False
    
    # Display files that can be staged
    print(f"{Fore.CYAN}Files with changes:")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    
    print(f"\n{Fore.CYAN}Enter file numbers to stage (comma-separated, 'a' for all, or 'q' to cancel): ", end="")
    selection = input().strip().lower()
    
    if selection == 'q':
        return False
    elif selection == 'a':
        # Stage all files
        subprocess.run(['git', '-C', repo_path, 'add', '-A'])
        print(f"{Fore.GREEN}All files staged.")
        return True
    else:
        try:
            # Stage selected files
            selected_indices = [int(idx.strip()) - 1 for idx in selection.split(',') if idx.strip()]
            for idx in selected_indices:
                if 0 <= idx < len(files):
                    subprocess.run(['git', '-C', repo_path, 'add', files[idx]])
                    print(f"{Fore.GREEN}Staged: {files[idx]}")
            return True
        except Exception as e:
            print(f"{Fore.RED}Error parsing selection: {e}")
            return False

def generate_extended_description(diff_text):
    """Generate a more detailed commit description for complex changes."""
    if not diff_text or len(diff_text) < 500:  # Only for substantial changes
        return None
        
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
        return response.choices[0].message.content
    except Exception as e:
        print(f"{Fore.YELLOW}Could not generate extended description: {e}")
        return None

def check_api_key():
    """Check if the OpenAI API key is properly set and guide the user to set it up if not."""
    if not os.environ.get("OPENAI_API_KEY"):
        print(f"{Fore.RED}❌ OpenAI API key is not set in your environment variables.")
        print(f"{Fore.YELLOW}You can set up your API key by running: {Fore.WHITE}ai-setup")
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
                print(f"{Fore.RED}Setup module not found. Try running {Fore.WHITE}ai-setup{Fore.RED} manually.")
                return False
        else:
            return False
    return True

def main():
    # Check for API key configuration
    if not check_api_key():
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
        print(f"{Fore.YELLOW}No changes detected in the repository.")
        return
    
    # Allow user to stage specific files if needed
    if changes["has_unstaged"] and not changes["has_staged"]:
        print(f"{Fore.CYAN}You have unstaged changes. Would you like to stage them? (y/n): ", end="")
        if input().strip().lower() == 'y':
            stage_specific_files(repo_path)
            # Refresh changes after staging
            changes = get_git_changes(repo_path)
    
    # Create diff content
    diff_prompt = create_diff_prompt(repo_context, changes)
    if not diff_prompt:
        print(f"{Fore.RED}No diff content to analyze.")
        return
    
    # Load project conventions
    conventions = load_project_conventions(repo_path)
    
    # Generate commit message
    system_prompt, user_prompt = diff_prompt
    print(f"{Fore.YELLOW}Generating commit message...")
    
    summary = summarize_diff(user_prompt, system_prompt)
    if summary is None:
        return
    
    # Parse and format the generated message
    parsed_commit = parse_commit_message(summary)
    formatted_display = format_commit_display(parsed_commit)
    
    # Generate extended description for complex changes
    combined_diff = changes["staged"] + changes["unstaged"]
    if len(combined_diff) > 1000:  # Only for substantial changes
        extended_desc = generate_extended_description(combined_diff)
        if extended_desc and not parsed_commit["body"]:
            parsed_commit["body"] = extended_desc
            parsed_commit["full_message"] = f"{parsed_commit['subject']}\n\n{extended_desc}"
    
    # Display the suggestion
    print(f"\n{Fore.GREEN}Suggested commit message:\n\n{formatted_display}\n")
    
    # Prompt user for confirmation or edits
    print(f"{Fore.CYAN}Options:")
    print(f"  y - Accept and commit")
    print(f"  e - Edit message before committing")
    print(f"  n - Cancel")
    choice = input(f"{Fore.CYAN}Your choice: ").strip().lower()
    
    if choice == 'e':
        print(f"{Fore.CYAN}Edit the commit message (press Enter on an empty line to finish):")
        subject = input(f"{Fore.WHITE}Subject: {Fore.GREEN}").strip() or parsed_commit["subject"]
        
        body_lines = []
        print(f"{Fore.WHITE}Body (empty line to finish):")
        while True:
            line = input(f"{Fore.GREEN}").rstrip()
            if not line:
                break
            body_lines.append(line)
        
        body = "\n".join(body_lines)
        commit_message = subject
        if body:
            commit_message += f"\n\n{body}"
        
        parsed_commit["full_message"] = commit_message
        
    if choice in ('y', 'e'):
        # Stage any remaining files if needed
        if changes["has_unstaged"]:
            print(f"{Fore.YELLOW}Staging all changes...")
            subprocess.run(['git', '-C', repo_path, 'add', '-A'])
        
        # Commit changes
        print(f"{Fore.YELLOW}Committing changes...")
        commit_result = subprocess.run(
            ['git', '-C', repo_path, 'commit', '-m', parsed_commit["full_message"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if commit_result.returncode == 0:
            print(f"{Fore.GREEN}✅ Changes committed successfully.")
            
            # Offer to push
            push_choice = input(f"{Fore.CYAN}Push changes to remote? (y/n): ").strip().lower()
            if push_choice == 'y':
                print(f"{Fore.YELLOW}Pushing changes...")
                push_result = subprocess.run(['git', '-C', repo_path, 'push'], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE)
                
                if push_result.returncode == 0:
                    print(f"{Fore.GREEN}✅ Changes pushed successfully.")
                else:
                    print(f"{Fore.RED}❌ Push failed: {push_result.stderr.decode('utf-8')}")
        else:
            print(f"{Fore.RED}❌ Commit failed: {commit_result.stderr.decode('utf-8')}")
    else:
        print(f"{Fore.RED}❌ Commit canceled.")

if __name__ == "__main__":
    main()
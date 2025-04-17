import os
import json
import re
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

def load_project_conventions(repo_path):
    """Load project-specific conventions from config or learn from commit history."""
    config_path = os.path.join(repo_path, '.gitai.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"{Fore.GREEN}✓ Loaded conventions from .gitai.json")
                return config
        except json.JSONDecodeError:
            print(f"{Fore.RED}✗ Error decoding .gitai.json. Using defaults.")
        except Exception as e:
            print(f"{Fore.RED}✗ Error loading .gitai.json: {e}. Using defaults.")
    
    # Placeholder for potentially learning conventions from history
    print(f"{Fore.YELLOW}⚠ No .gitai.json found. Using default conventions.")
    return {}

def parse_commit_message(message):
    """Parse the AI-generated commit message into title, body, and type."""
    lines = message.strip().split('\n')
    if not lines:
        return {"title": "", "body": "", "type": "unknown", "prefix": ""}
    
    # Extract the subject line (first line)
    subject = lines[0].strip()
    
    # Simple type extraction: Look for common prefixes like feat:, fix:, etc.
    match = re.match(r"^(\w+)(?:\(.+?\))?(!?):\s*(.*)", subject)
    commit_type = "unknown"
    commit_prefix = ""
    if match:
        commit_type = match.group(1).lower()
        commit_prefix = match.group(1) + (match.group(2) if match.group(2) else "")
        subject = match.group(3).strip()
    
    # The rest is the body
    body = "\n".join(lines[1:]).strip()
    if body and body.startswith("\n"):
        body = body.lstrip('\n')
    
    return {"title": subject, "body": body, "type": commit_type, "prefix": commit_prefix}

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
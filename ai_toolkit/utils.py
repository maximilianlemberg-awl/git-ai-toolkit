import re
from colorama import init

# Initialize colorama
init(autoreset=True)

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
    system_prompt = """You are an expert at writing concise, human-like git commit messages following best practices:

    1. Format Requirements:
       - Start with an imperative verb (Add, Fix, Update, Refactor, etc.)
       - First line (subject) MUST be under 50 characters. Be brief.
       - No period at end of summary line.
       - Only capitalize first word and proper nouns in the subject.
       - Include a detailed body ONLY IF NECESSARY to explain the 'why'. If the subject is self-explanatory for the changes, omit the body.
       - Body lines wrapped at 72 characters.
       - AVOID sounding like an AI. Write like a human developer. Use direct and active language.
       - AVOID phrases like "This commit...", "This change...", "The code was updated to...". Go straight to the point.

    2. Commit Classification (use appropriate type):
       - feat: New feature addition
       - fix: Bug fix
       - docs: Documentation changes
       - style: Code style/formatting changes (not affecting logic)
       - refactor: Code changes that neither fix bugs nor add features
       - perf: Performance improvements
       - test: Adding or modifying tests
       - chore: Maintenance tasks, dependency updates, etc.

    
        Focus on WHY the change was made, not just WHAT changed. Be specific and factual.
        If the changes are minor (e.g., typo fix, small style adjustment), a short, direct subject line is sufficient.
        If the diff is extensive, focus on the primary purpose or the most impactful changes for the commit message.
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
        3. An OPTIONAL detailed body explaining the WHY of the changes. Omit if subject is clear.
        
        Example 1 (simple change, no body needed):
        fix: Correct typo in README
        
        Example 2 (more complex, body explains 'why'):
        feat: Add user authentication endpoint
        
        Implement JWT-based authentication for the /login endpoint.
        This secures user access and lays groundwork for role-based permissions.
        
        Example 3 (refactor, concise body):
        refactor: Simplify user data fetching logic
        
        Consolidate user retrieval methods into a single service function
        to reduce code duplication and improve maintainability.
"""
    return system_prompt, user_prompt 
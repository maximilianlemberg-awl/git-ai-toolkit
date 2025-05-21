import os
import subprocess
import sys
from colorama import Fore, init
# Assuming ui_utils is in the same directory
from .ui_utils import Spinner

# Initialize colorama
init(autoreset=True)

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
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        spinner.update() # Keep update for potential future progress steps within this function

        # Get file statistics for better context
        stats_result = subprocess.run(['git', '-C', repo_path, 'diff', '--stat'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stats = stats_result.stdout if stats_result.returncode == 0 else ""
        spinner.update()

        # Get modified file types for context
        files_result = subprocess.run(['git', '-C', repo_path, 'diff', '--name-only'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        changed_files = files_result.stdout.splitlines() if files_result.returncode == 0 else []
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
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        unstaged = unstaged_result.stdout if unstaged_result.returncode == 0 else ""
        spinner.update()

        # Get staged changes
        staged_result = subprocess.run(['git', '-C', repo_path, 'diff', '--staged'],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        staged = staged_result.stdout if staged_result.returncode == 0 else ""

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

def stage_specific_files(repo_path, files=None):
    """Stages specific files or all changes if no files are specified."""
    if not files:
        command = ['git', '-C', repo_path, 'add', '.']
        message = "Staging all changes"
    else:
        command = ['git', '-C', repo_path, 'add'] + files
        message = f"Staging specific files: {', '.join(files)}"
        
    spinner = Spinner(message)
    spinner.start()
    
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            error_msg = f"Failed to stage files: {result.stderr.strip()}"
            spinner.stop(False, error_msg)
            print(f"{Fore.RED}{error_msg}")
            return False
            
        spinner.stop(True, "Files staged successfully")
        return True
    except Exception as e:
        error_msg = f"Exception occurred while staging files: {e}"
        spinner.stop(False, error_msg)
        print(f"{Fore.RED}{error_msg}")
        return False 
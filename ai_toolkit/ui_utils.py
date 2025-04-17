import sys
import time
import threading
from colorama import Fore, Style, init
import re

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
        self._thread = None

    def start(self):
        self.running = True
        self.spinner_index = 0
        print(f"\r{Fore.YELLOW}{self.message} {self.spinner_chars[0]}", end="")
        sys.stdout.flush()

        # Start continuous spinning in a separate thread
        def spin():
            while self.running:
                self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
                print(f"\r{Fore.YELLOW}{self.message} {self.spinner_chars[self.spinner_index]}", end="")
                sys.stdout.flush()
                time.sleep(self.delay)

        self._thread = threading.Thread(target=spin)
        self._thread.daemon = True
        self._thread.start()

    def update(self):
        # No longer needed for spinning animation, but kept for compatibility
        pass

    def stop(self, success=True, message=None):
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)  # Wait for thread to finish
        icon = f"{Fore.GREEN}✓" if success else f"{Fore.RED}✗"
        final_message = message if message else self.message
        print(f"\r{icon} {final_message}{' ' * 20}")

# Add other UI-related functions here later (e.g., create_box, format_commit_display)

# Box drawing and text formatting
def create_box(title, content_lines=None, min_width=48):
    """Create a visually appealing box around content."""
    content_lines = content_lines or []
    
    # Function to remove ANSI codes for width calculation
    def strip_ansi(text):
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)
        
    max_content_width = 0
    for line in content_lines:
        max_content_width = max(max_content_width, len(strip_ansi(line)))
    
    width = max(min_width, max_content_width + 4, len(strip_ansi(title)) + 4)
    
    # Top border
    box_str = f"{Fore.CYAN}╭{'─' * (width - 2)}╮\n"
    
    # Title line
    title_pad = (width - 2 - len(strip_ansi(title))) // 2
    box_str += f"│ {Fore.WHITE}{Style.BRIGHT}{' ' * title_pad}{title}{' ' * (width - 2 - len(strip_ansi(title)) - title_pad)}{Style.RESET_ALL}{Fore.CYAN} │\n"
    
    # Separator
    box_str += f"│{'─' * (width - 2)}│\n"
    
    # Content lines
    if content_lines:
        for line in content_lines:
            padded_line = line + ' ' * (width - 4 - len(strip_ansi(line)))
            box_str += f"│ {Fore.WHITE}{padded_line}{Style.RESET_ALL}{Fore.CYAN} │\n"
    else:
        box_str += f"│ {' ' * (width - 4)} │\n" # Empty content line if none provided
    
    # Bottom border
    box_str += f"╰{'─' * (width - 2)}╯{Style.RESET_ALL}"
    
    return box_str

def format_commit_display(parsed_commit):
    """Format the parsed commit message for display."""
    title = f"{parsed_commit['prefix']}: {parsed_commit['title']}"
    display_lines = [title]
    if parsed_commit['body']:
        display_lines.append("") # Blank line separator
        display_lines.extend(parsed_commit['body'].splitlines())
        
    return create_box("Generated Commit Message", display_lines) 
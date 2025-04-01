# 🧰 Git AI Toolkit

## 👋 Description

This tool can generate commit messages for your Git repository by summarizing the changes using the OpenAI API. It identifies the Git repository, checks for changes (both staged and unstaged), and uses OpenAI to provide a comprehensive commit message following conventional commit formats. If you approve, the changes can be committed and optionally pushed to the remote repository.

### Enhanced Features

- **Conventional Commit Format**: Uses standardized types (feat, fix, docs, etc.)
- **Smart Context Gathering**: Analyzes branch, file types, and repository context
- **Staged & Unstaged Changes**: Handles both types of changes with selective staging
- **Interactive Editing**: Edit commit messages before finalizing
- **Project-Specific Conventions**: Learns from your commit history
- **Color-Coded Output**: Better visual organization of information
- **Extended Description**: Auto-generates detailed descriptions for complex changes
- **Progress Indicators**: Spinners show status during long-running operations
- **Command-Line Options**: Full-featured command-line interface with help system
- **Clear Error Messages**: Human-readable errors with specific recovery steps
- **Smart Feedback**: Contextual suggestions for next steps after each action

## 🚀 Installation

Install the package via pip:

```sh
pip install git_ai_toolkit
```

## ⚙️ Configuration

### Option 1: Interactive Setup (Recommended)

Run the interactive setup command that will guide you through the process of configuring your OpenAI API key:

```sh
gitai-setup
```

The setup will:
1. Ask for your OpenAI API key
2. Validate the key format
3. Test the connection to the OpenAI API
4. Add the key to your environment variables permanently

### Option 2: Manual Setup

If you prefer to set up the API key manually:

1. **Add Your OpenAI API Key**

   Add your OpenAI API key to your environment variables by updating your shell's configuration file.

   For `zsh` (Zsh users):
   
   ```sh
   echo '\nexport OPENAI_API_KEY="your_openai_api_key_here"' >> ~/.zshrc
   source ~/.zshrc
   ```

   For `bash` (Bash users):
   
   ```sh
   echo '\nexport OPENAI_API_KEY="your_openai_api_key_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

   For `Windows` users:
   
   ```sh
   setx OPENAI_API_KEY "your_openai_api_key_here"
   ```

   Replace `your_openai_api_key_here` with your actual OpenAI API key.

## 💻 Usage

### Basic Usage

```sh
gitai             # Generate commit message for all changes
gitai --stage     # Stage all changes and generate commit
gitai --push      # Auto-push after committing
gitai --offline   # Skip AI and write commit manually 
```

### Complete Command Reference

#### Main Command: `gitai`

```
usage: gitai [-h] [--stage] [--push] [--offline] [--model MODEL]
             [--max-tokens MAX_TOKENS] [--debug] [--version]

Generate AI-powered Git commit messages and streamline your Git workflow.

options:
  -h, --help            show this help message and exit
  --stage, -s           Stage all unstaged files before generating commit
  --push, -p            Push changes after committing
  --offline, -o         Skip AI generation and craft commit message manually

Advanced options:
  --model MODEL, -m MODEL
                        OpenAI model to use (default: gpt-4o-mini)
  --max-tokens MAX_TOKENS
                        Maximum tokens for AI response (default: 300)
  --debug               Show detailed debug information
  --version, -v         Show version information and exit

Examples:
  gitai                    # Generate commit message for all changes
  gitai --stage            # Stage all changes and generate commit
  gitai --offline          # Skip AI generation and write manually
  gitai --push             # Automatically push after committing
  gitai --model gpt-4o     # Use a specific OpenAI model
```

#### Setup Command: `gitai-setup`

```
usage: gitai-setup [-h] [--key KEY] [--skip-validation] [--version]

Set up the Git AI Toolkit by configuring your OpenAI API key.

options:
  -h, --help            show this help message and exit
  --key KEY, -k KEY     Your OpenAI API key (if provided, skips prompt)
  --skip-validation, -s
                        Skip API key validation and testing
  --version, -v         Show version information and exit

Examples:
  gitai-setup                     # Interactive setup
  gitai-setup --key sk-xxx        # Directly set API key
  gitai-setup --skip-validation   # Skip API validation check
```

### Workflow Examples

#### Standard Workflow

1. Make changes to your code
2. Run `gitai` to generate a commit message
3. Review and accept or edit the generated message
4. Choose whether to push changes to remote

#### Quick Workflow

```sh
# Make changes to your code then:
gitai --stage --push  # Stage all changes, commit with AI message, and push
```

#### Manual Workflow

```sh
# Make changes to your code then:
gitai --offline  # Skip AI and write your own commit message
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.txt) file for more details.
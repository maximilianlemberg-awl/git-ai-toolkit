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

1. **Navigate to Your Git Project Directory**

    Ensure you are in the root directory of your Git repository:

    ```sh
    cd path/to/your/git/repository
    ```

2. **Run the Command**

    Execute the script using the command:

    ```sh
    gitai
    ```

3. **Follow the Prompts**

    - The script will check for a Git repository and detect changes.
    - It will then generate a suggested commit message using the OpenAI API.
    - You will have the option to commit the changes with the suggested message.
    - Finally, you will be prompted to push the changes to the remote repository.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.txt) file for more details.

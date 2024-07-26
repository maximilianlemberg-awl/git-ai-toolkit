# 🧰 Git AI Toolkit

## 👋 Description

This tool can generate commit messages for your Git repository by summarizing the changes using the OpenAI API. It identifies the Git repository, checks for changes using `git diff`, and uses OpenAI to provide a one-sentence summary of the changes. If you approve, the changes can be committed and optionally pushed to the remote repository.

## 🚀 Installation

Install the package via pip:

```sh
pip install git_ai_toolkit
```

## ⚙️ Configuration

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
    ai-commit
    ```

3. **Follow the Prompts**

    - The script will check for a Git repository and detect changes.
    - It will then generate a suggested commit message using the OpenAI API.
    - You will have the option to commit the changes with the suggested message.
    - Finally, you will be prompted to push the changes to the remote repository.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.txt) file for more details.

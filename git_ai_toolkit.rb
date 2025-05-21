class GitAiToolkit < Formula
  include Language::Python::Virtualenv

  desc "AI-powered Git commit message generator using OpenAI"
  homepage "https://github.com/maximilianlemberg-awl/git-ai-toolkit"
  url "https://github.com/maximilianlemberg-awl/git-ai-toolkit/archive/refs/tags/v0.2.4.tar.gz"
  sha256 "699cf3c1b08418275bbd4cca4ff3f6444517c89cdc2e16b40f57bd076f274e09"
  license "MIT"

  depends_on "python@3.9"

  resource "openai" do
    url "https://files.pythonhosted.org/packages/02/af/9ef59efdd6c4709ede18eb7f28df06c3b32064b1c2d2ed1a03d9b2e91f85/openai-1.37.0.tar.gz"
    sha256 "4ba5e8da45d8f3a5d56f2fd308b6803ef6ded7d71f6e39dfd6df789a332659b9"
  end

  resource "colorama" do
    url "https://files.pythonhosted.org/packages/d8/53/6f443c9a4a8358a93a6792e2acffb9d9d5cb0a5cfd8802644b7b1c9a02e4/colorama-0.4.6.tar.gz"
    sha256 "08695f5cb7ed6e0531a20572697297273c47b8cae5a63ffc6d6ed5c201be6e44"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    # Add a basic test that checks if the command exists and shows help
    assert_match "Generate AI-powered Git commit messages", shell_output("#{bin}/gitai --help")
    assert_match "Set up the Git AI Toolkit", shell_output("#{bin}/gitai-setup --help")
  end
end
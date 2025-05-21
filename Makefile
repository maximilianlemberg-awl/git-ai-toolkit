# Makefile for Git AI Toolkit Python CLI project

# Variables
PYTHON = python3
PIP = pip
VENV_DIR = .venv
SOURCE_DIRS = ai_toolkit tests
REQ = requirements.txt

default: help

.PHONY: help clean lint format test build install uninstall publish publish-test env

# Default help target
help:
	@echo "Available targets:"
	@echo "  help          Show this help message"
	@echo "  clean         Remove build, cache, and other artifacts"
	@echo "  lint          Run ruff linter on source and tests"
	@echo "  format        Format code with ruff"
	@echo "  test          Run pytest with coverage"
	@echo "  build         Clean and build sdist & wheel"
	@echo "  install       Install package locally"
	@echo "  uninstall     Uninstall package"
	@echo "  publish       Build and upload to PyPI"
	@echo "  publish-test  Build and upload to TestPyPI"
	@echo "  env           Create virtualenv and install dependencies"

# Clean temporary and build files
clean:
	@echo "Cleaning project..."
	@rm -rf __pycache__ */__pycache__ *.pyc *.pyo
	@rm -rf build/ dist/ *.egg-info/
	@rm -rf .coverage htmlcov/

# Lint using ruff
lint:
	@echo "Running ruff lint..."
	@command -v ruff >/dev/null 2>&1 || { echo "ruff not found. Install with '$(PIP) install ruff'"; exit 1; }
	@ruff check $(SOURCE_DIRS)

# Run tests with pytest and coverage
test:
	@echo "Running tests..."
	@command -v pytest >/dev/null 2>&1 || { echo "pytest not found. Install with '$(PIP) install pytest pytest-cov'"; exit 1; }
	@pytest --cov=ai_toolkit --cov-report=term-missing

# Build distribution packages
build: clean
	@echo "Building distributions..."
	@$(PYTHON) -c "import wheel" >/dev/null 2>&1 || { echo "wheel not found. Install with '$(PIP) install wheel'"; exit 1; }
	@$(PYTHON) setup.py sdist bdist_wheel

# Install the package locally
install: build
	@echo "Installing package..."
	@$(PIP) install .

# Uninstall the package
uninstall:
	@echo "Uninstalling package..."
	@$(PIP) uninstall -y git_ai_toolkit

# Publish to PyPI
publish: build
	@echo "Publishing to PyPI..."
	@command -v twine >/dev/null 2>&1 || { echo "twine not found. Install with '$(PIP) install twine'"; exit 1; }
	@twine upload dist/*

# Publish to TestPyPI
publish-test: build
	@echo "Publishing to TestPyPI..."
	@command -v twine >/dev/null 2>&1 || { echo "twine not found. Install with '$(PIP) install twine'"; exit 1; }
	@twine upload --repository testpypi dist/*

# Set up development environment
env:
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV_DIR)
	@echo "Activating venv and installing dependencies..."
	@$(VENV_DIR)/bin/$(PIP) install -r $(REQ) pytest pytest-cov ruff twine wheel
	@echo "To activate the virtual environment, run 'source $(VENV_DIR)/bin/activate'"


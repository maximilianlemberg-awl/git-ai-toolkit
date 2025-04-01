from setuptools import setup, find_packages

setup(
    name="git_ai_toolkit",
    version="0.2.3",
    description="A toolkit for using OpenAI's GPT-4o-mini model to assist with Git workflows.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Maximilian Lemberg",
    url="https://github.com/maximilianlemberg-awl/git-ai-toolkit",
    packages=find_packages(),
    install_requires=[
        "openai>=1.37.0",
        "colorama>=0.4.6"
    ],
    entry_points={
        'console_scripts': [
            'ai-commit=ai_toolkit.git_diff:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    license="MIT",
)
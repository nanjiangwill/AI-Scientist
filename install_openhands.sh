#!/bin/bash

echo "Installing OpenHands for AI Scientist Paper Reproduction..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install git and try again."
    exit 1
fi

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Installing poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Clone OpenHands repository if it doesn't exist
if [ ! -d "../openhands" ]; then
    echo "Cloning OpenHands repository..."
    cd ..
    git clone https://github.com/OpenHands/openhands.git
    cd openhands
else
    echo "OpenHands repository already exists, updating..."
    cd ../openhands
    git pull
fi

# Install OpenHands dependencies using poetry
echo "Installing OpenHands dependencies..."
poetry install

# Return to the AI-Scientist directory
cd ../AI-Scientist

echo "OpenHands installation complete!"
echo "You can now use OpenHands for paper reproduction with the AI Scientist framework."
echo "Example usage: python launch_paper_repro.py --pdf_path /path/to/paper.pdf --openhands_model_config llm.eval_sonnet" 
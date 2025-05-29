#!/bin/bash
# Potter runner script - automatically uses virtual environment

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if virtual environment exists
if [ ! -d "$DIR/.venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.py first."
    exit 1
fi

# Activate virtual environment and run the app
echo "🔄 Starting Potter..."
echo "ℹ️  Note: Configure your OpenAI API key in the app settings"
source "$DIR/.venv/bin/activate"
python "$DIR/src/potter.py"

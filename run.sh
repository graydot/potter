#!/bin/bash
# Rephrasely runner script - automatically uses virtual environment

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if virtual environment exists
if [ ! -d "$DIR/.venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.py first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "$DIR/.env" ]; then
    echo "❌ .env file not found. Please create one with your OpenAI API key."
    exit 1
fi

# Activate virtual environment and run the app
echo "🔄 Starting Rephrasely..."
source "$DIR/.venv/bin/activate"
python "$DIR/rephrasely.py"

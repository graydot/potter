#!/bin/bash

# Rephrasely Test Build Script
# Simple local build for testing before creating releases

set -e  # Exit on any error

echo "🔨 Rephrasely Test Build"
echo "========================="

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📂 Project root: $PROJECT_ROOT"

# Ensure we're in the virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected, activating..."
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ No virtual environment found at .venv/"
        echo "   Please create one with: python -m venv .venv"
        exit 1
    fi
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Install/update dependencies if needed
echo "📦 Checking dependencies..."
pip install --quiet -r requirements.txt
pip install --quiet pyinstaller

# Use existing build_app.py for the actual build
echo "🚀 Building app using build_app.py..."

if [[ -f "build_app.py" ]]; then
    python build_app.py
else
    echo "❌ build_app.py not found!"
    echo "   This script relies on the existing build_app.py for building"
    exit 1
fi

# Check if the build succeeded
if [[ -d "dist/Rephrasely.app" ]]; then
    echo "✅ Build successful!"
    echo ""
    echo "📱 App Location: dist/Rephrasely.app"
    
    # Calculate size
    APP_SIZE=$(du -sh "dist/Rephrasely.app" | cut -f1)
    echo "📏 App Size: $APP_SIZE"
    
    echo ""
    echo "🧪 Test Options:"
    echo "   • Test directly: open dist/Rephrasely.app"
    echo "   • Test in place: cd dist && open Rephrasely.app"
    echo "   • Test functionality: Run the app and try the hotkey"
    echo ""
    echo "💡 Tips:"
    echo "   • This is a test build - not signed for distribution"
    echo "   • Use this to verify changes before creating a release"
    echo "   • For releases, use: ./scripts/manual_release.sh"
else
    echo "❌ Build failed - app not found in dist/"
    exit 1
fi

echo "✨ Test build complete!" 
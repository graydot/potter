#!/bin/bash

# Setup Git Hooks for Rephrasely
# This script installs the pre-commit hook for automatic building

echo "🔧 Setting up Git Hooks for Rephrasely"
echo "======================================"

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📂 Project root: $PROJECT_ROOT"

# Check if we're in a git repository
if [[ ! -d ".git" ]]; then
    echo "❌ Error: Not in a git repository"
    echo "   Please run this script from the root of the Rephrasely git repository"
    exit 1
fi

# Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install pre-commit hook
if [[ -f ".githooks/pre-commit" ]]; then
    echo "📋 Installing pre-commit hook..."
    cp ".githooks/pre-commit" ".git/hooks/pre-commit"
    chmod +x ".git/hooks/pre-commit"
    echo "✅ Pre-commit hook installed"
else
    echo "❌ Error: .githooks/pre-commit not found"
    exit 1
fi

# Test the build script
if [[ -x "scripts/build_for_distribution.sh" ]]; then
    echo "✅ Build script found and executable"
else
    echo "⚠️  Making build script executable..."
    chmod +x "scripts/build_for_distribution.sh"
fi

echo ""
echo "🎉 Git Hooks Setup Complete!"
echo "============================"
echo ""
echo "🔄 The pre-commit hook will now:"
echo "   • Run automatically when you commit to main/master"
echo "   • Build the app for distribution"
echo "   • Add the built app to your commit"
echo ""
echo "💡 Tips:"
echo "   • Only commits to main/master trigger builds"
echo "   • Only commits with Python/config file changes trigger builds"
echo "   • The build process takes 1-2 minutes"
echo ""
echo "🚀 Ready for automated distribution builds!" 
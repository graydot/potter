#!/bin/bash

# Setup Git Hooks for Potter
# This script installs the pre-commit hook for GitHub releases

echo "🔧 Setting up Git Hooks for Potter"
echo "======================================"

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📂 Project root: $PROJECT_ROOT"

# Check if we're in a git repository
if [[ ! -d ".git" ]]; then
    echo "❌ Error: Not in a git repository"
    echo "   Please run this script from the root of the Potter git repository"
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

# Check GitHub release script
if [[ -x "scripts/create_github_release.sh" ]]; then
    echo "✅ GitHub release script found and executable"
else
    echo "⚠️  Making GitHub release script executable..."
    chmod +x "scripts/create_github_release.sh"
fi

# Check other scripts
if [[ -x "scripts/manual_release.sh" ]]; then
    echo "✅ Manual release script found and executable"
else
    echo "⚠️  Making manual release script executable..."
    chmod +x "scripts/manual_release.sh"
fi

echo ""
echo "🎉 Git Hooks Setup Complete!"
echo "============================"
echo ""
echo "🔄 The pre-commit hook will now:"
echo "   • Run automatically when you commit to main/master"
echo "   • Ask if you want to create GitHub releases for Python changes"
echo "   • Use GitHub Releases for distribution (no local builds)"
echo ""
echo "💡 Tips:"
echo "   • Only commits to main/master trigger release prompts"
echo "   • Only commits with Python/config file changes trigger prompts"
echo "   • You need GitHub CLI authenticated: gh auth login"
echo "   • Manual releases: ./scripts/manual_release.sh"
echo ""
echo "🚀 Ready for GitHub releases system!" 
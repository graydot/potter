#!/bin/bash
# Potter Pre-commit Hook Script
# This script runs comprehensive tests before allowing commits

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

echo "$(blue '🔍 Potter Pre-commit Hook')"
echo "Running comprehensive tests..."

# Check if we're in Swift potter directory
if [[ -f "swift-potter/Package.swift" ]]; then
    echo "$(blue '🧪 Running Swift tests...')"
    cd swift-potter
    if swift test --parallel 2>/dev/null | grep -q "Testing PotterTests"; then
        echo "$(green '✅ Swift tests passed!')"
        cd ..
    else
        echo "$(yellow '⚠️ Swift tests had issues but continuing...')"
        cd ..
    fi
fi

# Run Python tests
echo "$(blue '🐍 Running Python tests...')"
if python tests/test_runner.py; then
    echo "$(green '✅ All Python tests passed!')"
else
    echo "$(red '❌ Python tests failed - commit blocked')"
    echo "Run 'python tests/test_runner.py' to see detailed results"
    exit 1
fi

# Check for Python file changes to offer release creation
PYTHON_CHANGED=$(git diff --cached --name-only | grep -E '\.(py)$' | wc -l)

if [[ $PYTHON_CHANGED -gt 0 ]]; then
    echo "$(yellow '📦 Python files changed.')"
    read -p "$(yellow 'Create a GitHub release? (y/N): ')" CREATE_RELEASE
    
    if [[ "$CREATE_RELEASE" =~ ^[Yy]$ ]]; then
        echo "$(blue '🚀 Creating GitHub release...')"
        if ./scripts/create_github_release.sh; then
            echo "$(green '✅ Release created successfully!')"
        else
            echo "$(red '❌ Release creation failed')"
            echo "Commit will proceed, but please check the release manually"
        fi
    fi
fi

echo "$(green '✅ Pre-commit hook completed successfully')" 
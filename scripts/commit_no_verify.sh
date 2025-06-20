#!/bin/bash
# Emergency commit script - bypasses pre-commit hooks
# Use only when you need to commit without running tests (e.g., work in progress)

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }

echo "$(yellow '⚠️ Emergency Commit (No Tests)')"
echo "$(yellow 'This bypasses all pre-commit hooks including tests')"
echo ""

# Get commit message
if [[ -n "$1" ]]; then
    COMMIT_MSG="$1"
else
    read -p "Enter commit message: " COMMIT_MSG
fi

if [[ -z "$COMMIT_MSG" ]]; then
    echo "$(red '❌ Commit message required')"
    exit 1
fi

echo "$(yellow 'Committing without tests...')"
git commit --no-verify -m "$COMMIT_MSG"

if [[ $? -eq 0 ]]; then
    echo "$(green '✅ Commit successful')"
    echo "$(yellow '📋 Remember to run tests later:')"
    echo "$(yellow 'cd swift-potter && make test')"
else
    echo "$(red '❌ Commit failed')"
    exit 1
fi
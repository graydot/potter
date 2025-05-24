#!/bin/bash

# Manual GitHub Release Creation
# Simple wrapper for creating releases manually

echo "🚀 Manual GitHub Release Creation"
echo "================================="

# Check if in git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if the main release script exists
RELEASE_SCRIPT="$SCRIPT_DIR/create_github_release.sh"

if [[ ! -f "$RELEASE_SCRIPT" ]]; then
    echo "❌ Release script not found: $RELEASE_SCRIPT"
    exit 1
fi

if [[ ! -x "$RELEASE_SCRIPT" ]]; then
    echo "🔧 Making release script executable..."
    chmod +x "$RELEASE_SCRIPT"
fi

# Run the release script
echo "📦 Running GitHub release creation..."
echo ""

cd "$PROJECT_ROOT"
exec "$RELEASE_SCRIPT" 
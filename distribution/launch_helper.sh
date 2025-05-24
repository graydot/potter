#!/bin/bash

# Rephrasely Launch Helper
# This script helps launch Rephrasely if you're having issues with double-clicking

echo "🚀 Rephrasely Launch Helper"
echo "=========================="

# Check if the app exists
if [[ ! -d "Rephrasely.app" ]]; then
    echo "❌ Rephrasely.app not found in current directory"
    echo "   Please run this script from the folder containing Rephrasely.app"
    exit 1
fi

echo "📱 Found Rephrasely.app"

# Remove quarantine attribute if present
echo "🔓 Removing quarantine attribute..."
xattr -r -d com.apple.quarantine Rephrasely.app 2>/dev/null || echo "   No quarantine attribute found"

# Launch the app
echo "🚀 Launching Rephrasely..."
open Rephrasely.app

# Check if it's running
sleep 2
if pgrep -f "Rephrasely" > /dev/null; then
    echo "✅ Rephrasely is now running!"
    echo "   Look for the Rephrasely icon in your menu bar"
else
    echo "⚠️  Rephrasely may not have started properly"
    echo "   If you see security warnings, click 'Open' to allow the app"
    echo "   You can also try right-clicking the app and selecting 'Open'"
fi

echo ""
echo "💡 Tips:"
echo "   • Rephrasely runs in the background with a menu bar icon"
echo "   • If you don't see it, check your menu bar (top of screen)"
echo "   • The app may need a few seconds to fully start" 
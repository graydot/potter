#!/bin/bash

# Test DMG Creation Script
# Tests the DMG creation process without doing a full release

echo "🧪 Testing DMG Creation"
echo "======================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set up test variables
VERSION="test-$(date +%Y%m%d-%H%M%S)"
DMG_NAME="Rephrasely-$VERSION.dmg"
DMG_TEMP_NAME="temp_$DMG_NAME"
VOLUME_NAME="Rephrasely $VERSION"
DMG_DIR="dmg_staging_test"

echo "📁 Project root: $PROJECT_ROOT"
echo "🏷️  Test version: $VERSION"

# Clean up any previous test
cd "$PROJECT_ROOT"
rm -rf "$DMG_DIR" 2>/dev/null

# Check if app exists in dist
if [[ ! -d "dist/Rephrasely.app" ]]; then
    echo "⚠️  No app found in dist/, building first..."
    
    # Build the app quickly for testing
    if [[ -f "build_app.py" ]]; then
        python build_app.py --quick
    else
        echo "❌ build_app.py not found, cannot create test app"
        exit 1
    fi
    
    # Check again
    if [[ ! -d "dist/Rephrasely.app" ]]; then
        echo "❌ Failed to build app for testing"
        exit 1
    fi
fi

echo "✅ App found: dist/Rephrasely.app"

# Create test staging directory
echo "📦 Creating DMG staging directory..."
mkdir -p "$DMG_DIR"

# Copy app to staging
cp -R "dist/Rephrasely.app" "$DMG_DIR/"
echo "✅ Copied app to staging"

# Create Applications symlink
ln -s /Applications "$DMG_DIR/Applications"
echo "✅ Created Applications symlink"

# Create background directory and copy background
mkdir -p "$DMG_DIR/.background"

if [[ -f "assets/dmg_background.png" ]]; then
    cp "assets/dmg_background.png" "$DMG_DIR/.background/background.png"
    echo "✅ Using professional DMG background"
else
    echo "⚠️  Professional background not found, skipping background"
fi

# Calculate the size needed for the DMG
APP_SIZE_MB=$(du -sm "$DMG_DIR" | cut -f1)
DMG_SIZE_MB=$((APP_SIZE_MB + 50))  # Add 50MB padding

echo "📏 DMG size will be: ${DMG_SIZE_MB}MB"

# Create the DMG
echo "💿 Creating DMG..."
hdiutil create -srcfolder "$DMG_DIR" \
               -volname "$VOLUME_NAME" \
               -fs HFS+ \
               -fsargs "-c c=64,a=16,e=16" \
               -format UDRW \
               -size ${DMG_SIZE_MB}m \
               "$DMG_TEMP_NAME"

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to create DMG"
    rm -rf "$DMG_DIR"
    exit 1
fi

echo "✅ Created temporary DMG"

# Mount the DMG for customization
echo "🔧 Mounting DMG for customization..."
DMG_DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "$DMG_TEMP_NAME" | grep '^/dev/' | sed 1q | awk '{print $1}')
MOUNT_POINT="/Volumes/$VOLUME_NAME"

# Wait for mount
sleep 3

# Check if mounted
if [[ ! -d "$MOUNT_POINT" ]]; then
    echo "❌ Failed to mount DMG"
    rm -f "$DMG_TEMP_NAME"
    rm -rf "$DMG_DIR"
    exit 1
fi

echo "✅ DMG mounted at: $MOUNT_POINT"

# Set up the DMG window appearance using AppleScript
echo "🎨 Customizing DMG appearance..."
osascript << APPLESCRIPT
tell application "Finder"
    tell disk "$VOLUME_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {100, 100, 700, 500}
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 128
        
        -- Position the app icon
        set position of item "Rephrasely.app" of container window to {150, 200}
        
        -- Position the Applications symlink
        set position of item "Applications" of container window to {450, 200}
        
        -- Set background if available
        try
            set background picture of theViewOptions to file ".background:background.png"
        end try
        
        -- Update and close
        update without registering applications
        delay 2
        close
    end tell
end tell
APPLESCRIPT

if [[ $? -eq 0 ]]; then
    echo "✅ DMG appearance customized"
else
    echo "⚠️  AppleScript customization had issues, but continuing..."
fi

# Unmount the DMG
echo "📤 Unmounting DMG..."
hdiutil detach "$DMG_DEVICE"

if [[ $? -ne 0 ]]; then
    echo "⚠️  Warning: Failed to properly unmount DMG"
fi

# Convert to read-only compressed DMG
echo "🗜️  Converting to compressed DMG..."
hdiutil convert "$DMG_TEMP_NAME" -format UDZO -imagekey zlib-level=9 -o "$DMG_NAME"

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to convert DMG to compressed format"
    rm -f "$DMG_TEMP_NAME"
    rm -rf "$DMG_DIR"
    exit 1
fi

# Clean up
rm -f "$DMG_TEMP_NAME"
rm -rf "$DMG_DIR"

# Show results
DMG_SIZE=$(du -sh "$DMG_NAME" | cut -f1)
echo ""
echo "🎉 DMG Creation Test Successful!"
echo "================================"
echo "📦 Created: $DMG_NAME"
echo "📏 Size: $DMG_SIZE"
echo "🔍 Test the DMG by double-clicking it"
echo ""
echo "🗑️  To clean up: rm $DMG_NAME" 
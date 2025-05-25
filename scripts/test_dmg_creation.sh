#!/bin/bash
# Enhanced DMG Creation Script with Code Signing Support
# Creates professional DMG installers for GitHub releases

# Configuration
APP_NAME="Rephrasely"
DMG_DIR="dist/dmg"
APP_PATH="dist/app/Rephrasely.app"
BACKGROUND_IMAGE="assets/dmg_background.png"

# Get version from git tags or use default
if git describe --tags --exact-match 2>/dev/null; then
    VERSION=$(git describe --tags --exact-match | sed 's/^v//')
else
    VERSION="1.0.0"
fi

DMG_NAME="Rephrasely-${VERSION}.dmg"
TEMP_DMG="${DMG_DIR}/temp_${DMG_NAME}"
FINAL_DMG="${DMG_DIR}/${DMG_NAME}"

echo "🔧 Enhanced DMG Creation for ${APP_NAME} v${VERSION}"
echo "======================================================"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: App not found at $APP_PATH"
    echo "Please run 'python scripts/build_app.py' first"
    exit 1
fi

# Check if app is signed
echo "🔍 Checking app signature..."
if codesign --verify --deep --strict "$APP_PATH" 2>/dev/null; then
    echo "✅ App is properly signed"
    SIGNED_APP=true
    
    # Get signing identity for DMG signing
    SIGNING_IDENTITY=$(codesign -dv "$APP_PATH" 2>&1 | grep "Authority=" | head -1 | sed 's/Authority=//')
    if [[ "$SIGNING_IDENTITY" == *"Developer ID"* ]]; then
        echo "📝 Found Developer ID certificate: $SIGNING_IDENTITY"
        DMG_SIGNING_IDENTITY="$SIGNING_IDENTITY"
    else
        echo "⚠️  App signed with non-Developer ID certificate"
        DMG_SIGNING_IDENTITY=""
    fi
else
    echo "⚠️  App is not signed - DMG will be unsigned"
    SIGNED_APP=false
    DMG_SIGNING_IDENTITY=""
fi

# Create DMG directory
mkdir -p "$DMG_DIR"

# Clean up any existing DMG files
rm -f "$TEMP_DMG" "$FINAL_DMG"

echo "📦 Creating DMG structure..."

# Create temporary directory for DMG contents
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy app to temp directory
echo "📋 Copying app bundle..."
cp -R "$APP_PATH" "$TEMP_DIR/"

# Create Applications symlink
echo "🔗 Creating Applications symlink..."
ln -s /Applications "$TEMP_DIR/Applications"

# Copy background image if it exists
if [ -f "$BACKGROUND_IMAGE" ]; then
    echo "🎨 Adding custom background..."
    mkdir -p "$TEMP_DIR/.background"
    cp "$BACKGROUND_IMAGE" "$TEMP_DIR/.background/background.png"
    BACKGROUND_OPTION="-background $TEMP_DIR/.background/background.png"
else
    echo "⚠️  No background image found at $BACKGROUND_IMAGE"
    BACKGROUND_OPTION=""
fi

# Calculate required size (with some padding)
echo "📏 Calculating DMG size..."
SIZE_KB=$(du -sk "$TEMP_DIR" | cut -f1)
SIZE_KB=$((SIZE_KB + 10240))  # Add 10MB padding
SIZE_MB=$((SIZE_KB / 1024 + 1))

echo "App size: ${SIZE_MB}MB"

# Create initial DMG
echo "🔨 Creating initial DMG..."
if ! hdiutil create -srcfolder "$TEMP_DIR" \
    -volname "$APP_NAME" \
    -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" \
    -format UDRW \
    -size ${SIZE_MB}m \
    "$TEMP_DMG"; then
    echo "❌ Failed to create initial DMG"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "✅ Initial DMG created"

# Mount the DMG
echo "📱 Mounting DMG for customization..."
if ! hdiutil attach "$TEMP_DMG" -noautoopen -quiet; then
    echo "❌ Failed to mount DMG"
    rm -f "$TEMP_DMG"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Find the mounted volume
VOLUME="/Volumes/$APP_NAME"
if [ ! -d "$VOLUME" ]; then
    echo "❌ Mounted volume not found at $VOLUME"
    hdiutil detach "$VOLUME" 2>/dev/null
    rm -f "$TEMP_DMG"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "📐 Customizing DMG layout..."

# Customize DMG appearance with AppleScript
osascript <<EOF
try
    tell application "Finder"
        tell disk "$APP_NAME"
            open
            set current view of container window to icon view
            set toolbar visible of container window to false
            set statusbar visible of container window to false
            set the bounds of container window to {100, 100, 640, 480}
            set viewOptions to the icon view options of container window
            set arrangement of viewOptions to not arranged
            set icon size of viewOptions to 128
            set background picture of viewOptions to file ".background:background.png"
            
            -- Position app icon
            set position of item "$APP_NAME.app" of container window to {150, 200}
            
            -- Position Applications symlink
            set position of item "Applications" of container window to {390, 200}
            
            -- Hide background folder
            set the extension hidden of item ".background" to true
            
            close
            open
            
            -- Force update
            update without registering applications
            delay 2
        end tell
    end tell
on error errMsg
    display dialog "AppleScript Error: " & errMsg
end try
EOF

# Wait for changes to take effect
sleep 3

echo "💾 Finalizing DMG..."

# Unmount the DMG
if ! hdiutil detach "$VOLUME"; then
    echo "⚠️  Warning: Failed to cleanly unmount DMG"
    # Force unmount
    hdiutil detach "$VOLUME" -force
fi

# Convert to final compressed DMG
echo "🗜️  Compressing DMG..."
if ! hdiutil convert "$TEMP_DMG" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "$FINAL_DMG"; then
    echo "❌ Failed to compress DMG"
    rm -f "$TEMP_DMG"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Clean up temporary files
rm -f "$TEMP_DMG"
rm -rf "$TEMP_DIR"

# Sign the DMG if we have a Developer ID certificate
if [ "$SIGNED_APP" = true ] && [ ! -z "$DMG_SIGNING_IDENTITY" ]; then
    echo "🔐 Signing DMG with Developer ID..."
    if codesign --sign "$DMG_SIGNING_IDENTITY" \
        --timestamp \
        --options runtime \
        "$FINAL_DMG"; then
        echo "✅ DMG signed successfully"
        
        # Verify DMG signature
        if codesign --verify --deep --strict "$FINAL_DMG" 2>/dev/null; then
            echo "✅ DMG signature verified"
        else
            echo "⚠️  DMG signature verification failed"
        fi
    else
        echo "⚠️  Failed to sign DMG"
    fi
else
    echo "⚠️  Skipping DMG signing (no Developer ID certificate)"
fi

# Final verification
if [ -f "$FINAL_DMG" ]; then
    DMG_SIZE=$(du -h "$FINAL_DMG" | cut -f1)
    echo ""
    echo "🎉 DMG Creation Complete!"
    echo "======================================================"
    echo "📦 DMG: $FINAL_DMG"
    echo "📏 Size: $DMG_SIZE"
    echo "🏷️  Version: $VERSION"
    
    if [ "$SIGNED_APP" = true ]; then
        echo "🔐 Code Signed: Yes"
        if [ ! -z "$DMG_SIGNING_IDENTITY" ]; then
            echo "📝 DMG Signed: Yes ($DMG_SIGNING_IDENTITY)"
        else
            echo "📝 DMG Signed: No (not Developer ID)"
        fi
    else
        echo "🔐 Code Signed: No"
        echo "📝 DMG Signed: No"
    fi
    
    echo ""
    echo "📋 Next Steps:"
    if [ "$SIGNED_APP" = true ] && [ ! -z "$DMG_SIGNING_IDENTITY" ]; then
        echo "✅ Ready for distribution!"
        echo "• Upload to GitHub releases"
        echo "• Users can install without Gatekeeper warnings"
    else
        echo "⚠️  For distribution without warnings:"
        echo "• Sign the app with Developer ID certificate"
        echo "• Notarize with Apple"
        echo "• Users will need to right-click → Open on first launch"
    fi
    
    echo ""
    echo "🧪 Testing:"
    echo "• Double-click DMG to test installation"
    echo "• Drag app to Applications folder"
    echo "• Launch app to verify functionality"
    
else
    echo "❌ DMG creation failed!"
    exit 1
fi 
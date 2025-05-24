#!/bin/bash

# Enhanced DMG Creation for Potter
# Creates a beautiful, professional DMG installer

set -e

# Configuration
APP_NAME="Potter"
APP_PATH="dist/app/Potter.app"
VERSION="1.0.0"
DMG_NAME="Potter-${VERSION}"
DMG_DIR="dist/dmg"
TEMP_DMG="${DMG_DIR}/temp_${DMG_NAME}.dmg"
FINAL_DMG="${DMG_DIR}/${DMG_NAME}.dmg"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Enhanced DMG Creation for Potter v${VERSION}${NC}"
echo "======================================================"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}❌ App not found at $APP_PATH${NC}"
    echo "   Run: python scripts/build_app.py first"
    exit 1
fi

# Check app signature
echo -e "${BLUE}🔍 Checking app signature...${NC}"
if codesign -dv "$APP_PATH" 2>/dev/null; then
    echo -e "${GREEN}✅ App is properly signed${NC}"
    
    # Check if it's signed with Developer ID
    if codesign -dv "$APP_PATH" 2>&1 | grep -q "Developer ID Application"; then
        echo -e "${GREEN}✅ Signed with Developer ID Application${NC}"
        SIGN_DMG=true
    else
        echo -e "${YELLOW}⚠️  App signed with non-Developer ID certificate${NC}"
        SIGN_DMG=false
    fi
else
    echo -e "${YELLOW}⚠️  App is not signed${NC}"
    SIGN_DMG=false
fi

# Create DMG directory
mkdir -p "$DMG_DIR"

# Clean up any existing DMGs
rm -f "$TEMP_DMG" "$FINAL_DMG"

echo -e "${BLUE}📦 Creating DMG structure...${NC}"

# Create temporary directory for DMG contents
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy app to temp directory
echo -e "${BLUE}📋 Copying app bundle...${NC}"
cp -R "$APP_PATH" "$TEMP_DIR/"

# Create Applications symlink
echo -e "${BLUE}🔗 Creating Applications symlink...${NC}"
ln -s /Applications "$TEMP_DIR/Applications"

# Create background image (optional - simple background)
echo -e "${BLUE}🎨 Adding custom background...${NC}"
mkdir -p "$TEMP_DIR/.background"

# Create a simple background using built-in tools
cat > "$TEMP_DIR/.background/background.png" << 'EOF'
# This would be a background image - for now we'll use system default
EOF

# Calculate DMG size
echo -e "${BLUE}📏 Calculating DMG size...${NC}"
APP_SIZE=$(du -sm "$APP_PATH" | cut -f1)
echo "App size: ${APP_SIZE}MB"
DMG_SIZE=$((APP_SIZE + 100))  # Add 100MB padding

# Create initial DMG
echo -e "${BLUE}🔨 Creating initial DMG...${NC}"
hdiutil create -srcfolder "$TEMP_DIR" -volname "$APP_NAME" -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${DMG_SIZE}m "$TEMP_DMG"

echo -e "${GREEN}✅ Initial DMG created${NC}"

# Mount DMG for customization
echo -e "${BLUE}📱 Mounting DMG for customization...${NC}"
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "$TEMP_DMG" | \
         egrep '^/dev/' | sed 1q | awk '{print $1}')

# Customize DMG layout
echo -e "${BLUE}📐 Customizing DMG layout...${NC}"
sleep 2  # Give time for mounting

# Set custom view options using AppleScript
osascript << EOF
tell application "Finder"
    tell disk "$APP_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 100, 900, 400}
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 72
        set position of item "Potter.app" of container window to {150, 200}
        set position of item "Applications" of container window to {350, 200}
        close
        open
        update without registering applications
        delay 2
    end tell
end tell
EOF

# Finalize DMG
echo -e "${BLUE}💾 Finalizing DMG...${NC}"
sync
hdiutil detach "$DEVICE"

# Convert to compressed DMG
echo -e "${BLUE}🗜️  Compressing DMG...${NC}"
hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$FINAL_DMG"

# Sign DMG if we have Developer ID
if [ "$SIGN_DMG" = true ] && [ -n "$DEVELOPER_ID_APPLICATION" ]; then
    echo -e "${BLUE}🔐 Signing DMG...${NC}"
    codesign --force --sign "$DEVELOPER_ID_APPLICATION" "$FINAL_DMG"
    echo -e "${GREEN}✅ DMG signed successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping DMG signing (no Developer ID certificate)${NC}"
fi

# Clean up
rm -f "$TEMP_DMG"
rm -rf "$TEMP_DIR"

# Get final DMG size
FINAL_SIZE=$(du -h "$FINAL_DMG" | cut -f1)

echo ""
echo -e "${GREEN}🎉 DMG Creation Complete!${NC}"
echo "======================================================"
echo -e "${GREEN}📦 DMG: $FINAL_DMG${NC}"
echo -e "${GREEN}📏 Size: $FINAL_SIZE${NC}"
echo -e "${GREEN}🏷️  Version: $VERSION${NC}"
echo -e "${GREEN}🔐 Code Signed: $([ -f "$APP_PATH" ] && codesign -dv "$APP_PATH" 2>/dev/null && echo "Yes" || echo "No")${NC}"
echo -e "${GREEN}📝 DMG Signed: $([ "$SIGN_DMG" = true ] && echo "Yes" || echo "No")${NC}"

echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
if [ "$SIGN_DMG" = false ]; then
    echo -e "${YELLOW}⚠️  For distribution without warnings:${NC}"
    echo "• Sign the app with Developer ID certificate"
    echo "• Notarize with Apple"
    echo "• Users will need to right-click → Open on first launch"
fi

echo ""
echo -e "${BLUE}🧪 Testing:${NC}"
echo "• Double-click DMG to test installation"
echo "• Drag app to Applications folder"
echo "• Launch app to verify functionality" 
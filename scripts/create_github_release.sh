#!/bin/bash

# Potter GitHub Release Creation Script
# This script builds the app and creates a GitHub release with distribution files

set -e  # Exit on any error

echo "🚀 Creating GitHub Release for Potter"
echo "===================================="

# Load signing configuration
if [[ -f "$HOME/.potter_signing.env" ]]; then
    echo "🔐 Loading signing configuration..."
    source "$HOME/.potter_signing.env"
    echo "✅ Signing configuration loaded"
else
    echo "⚠️  No signing configuration found at $HOME/.potter_signing.env"
    echo "   Will proceed with adhoc signing"
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "   Install it with: brew install gh"
    echo "   Or visit: https://cli.github.com/"
    exit 1
fi

# Check if we're logged into GitHub CLI
if ! gh auth status &> /dev/null; then
    echo "❌ Not logged into GitHub CLI"
    echo "   Run: gh auth login"
    exit 1
fi

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📂 Project root: $PROJECT_ROOT"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Current branch: $CURRENT_BRANCH"

# Only allow releases from main/master branch
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    echo "❌ Releases can only be created from main/master branch"
    echo "   Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ There are uncommitted changes"
    echo "   Please commit all changes before creating a release"
    exit 1
fi

# Get version information
VERSION=$(git describe --tags --always 2>/dev/null || echo "v1.0.0-dev")
COMMIT_HASH=$(git rev-parse --short HEAD)
BUILD_DATE=$(date '+%Y-%m-%d %H:%M:%S')

# If no tags exist, ask user for version
if [[ "$VERSION" == *"-"* ]] || [[ "$VERSION" == "v1.0.0-dev" ]]; then
    echo "🏷️  No tags found. What version should this be?"
    echo "   Examples: v1.0.0, v1.0.1, v2.0.0-beta"
    read -p "Version: " USER_VERSION
    
    if [[ -z "$USER_VERSION" ]]; then
        echo "❌ Version is required"
        exit 1
    fi
    
    # Ensure version starts with 'v'
    if [[ ! "$USER_VERSION" =~ ^v ]]; then
        USER_VERSION="v$USER_VERSION"
    fi
    
    VERSION="$USER_VERSION"
    
    # Create the tag
    echo "🏷️  Creating tag: $VERSION"
    git tag -a "$VERSION" -m "Release $VERSION"
    

    git push origin "$VERSION"
    echo "✅ Tag pushed to remote"

fi

echo "🏷️  Version: $VERSION"
echo "📅 Build Date: $BUILD_DATE"
echo "🔗 Commit: $COMMIT_HASH"

# Check if Potter directory exists
POTTER_DIR="../Potter"
if [[ ! -d "$POTTER_DIR" ]]; then
    echo "❌ Potter directory not found at $POTTER_DIR"
    echo "   Please ensure the Potter repository exists"
    exit 1
fi

# Check if Potter directory is a git repository
cd "$POTTER_DIR"
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Potter directory is not a git repository"
    exit 1
fi

# Check if release already exists in Potter repo
if gh release view "$VERSION" &> /dev/null; then
    echo "⚠️  Release $VERSION already exists in Potter repository"
    echo "   Do you want to delete it and create a new one? (y/N)"
    read -p "Delete existing release? " DELETE_RELEASE
    
    if [[ "$DELETE_RELEASE" =~ ^[Yy]$ ]]; then
        echo "🗑️  Deleting existing release..."
        gh release delete "$VERSION" --yes
        echo "✅ Existing release deleted"
    else
        echo "❌ Release creation cancelled"
        exit 1
    fi
fi

# Return to project root for building
cd "$PROJECT_ROOT"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Create dist directory structure
mkdir -p dist/app
mkdir -p dist/dmg
mkdir -p dist/archives

# Remove old distribution folder (we'll use dist now)
rm -rf distribution/

# Ensure we're in the virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected, activating..."
    source .venv/bin/activate
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet pyinstaller

# Create build info file
echo "📝 Creating build info..."
cat > build_info.json << EOF
{
    "version": "$VERSION",
    "build_date": "$BUILD_DATE",
    "commit_hash": "$COMMIT_HASH",
    "built_for": "github_release"
}
EOF

# Build the app using the proper build script
echo "🔨 Building Potter app with proper signing..."

# Use the Python build script which handles signing correctly
if python scripts/build_app.py --target github; then
    echo "✅ App built and signed successfully"
else
    echo "❌ Build failed"
    exit 1
fi

# Create installation instructions in dist/archives
echo "📁 Preparing distribution files..."
mkdir -p dist/archives
cat > "dist/archives/INSTALLATION.md" << EOF
# Potter Installation Instructions

## Quick Install from DMG
1. Download \`Potter-$VERSION.dmg\` from the release
2. Double-click the DMG file to open it
3. Drag \`Potter.app\` to the Applications folder in the window
4. Eject the DMG and launch Potter from Applications
5. Right-click the app and select "Open" on first launch
6. Grant accessibility permissions when prompted
7. Look for the Potter icon in your menu bar

## First Launch
1. macOS may show a security warning for unsigned apps
2. Right-click the app and select "Open" to bypass this
3. Grant accessibility permissions in System Settings > Privacy & Security
4. Configure your OpenAI API key in the app settings

## Usage
- **Global Hotkey**: Cmd+Shift+R (configurable)
- **Menu Bar Icon**: Click to access settings and modes
- **Modes**: Rephrase, Summarize, Expand, Casual, Formal

## Troubleshooting
- If the app doesn't start, try removing quarantine: \`xattr -r -d com.apple.quarantine Potter.app\`
- Check Console.app for error messages if needed
- Make sure you have an active internet connection for AI processing

## Requirements
- macOS 10.14 or later
- OpenAI API key (get one at https://platform.openai.com/api-keys)
- Internet connection for AI processing
EOF

# Create DMG installer in dist/dmg
echo "💿 Creating DMG installer..."

DMG_NAME="Potter-$VERSION.dmg"
DMG_TEMP_NAME="temp_$DMG_NAME"
VOLUME_NAME="Potter $VERSION"
DMG_STAGING_DIR="dist/dmg/staging"

# Create staging directory
rm -rf "$DMG_STAGING_DIR"
mkdir -p "$DMG_STAGING_DIR"

# Copy app to staging
cp -R "dist/app/Potter.app" "$DMG_STAGING_DIR/"

# Create Applications symlink
ln -s /Applications "$DMG_STAGING_DIR/Applications"

# Create a simple background (we'll use a solid color for simplicity)
mkdir -p "$DMG_STAGING_DIR/.background"

# Copy the professional background image if available
if [[ -f "$PROJECT_ROOT/assets/dmg_background.png" ]]; then
    cp "$PROJECT_ROOT/assets/dmg_background.png" "$DMG_STAGING_DIR/.background/background.png"
    echo "✅ Using professional DMG background"
else
    # Fallback: Create background image using built-in tools
    echo "⚠️  Professional background not found, creating simple background..."
    cat > "$DMG_STAGING_DIR/.background/create_bg.py" << 'BGEOF'
#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import sys

# Create a 600x400 background image
width, height = 600, 400
img = Image.new('RGB', (width, height), color='#f5f5f5')
draw = ImageDraw.Draw(img)

# Create a subtle gradient
for y in range(height):
    alpha = int(255 * (1 - y / height * 0.1))
    color = (240, 240, 240)
    draw.line([(0, y), (width, y)], fill=color)

# Add some text
try:
    # Try to use a system font
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
except:
    font = ImageFont.load_default()

text = "Drag Potter to Applications to install"
text_bbox = draw.textbbox((0, 0), text, font=font)
text_width = text_bbox[2] - text_bbox[0]
text_x = (width - text_width) // 2
text_y = height - 60

draw.text((text_x, text_y), text, fill='#666666', font=font)

# Add an arrow
arrow_start_x = 180
arrow_start_y = 200
arrow_end_x = 420
arrow_end_y = 200

# Draw arrow line
draw.line([(arrow_start_x, arrow_start_y), (arrow_end_x, arrow_end_y)], fill='#999999', width=3)

# Draw arrowhead
arrow_size = 15
draw.polygon([
    (arrow_end_x, arrow_end_y),
    (arrow_end_x - arrow_size, arrow_end_y - arrow_size//2),
    (arrow_end_x - arrow_size, arrow_end_y + arrow_size//2)
], fill='#999999')

img.save('background.png')
BGEOF

    # Create background using Python (if available) or skip
    cd "$DMG_STAGING_DIR/.background"
    if command -v python3 &> /dev/null && python3 -c "import PIL" 2>/dev/null; then
        python3 create_bg.py
        echo "✅ Created fallback background image"
    else
        # Create a simple solid color background
        echo "⚠️  PIL not available, using minimal background"
        # Create a minimal 600x400 gray background using sips (built into macOS)
        sips -c 600 400 -s format png --out background.png /System/Library/CoreServices/DefaultDesktop.heic 2>/dev/null || \
        echo "Creating minimal background..." > background.txt && mv background.txt background.png
    fi
    rm -f create_bg.py
    cd "$PROJECT_ROOT"
fi

# Calculate the size needed for the DMG
APP_SIZE_MB=$(du -sm "$DMG_STAGING_DIR" | cut -f1)
DMG_SIZE_MB=$((APP_SIZE_MB + 50))  # Add 50MB padding

echo "📏 DMG size: ${DMG_SIZE_MB}MB"

# Create the DMG in dist/dmg
cd "dist/dmg"
hdiutil create -srcfolder "staging" \
               -volname "$VOLUME_NAME" \
               -fs HFS+ \
               -fsargs "-c c=64,a=16,e=16" \
               -format UDRW \
               -size ${DMG_SIZE_MB}m \
               "$DMG_TEMP_NAME"

# Mount the DMG for customization
echo "🔧 Customizing DMG layout..."
DMG_DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "$DMG_TEMP_NAME" | grep '^/dev/' | sed 1q | awk '{print $1}')
MOUNT_POINT="/Volumes/$VOLUME_NAME"

# Wait for mount
sleep 2

# Set up the DMG window appearance using AppleScript
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
        set position of item "Potter.app" of container window to {150, 200}
        
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

# Unmount the DMG
hdiutil detach "$DMG_DEVICE"

# Convert to read-only compressed DMG
echo "🗜️  Compressing DMG..."
hdiutil convert "$DMG_TEMP_NAME" -format UDZO -imagekey zlib-level=9 -o "$DMG_NAME"

# Clean up temporary files
rm -f "$DMG_TEMP_NAME"
rm -rf staging

echo "✅ Created $DMG_NAME in dist/dmg/"

cd "$PROJECT_ROOT"

# Calculate file sizes
APP_SIZE=$(du -sh "dist/app/Potter.app" | cut -f1)
DMG_SIZE=$(du -sh "dist/dmg/$DMG_NAME" | cut -f1)

echo ""
echo "📦 Distribution files ready in dist/:"
echo "   • App bundle: $APP_SIZE (dist/app/Potter.app)"
echo "   • DMG installer: $DMG_SIZE (dist/dmg/$DMG_NAME)"

# Get the repository name for download URLs
REPO_INFO=$(cd "$POTTER_DIR" && gh repo view --json owner,name -q '.owner.login + "/" + .name')

# Generate release notes
RELEASE_NOTES_FILE="release_notes_temp.md"
cat > "$RELEASE_NOTES_FILE" << EOF
# Potter $VERSION

AI-powered text processing for macOS with global hotkey support.

---

# 🔥 **GET POTTER NOW** 🔥

## 📥 **DIRECT DOWNLOAD LINKS** (Click to download immediately)

> ### 🚀 **[⬇️ DOWNLOAD POTTER-$VERSION.DMG](https://github.com/$REPO_INFO/releases/download/$VERSION/Potter-$VERSION.dmg)** 
> **👆 CLICK THE LINK ABOVE TO DOWNLOAD NOW 👆**

### Alternative Download Options:
- **[📦 This Version (Potter-$VERSION.dmg)](https://github.com/$REPO_INFO/releases/download/$VERSION/Potter-$VERSION.dmg)** - Direct link to this release
- **[🔄 Always Latest Version](https://github.com/$REPO_INFO/releases/latest)** - Always redirects to newest release

**Quick Install**: Click link above → DMG downloads → Double-click → Drag to Applications → Done!

---

## 🎯 Features
- **Global Hotkey**: Cmd+Shift+R to process selected text
- **AI Modes**: Rephrase, Summarize, Expand, Casual, Formal
- **Menu Bar App**: Runs quietly in the background
- **Auto-paste**: Automatically replaces selected text
- **OpenAI Integration**: Uses GPT models for text processing

## 📦 Installation
1. Download \`Potter-$VERSION.dmg\`
2. Double-click the DMG file to open it
3. Drag \`Potter.app\` to the Applications folder in the window
4. Eject the DMG and launch Potter from Applications
5. Right-click the app and select "Open" on first launch
6. Configure OpenAI API key in settings

## 🔧 Requirements
- macOS 10.14+
- OpenAI API key
- Internet connection

## 📋 Build Info
- **Version**: $VERSION
- **Build Date**: $BUILD_DATE
- **Commit**: $COMMIT_HASH
- **App Size**: $APP_SIZE
- **DMG Size**: $DMG_SIZE

---

> **📥 Download files are also available in the "Assets" section below, but we recommend using the download link at the top of this page for the easiest experience.**
EOF

# Ask for additional release notes
echo ""
echo "📝 Release Notes Preview:"
echo "========================"
cat "$RELEASE_NOTES_FILE"
echo "========================"
echo ""
echo "Do you want to add any additional release notes? (y/N)"
read -p "Add notes? " ADD_NOTES

if [[ "$ADD_NOTES" =~ ^[Yy]$ ]]; then
    echo "Enter additional notes (end with Ctrl+D):"
    ADDITIONAL_NOTES=$(cat)
    
    # Append additional notes
    echo "" >> "$RELEASE_NOTES_FILE"
    echo "## Additional Notes" >> "$RELEASE_NOTES_FILE"
    echo "$ADDITIONAL_NOTES" >> "$RELEASE_NOTES_FILE"
fi

# Create the GitHub release in Potter repository
echo ""
echo "🚀 Creating GitHub release in Potter repository..."

# Change to Potter directory
cd "$POTTER_DIR"

# Create tag in Potter repo
echo "🏷️  Creating tag $VERSION in Potter repository..."
git tag "$VERSION" 2>/dev/null || echo "   Tag $VERSION already exists"

# Push tag to Potter repo
echo "📤 Pushing tag to Potter repository..."
git push origin "$VERSION" 2>/dev/null || echo "   Tag already pushed or no remote configured"

# Create release in Potter repo
gh release create "$VERSION" \
    "$PROJECT_ROOT/dist/dmg/$DMG_NAME" \
    "$PROJECT_ROOT/dist/archives/INSTALLATION.md" \
    --title "Potter $VERSION" \
    --notes-file "$PROJECT_ROOT/$RELEASE_NOTES_FILE"

if [[ $? -eq 0 ]]; then
    echo "✅ GitHub release created successfully!"
    echo ""
    echo "🔗 Release URL: https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/releases/tag/$VERSION"
    echo ""
    echo "📤 Files uploaded:"
    echo "   • Potter-$VERSION.dmg"
    echo "   • INSTALLATION.md"
    echo ""
    echo "🎉 Users can now download Potter $VERSION from GitHub Releases!"
else
    echo "❌ Failed to create GitHub release"
    exit 1
fi

# Return to project root
cd "$PROJECT_ROOT"

# Clean up
rm -f "$RELEASE_NOTES_FILE"
rm -f build_info.json

echo "✨ GitHub release creation complete!"

echo ""
echo "🎉 Potter release completed!" 
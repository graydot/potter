#!/bin/bash

# Rephrasely GitHub Release Creation Script
# This script builds the app and creates a GitHub release with distribution files

set -e  # Exit on any error

echo "🚀 Creating GitHub Release for Rephrasely"
echo "========================================="

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
    
    # Ask if user wants to push the tag
    echo "📤 Do you want to push the tag to remote? (y/N)"
    read -p "Push tag? " PUSH_TAG
    if [[ "$PUSH_TAG" =~ ^[Yy]$ ]]; then
        git push origin "$VERSION"
        echo "✅ Tag pushed to remote"
    fi
fi

echo "🏷️  Version: $VERSION"
echo "📅 Build Date: $BUILD_DATE"
echo "🔗 Commit: $COMMIT_HASH"

# Check if release already exists
if gh release view "$VERSION" &> /dev/null; then
    echo "⚠️  Release $VERSION already exists"
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

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/
rm -rf distribution/

# Create distribution directory
mkdir -p distribution

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

# Build the app with PyInstaller
echo "🔨 Building app with PyInstaller..."

# Check if icon exists, use it if available
ICON_PARAM=""
if [[ -f "assets/icon.icns" ]]; then
    ICON_PARAM="--icon=assets/icon.icns"
    echo "📱 Using app icon: assets/icon.icns"
else
    echo "⚠️  No icon file found, building without custom icon"
fi

python -m PyInstaller \
    --name="Rephrasely" \
    --windowed \
    --onedir \
    $ICON_PARAM \
    --add-data="build_info.json:." \
    --hidden-import="objc" \
    --hidden-import="Foundation" \
    --hidden-import="AppKit" \
    --hidden-import="UserNotifications" \
    --hidden-import="ApplicationServices" \
    --hidden-import="Quartz" \
    --clean \
    rephrasely.py

# Verify the app was built
if [[ ! -d "dist/Rephrasely.app" ]]; then
    echo "❌ Build failed: App not found in dist/"
    exit 1
fi

echo "✅ App built successfully"

# Fix app bundle configuration
echo "🔧 Configuring app bundle..."

# Update Info.plist with proper settings
/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $VERSION" "dist/Rephrasely.app/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "dist/Rephrasely.app/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $VERSION" "dist/Rephrasely.app/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "dist/Rephrasely.app/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "dist/Rephrasely.app/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :LSUIElement true" "dist/Rephrasely.app/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Add :LSBackgroundOnly bool false" "dist/Rephrasely.app/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :LSBackgroundOnly false" "dist/Rephrasely.app/Contents/Info.plist"

# Add usage descriptions
/usr/libexec/PlistBuddy -c "Add :NSAppleEventsUsageDescription string 'Rephrasely needs to send AppleEvents to paste processed text and manage login items.'" "dist/Rephrasely.app/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :NSAppleEventsUsageDescription 'Rephrasely needs to send AppleEvents to paste processed text and manage login items.'" "dist/Rephrasely.app/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Add :NSSystemAdministrationUsageDescription string 'Rephrasely needs system administration access to manage startup settings.'" "dist/Rephrasely.app/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Set :NSSystemAdministrationUsageDescription 'Rephrasely needs system administration access to manage startup settings.'" "dist/Rephrasely.app/Contents/Info.plist"

# Set executable permissions
chmod +x "dist/Rephrasely.app/Contents/MacOS/Rephrasely"

echo "✅ App bundle configured"

# Code signing
echo "🔐 Code signing..."
codesign --force --deep --sign - "dist/Rephrasely.app"
echo "✅ App signed with adhoc signature"

# Copy to distribution folder
echo "📁 Preparing distribution files..."
cp -R "dist/Rephrasely.app" "distribution/"

# Create installation instructions
cat > "distribution/INSTALLATION.md" << EOF
# Rephrasely Installation Instructions

## Quick Install
1. Download \`Rephrasely.app.zip\` from the release
2. Extract the ZIP file by double-clicking it
3. Drag \`Rephrasely.app\` to your Applications folder
4. Right-click the app and select "Open" on first launch
5. Grant accessibility permissions when prompted
6. Look for the Rephrasely icon in your menu bar

## Alternative Downloads
- **Rephrasely.app.zip** (Recommended) - Compressed app bundle
- **Rephrasely.app.tar.gz** - Alternative compression format

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
- If the app doesn't start, try removing quarantine: \`xattr -r -d com.apple.quarantine Rephrasely.app\`
- Check Console.app for error messages if needed
- Make sure you have an active internet connection for AI processing

## Requirements
- macOS 10.14 or later
- OpenAI API key (get one at https://platform.openai.com/api-keys)
- Internet connection for AI processing
EOF

# Create ZIP and tar.gz archives
echo "🗜️  Creating distribution archives..."
cd distribution

# Create ZIP
zip -r "Rephrasely.app.zip" "Rephrasely.app"
echo "✅ Created Rephrasely.app.zip"

# Create tar.gz (preserves permissions better)
tar -czf "Rephrasely.app.tar.gz" "Rephrasely.app"
echo "✅ Created Rephrasely.app.tar.gz"

cd "$PROJECT_ROOT"

# Calculate file sizes
APP_SIZE=$(du -sh "distribution/Rephrasely.app" | cut -f1)
ZIP_SIZE=$(du -sh "distribution/Rephrasely.app.zip" | cut -f1)
TAR_SIZE=$(du -sh "distribution/Rephrasely.app.tar.gz" | cut -f1)

echo ""
echo "📦 Distribution files ready:"
echo "   • App bundle: $APP_SIZE"
echo "   • ZIP archive: $ZIP_SIZE"
echo "   • TAR archive: $TAR_SIZE"

# Generate release notes
RELEASE_NOTES_FILE="release_notes_temp.md"
cat > "$RELEASE_NOTES_FILE" << EOF
# Rephrasely $VERSION

AI-powered text processing for macOS with global hotkey support.

## 🎯 Features
- **Global Hotkey**: Cmd+Shift+R to process selected text
- **AI Modes**: Rephrase, Summarize, Expand, Casual, Formal
- **Menu Bar App**: Runs quietly in the background
- **Auto-paste**: Automatically replaces selected text
- **OpenAI Integration**: Uses GPT models for text processing

## 📦 Installation
1. Download \`Rephrasely.app.zip\`
2. Extract and drag to Applications folder
3. Right-click and "Open" on first launch
4. Configure OpenAI API key in settings

## 🔧 Requirements
- macOS 10.14+
- OpenAI API key
- Internet connection

## 📋 Build Info
- **Version**: $VERSION
- **Build Date**: $BUILD_DATE
- **Commit**: $COMMIT_HASH
- **App Size**: $APP_SIZE
- **ZIP Size**: $ZIP_SIZE

## 📥 Download Options
- **Rephrasely.app.zip** (Recommended) - Standard ZIP archive
- **Rephrasely.app.tar.gz** - Alternative compression format

Choose the ZIP file for easiest installation on most systems.
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

# Create the GitHub release
echo ""
echo "🚀 Creating GitHub release..."

gh release create "$VERSION" \
    "distribution/Rephrasely.app.zip" \
    "distribution/Rephrasely.app.tar.gz" \
    "distribution/INSTALLATION.md" \
    --title "Rephrasely $VERSION" \
    --notes-file "$RELEASE_NOTES_FILE" \
    --discussion-category "Releases"

if [[ $? -eq 0 ]]; then
    echo "✅ GitHub release created successfully!"
    echo ""
    echo "🔗 Release URL: https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/releases/tag/$VERSION"
    echo ""
    echo "📤 Files uploaded:"
    echo "   • Rephrasely.app.zip ($ZIP_SIZE)"
    echo "   • Rephrasely.app.tar.gz ($TAR_SIZE)"
    echo "   • INSTALLATION.md"
    echo ""
    echo "🎉 Users can now download Rephrasely $VERSION from GitHub Releases!"
else
    echo "❌ Failed to create GitHub release"
    exit 1
fi

# Clean up
rm -f "$RELEASE_NOTES_FILE"
rm -f build_info.json

echo "✨ GitHub release creation complete!" 
#!/bin/bash

# Rephrasely Distribution Build Script
# This script builds the macOS app and prepares it for distribution

set -e  # Exit on any error

echo "🚀 Building Rephrasely for Distribution"
echo "======================================"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📂 Project root: $PROJECT_ROOT"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/
rm -rf distribution/Rephrasely.app*

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

# Get version from git or use default
VERSION=$(git describe --tags --always 2>/dev/null || echo "v1.0.0")
BUILD_DATE=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "🏷️  Version: $VERSION"
echo "📅 Build Date: $BUILD_DATE"
echo "🔗 Commit: $COMMIT_HASH"

# Create build info file
echo "📝 Creating build info..."
cat > build_info.json << EOF
{
    "version": "$VERSION",
    "build_date": "$BUILD_DATE",
    "commit_hash": "$COMMIT_HASH",
    "built_for": "distribution"
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

# Update Info.plist with proper settings - Add entries if they don't exist
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

# Code signing (if certificates are available)
echo "🔐 Checking for code signing..."
if security find-identity -v -p codesigning | grep -q "Developer ID"; then
    echo "📝 Code signing certificate found, signing app..."
    codesign --force --deep --sign "Developer ID Application" "dist/Rephrasely.app"
    echo "✅ App signed successfully"
else
    echo "⚠️  No code signing certificate found - app will not be signed"
    echo "   Users may need to right-click and select 'Open' on first launch"
fi

# Copy to distribution folder
echo "📁 Copying to distribution folder..."
cp -R "dist/Rephrasely.app" "distribution/"

# Create ZIP for distribution (optional)
echo "🗜️  Creating ZIP archive..."
cd distribution
zip -r "Rephrasely.app.zip" "Rephrasely.app"

# Create tar.gz for GitHub releases (preserves permissions better)
echo "📦 Creating tar.gz archive for GitHub..."
tar -czf "Rephrasely.app.tar.gz" "Rephrasely.app"
cd "$PROJECT_ROOT"

# Calculate file sizes
APP_SIZE=$(du -sh "distribution/Rephrasely.app" | cut -f1)
ZIP_SIZE=$(du -sh "distribution/Rephrasely.app.zip" | cut -f1)
TAR_SIZE=$(du -sh "distribution/Rephrasely.app.tar.gz" | cut -f1)

echo ""
echo "🎉 Build Complete!"
echo "=================="
echo "📱 App Size: $APP_SIZE"
echo "📦 ZIP Size: $ZIP_SIZE"
echo "📦 TAR Size: $TAR_SIZE"
echo "📍 App Location: distribution/Rephrasely.app"
echo "📍 ZIP Location: distribution/Rephrasely.app.zip"
echo "📍 TAR Location: distribution/Rephrasely.app.tar.gz"
echo ""
echo "🔗 Distribution Options:"
echo "   • Direct .app: More convenient for users"
echo "   • ZIP file: Better compatibility and smaller download"
echo "   • TAR file: Better compatibility and smaller download"
echo "   • Both: Let users choose their preference"

# Update distribution README with build info
cat > distribution/BUILD_INFO.md << EOF
# Build Information

- **Version**: $VERSION
- **Build Date**: $BUILD_DATE
- **Commit Hash**: $COMMIT_HASH
- **App Size**: $APP_SIZE
- **ZIP Size**: $ZIP_SIZE
- **TAR Size**: $TAR_SIZE

## Distribution Files

- \`Rephrasely.app\` - Direct macOS application (drag to /Applications)
- \`Rephrasely.app.zip\` - Compressed version (extract then drag to /Applications)
- \`Rephrasely.app.tar.gz\` - Compressed version (extract then drag to /Applications)

## Installation Options

### Option 1: Direct .app (Recommended)
1. Download \`Rephrasely.app\`
2. Drag directly to /Applications folder
3. Right-click and select "Open" on first launch (if unsigned)

### Option 2: ZIP Download
1. Download \`Rephrasely.app.zip\`
2. Extract the ZIP file
3. Drag \`Rephrasely.app\` to /Applications
4. Right-click and select "Open" on first launch (if unsigned)

### Option 3: TAR Download
1. Download \`Rephrasely.app.tar.gz\`
2. Extract the TAR file
3. Drag \`Rephrasely.app\` to /Applications
4. Right-click and select "Open" on first launch (if unsigned)

EOF

echo "📋 Build info saved to distribution/BUILD_INFO.md"

# Clean up temporary files
rm -f build_info.json

echo "✨ Distribution build complete!" 
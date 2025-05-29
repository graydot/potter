#!/bin/bash

# Potter Mac App Store Build Script
# Builds app for App Store submission with proper signing and packaging

set -e  # Exit on any error

echo "🍎 Building Potter for Mac App Store"
echo "===================================="

# Check if we're in the correct directory
if [[ ! -f "Potter-AppStore.spec" ]]; then
    echo "❌ Potter-AppStore.spec not found. Please run from project root."
    exit 1
fi

# Load App Store signing configuration
if [[ -f "$HOME/.potter_appstore_signing.env" ]]; then
    echo "🔐 Loading App Store signing configuration..."
    source "$HOME/.potter_appstore_signing.env"
    echo "✅ App Store signing configuration loaded"
else
    echo "❌ No App Store signing configuration found at $HOME/.potter_appstore_signing.env"
    echo ""
    echo "Create this file with:"
    echo "export APPSTORE_APP_CERT='3rd Party Mac Developer Application: Your Name (TEAMID)'"
    echo "export APPSTORE_INSTALLER_CERT='3rd Party Mac Developer Installer: Your Name (TEAMID)'"
    echo "export APPLE_ID_EMAIL='your-apple-id@example.com'"
    echo "export APPLE_ID_PASSWORD='app-specific-password'"
    echo "export TEAM_ID='YOUR_TEAM_ID'"
    exit 1
fi

# Verify certificates exist
echo "🔍 Checking for required certificates..."
if ! security find-identity -v -p codesigning | grep -q "$APPSTORE_APP_CERT"; then
    echo "❌ App signing certificate not found: $APPSTORE_APP_CERT"
    echo "   Please install Mac App Store certificates from Apple Developer portal"
    exit 1
fi

if ! security find-identity -v -p codesigning | grep -q "$APPSTORE_INSTALLER_CERT"; then
    echo "❌ Installer signing certificate not found: $APPSTORE_INSTALLER_CERT"
    echo "   Please install Mac App Store certificates from Apple Developer portal"
    exit 1
fi

echo "✅ Required certificates found"

# Ensure we're in the virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected, activating..."
    source .venv/bin/activate
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet pyinstaller

# Get version information
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
    "built_for": "mac_app_store"
}
EOF

# Build with PyInstaller
echo "🔨 Building with PyInstaller..."
pyinstaller Potter-AppStore.spec --clean --noconfirm

# Verify the app bundle was created
if [[ ! -d "dist/Potter.app" ]]; then
    echo "❌ App bundle not created"
    exit 1
fi

echo "✅ App bundle created: dist/Potter.app"

# Code sign the app
echo "✍️  Code signing app..."
codesign --force --sign "$APPSTORE_APP_CERT" \
         --entitlements entitlements-appstore.plist \
         --options runtime \
         --timestamp \
         --deep \
         dist/Potter.app

# Verify code signature
echo "🔍 Verifying code signature..."
codesign --verify --verbose=2 dist/Potter.app
spctl --assess --verbose=2 --type execute dist/Potter.app

# Create installer package
echo "📦 Creating installer package..."
productbuild --component dist/Potter.app /Applications \
             --sign "$APPSTORE_INSTALLER_CERT" \
             --product dist/Potter.app/Contents/Info.plist \
             dist/Potter.pkg

# Verify installer signature
echo "🔍 Verifying installer signature..."
pkgutil --check-signature dist/Potter.pkg

# Calculate sizes
APP_SIZE=$(du -sh "dist/Potter.app" | cut -f1)
PKG_SIZE=$(du -sh "dist/Potter.pkg" | cut -f1)

echo ""
echo "✅ Mac App Store build complete!"
echo "📦 App bundle: $APP_SIZE (dist/Potter.app)"
echo "📦 Installer: $PKG_SIZE (dist/Potter.pkg)"
echo ""
echo "🚀 Next steps:"
echo "   1. Test the app thoroughly"
echo "   2. Upload to App Store Connect using Transporter or:"
echo "      xcrun altool --upload-app --type osx --file dist/Potter.pkg \\"
echo "                   --username '$APPLE_ID_EMAIL' \\"
echo "                   --password '$APPLE_ID_PASSWORD' \\"
echo "                   --asc-provider '$TEAM_ID'"
echo ""
echo "   3. Submit for review in App Store Connect"

# Clean up
rm -f build_info.json 
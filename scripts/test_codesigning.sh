#!/bin/bash
# Code Signing Test Script
# Tests code signing setup and certificate availability

echo "🔐 Code Signing Test"
echo "===================="

# Test if signing certificates are available
echo "🔍 Checking available certificates..."

# List all code signing certificates
CERTS=$(security find-identity -v -p codesigning 2>/dev/null)

if [ -z "$CERTS" ]; then
    echo "❌ No code signing certificates found in keychain"
    echo ""
    echo "💡 To set up code signing:"
    echo "1. Get Apple Developer Account ($99/year)"
    echo "2. Create certificates in Apple Developer Portal"
    echo "3. Download and install certificates"
    echo "4. See docs/CODE_SIGNING_SETUP.md for details"
    exit 1
fi

echo "✅ Found certificates:"
echo "$CERTS"
echo ""

# Check for specific certificate types
DEVELOPER_ID=$(echo "$CERTS" | grep "Developer ID Application" | head -1)
MAC_APP_STORE=$(echo "$CERTS" | grep "3rd Party Mac Developer Application" | head -1)

echo "📋 Certificate Status:"
if [ ! -z "$DEVELOPER_ID" ]; then
    echo "✅ Developer ID Application (for GitHub releases): Found"
    DEVELOPER_ID_NAME=$(echo "$DEVELOPER_ID" | sed 's/.*"\(.*\)".*/\1/')
    echo "   $DEVELOPER_ID_NAME"
else
    echo "❌ Developer ID Application: Not found"
fi

if [ ! -z "$MAC_APP_STORE" ]; then
    echo "✅ Mac App Store Application (for App Store): Found"
    MAC_APP_STORE_NAME=$(echo "$MAC_APP_STORE" | sed 's/.*"\(.*\)".*/\1/')
    echo "   $MAC_APP_STORE_NAME"
else
    echo "❌ Mac App Store Application: Not found"
fi

echo ""

# Test environment variables
echo "🔧 Checking environment variables..."

# Check for GitHub release signing variables
if [ ! -z "$DEVELOPER_ID_APPLICATION" ] && [ ! -z "$APPLE_TEAM_ID" ]; then
    echo "✅ GitHub release variables configured"
    echo "   DEVELOPER_ID_APPLICATION: $DEVELOPER_ID_APPLICATION"
    echo "   APPLE_TEAM_ID: $APPLE_TEAM_ID"
else
    echo "⚠️  GitHub release variables not configured"
    echo "   Set: DEVELOPER_ID_APPLICATION, APPLE_TEAM_ID"
fi

# Check for notarization variables
if [ ! -z "$APPLE_ID" ] && [ ! -z "$APPLE_APP_PASSWORD" ]; then
    echo "✅ Notarization variables configured"
    echo "   APPLE_ID: $APPLE_ID"
    echo "   APPLE_APP_PASSWORD: [hidden]"
else
    echo "⚠️  Notarization variables not configured (optional)"
    echo "   Set: APPLE_ID, APPLE_APP_PASSWORD"
fi

# Check for App Store variables
if [ ! -z "$MAC_APP_STORE_CERTIFICATE" ] && [ ! -z "$APPLE_TEAM_ID" ]; then
    echo "✅ App Store variables configured"
    echo "   MAC_APP_STORE_CERTIFICATE: $MAC_APP_STORE_CERTIFICATE"
else
    echo "⚠️  App Store variables not configured"
    echo "   Set: MAC_APP_STORE_CERTIFICATE, MAC_INSTALLER_CERTIFICATE"
fi

echo ""

# Test if we can build with signing
echo "🧪 Testing build with code signing..."

if [ ! -z "$DEVELOPER_ID" ]; then
    echo "🔨 Testing GitHub release build..."
    if python scripts/build_app.py --target github --skip-notarization; then
        echo "✅ GitHub release build successful"
        
        # Check if app was actually signed
        if codesign --verify --deep --strict dist/app/Rephrasely.app 2>/dev/null; then
            echo "✅ App is properly signed"
            
            # Get signing details
            SIGNING_INFO=$(codesign -dv dist/app/Rephrasely.app 2>&1)
            echo "📝 Signing details:"
            echo "$SIGNING_INFO" | grep "Authority="
            echo "$SIGNING_INFO" | grep "TeamIdentifier="
            
        else
            echo "❌ App was built but not signed"
        fi
    else
        echo "❌ GitHub release build failed"
    fi
else
    echo "⚠️  Skipping GitHub build test - no Developer ID certificate"
fi

echo ""

if [ ! -z "$MAC_APP_STORE" ]; then
    echo "🏪 Testing App Store build..."
    if python scripts/build_app.py --target appstore; then
        echo "✅ App Store build successful"
    else
        echo "❌ App Store build failed"
    fi
else
    echo "⚠️  Skipping App Store build test - no Mac App Store certificate"
fi

echo ""
echo "🎯 Summary:"
echo "==========="

if [ ! -z "$DEVELOPER_ID" ]; then
    echo "✅ Ready for GitHub releases (signed DMGs)"
else
    echo "❌ Not ready for GitHub releases (need Developer ID certificate)"
fi

if [ ! -z "$MAC_APP_STORE" ]; then
    echo "✅ Ready for App Store distribution"
else
    echo "❌ Not ready for App Store (need Mac App Store certificate)"
fi

if [ ! -z "$APPLE_ID" ] && [ ! -z "$APPLE_APP_PASSWORD" ]; then
    echo "✅ Ready for notarization"
else
    echo "⚠️  Notarization not configured (recommended for GitHub releases)"
fi

echo ""
echo "📚 Resources:"
echo "• docs/CODE_SIGNING_SETUP.md - Complete setup guide"
echo "• Apple Developer Portal - Create certificates"
echo "• Keychain Access - Manage certificates" 
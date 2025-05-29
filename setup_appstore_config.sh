#!/bin/bash

# Setup App Store Configuration for Potter
echo "🍎 Setting up App Store configuration for Potter..."

CONFIG_FILE="$HOME/.potter_appstore_signing.env"

echo ""
echo "Please provide the following information:"
echo ""

# Get Apple ID email
read -p "Apple ID Email: " APPLE_ID_EMAIL

# Get App-Specific Password
echo ""
echo "App-Specific Password (create at appleid.apple.com):"
read -s APPLE_ID_PASSWORD
echo ""

# Get Team ID
read -p "Team ID (from Apple Developer portal): " TEAM_ID

# Get certificate names (these should match what's installed)
echo ""
echo "Certificate names (exactly as they appear in Keychain):"
read -p "3rd Party Mac Developer Application cert: " APPSTORE_APP_CERT
read -p "3rd Party Mac Developer Installer cert: " APPSTORE_INSTALLER_CERT

# Create the configuration file
cat > "$CONFIG_FILE" << EOF
# Potter App Store Signing Configuration
export APPSTORE_APP_CERT="$APPSTORE_APP_CERT"
export APPSTORE_INSTALLER_CERT="$APPSTORE_INSTALLER_CERT"
export APPLE_ID_EMAIL="$APPLE_ID_EMAIL"
export APPLE_ID_PASSWORD="$APPLE_ID_PASSWORD"
export TEAM_ID="$TEAM_ID"
EOF

# Set secure permissions
chmod 600 "$CONFIG_FILE"

echo ""
echo "✅ Configuration saved to: $CONFIG_FILE"
echo ""
echo "🚀 You can now run: ./scripts/build_appstore.sh" 
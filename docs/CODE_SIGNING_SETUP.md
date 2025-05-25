# 🔐 Code Signing Setup Guide

This guide covers setting up code signing for Rephrasely to distribute signed DMGs and publish to the App Store.

## 📋 Prerequisites

### Apple Developer Account Requirements
- **Paid Apple Developer Account** ($99/year)
- **Team ID** (found in your Apple Developer account)
- **Certificates** (created in Apple Developer portal)
- **App Store Connect Access** (for App Store distribution)

## 🏠 Local Development Setup

### Step 1: Create Certificates in Apple Developer Portal

1. **Login to [Apple Developer Portal](https://developer.apple.com)**
2. **Go to Certificates, Identifiers & Profiles**
3. **Create the following certificates:**

#### For GitHub Releases (DMG Distribution):
- **Developer ID Application**
  - Used to sign the app for distribution outside App Store
  - Download and install in macOS Keychain
- **Developer ID Installer** (optional)
  - Used to sign installer packages
  - Download and install in macOS Keychain

#### For App Store Distribution:
- **Mac App Store**
  - Used to sign apps for App Store submission
  - Download and install in macOS Keychain
- **Mac Installer Distribution**
  - Used to sign packages for App Store submission
  - Download and install in macOS Keychain

### Step 2: Install Certificates

1. **Download certificates** from Apple Developer Portal
2. **Double-click each .cer file** to install in Keychain Access
3. **Verify installation** in Keychain Access under "My Certificates"

### Step 3: Configure Local Environment

Create a script to set environment variables:

```bash
# Create ~/.rephrasely_signing.env
cat > ~/.rephrasely_signing.env << 'EOF'
# Apple Developer Configuration
export APPLE_TEAM_ID="YOUR_TEAM_ID"

# GitHub Release Signing (Developer ID certificates)
export DEVELOPER_ID_APPLICATION="Developer ID Application: Your Name (TEAM_ID)"
export DEVELOPER_ID_INSTALLER="Developer ID Installer: Your Name (TEAM_ID)"

# App Store Signing (Mac App Store certificates)
export MAC_APP_STORE_CERTIFICATE="3rd Party Mac Developer Application: Your Name (TEAM_ID)"
export MAC_INSTALLER_CERTIFICATE="3rd Party Mac Developer Installer: Your Name (TEAM_ID)"

# Notarization (for GitHub releases)
export APPLE_ID="your@apple.id"
export APPLE_APP_PASSWORD="app-specific-password"  # See setup below
export ASC_PROVIDER="TEAM_ID"  # Only if you're on multiple teams

# App Store Connect API (preferred for automation)
export ASC_API_KEY_ID="ABCD123456"
export ASC_API_ISSUER_ID="12345678-1234-1234-1234-123456789012"
export ASC_API_KEY_PATH="$HOME/.appstoreconnect/private_keys/AuthKey_ABCD123456.p8"
EOF

# Load environment (add to your shell profile)
source ~/.rephrasely_signing.env
```

### Step 4: Setup App-Specific Password (for Notarization)

1. **Go to [appleid.apple.com](https://appleid.apple.com)**
2. **Sign in with your Apple ID**
3. **In Security section, click "Generate Password"**
4. **Label**: "Rephrasely Notarization"
5. **Copy the generated password** (format: abcd-efgh-ijkl-mnop)
6. **Add to environment**: `export APPLE_APP_PASSWORD="abcd-efgh-ijkl-mnop"`

### Step 5: Setup App Store Connect API (Recommended)

1. **Go to [App Store Connect](https://appstoreconnect.apple.com)**
2. **Users and Access → Keys**
3. **Generate API Key**:
   - **Name**: "Rephrasely CI/CD"
   - **Access**: "App Manager" 
   - **Download the key file** (AuthKey_KEYID.p8)
4. **Store securely**:
   ```bash
   mkdir -p ~/.appstoreconnect/private_keys/
   mv ~/Downloads/AuthKey_KEYID.p8 ~/.appstoreconnect/private_keys/
   chmod 600 ~/.appstoreconnect/private_keys/AuthKey_KEYID.p8
   ```

## 🏗️ Building Locally

### GitHub Release Build (Signed DMG)
```bash
# Load signing environment
source ~/.rephrasely_signing.env

# Build signed app with notarization
python scripts/build_app.py --target github

# Create signed DMG
./scripts/test_dmg_creation.sh
```

### App Store Build
```bash
# Load signing environment
source ~/.rephrasely_signing.env

# Build and upload to App Store
python scripts/build_app.py --target appstore
```

### Development Build (No Signing)
```bash
# Quick development build
python scripts/build_app.py --skip-signing
```

## 🤖 GitHub Actions Setup

### Step 1: Export Certificates

Export certificates from Keychain Access as .p12 files:

```bash
# Export Developer ID Application certificate
security find-identity -v -p codesigning
# Note the hash/name of your Developer ID Application certificate

# Export as .p12 (you'll be prompted for password)
security export -k login.keychain -t identities -f pkcs12 \
  -o developer_id_application.p12 \
  "CERTIFICATE_HASH_OR_NAME"

# Export other certificates similarly
security export -k login.keychain -t identities -f pkcs12 \
  -o mac_app_store.p12 \
  "MAC_APP_STORE_CERTIFICATE_HASH"
```

### Step 2: Encode Certificates to Base64

```bash
# Encode certificates to base64 for GitHub Secrets
base64 -i developer_id_application.p12 -o developer_id_application.p12.txt
base64 -i mac_app_store.p12 -o mac_app_store.p12.txt
```

### Step 3: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and Variables → Actions

#### Required Secrets:

**For GitHub Releases:**
```
DEVELOPER_ID_APPLICATION_P12    # Base64 encoded .p12 file
DEVELOPER_ID_INSTALLER_P12      # Base64 encoded .p12 file (optional)
CERTIFICATES_PASSWORD           # Password used when exporting .p12 files
DEVELOPER_ID_NAME              # "Your Name (TEAM_ID)" without "Developer ID Application:"
APPLE_TEAM_ID                  # Your 10-character team ID
```

**For Notarization (Optional but Recommended):**
```
APPLE_ID                       # Your Apple ID email
APPLE_APP_PASSWORD             # App-specific password from appleid.apple.com
ASC_PROVIDER                   # Your team ID (if multiple teams)
```

**For App Store Distribution:**
```
MAC_APP_STORE_P12             # Base64 encoded Mac App Store certificate
MAC_INSTALLER_P12             # Base64 encoded Mac Installer certificate
MAC_APP_STORE_NAME            # "Your Name (TEAM_ID)" without certificate prefix
MAC_INSTALLER_NAME            # "Your Name (TEAM_ID)" without certificate prefix
```

**For App Store Connect API (Recommended):**
```
ASC_API_KEY_ID                # API Key ID from App Store Connect
ASC_API_ISSUER_ID             # Issuer ID from App Store Connect
ASC_API_KEY_CONTENT           # Contents of AuthKey_KEYID.p8 file
```

#### Example Secret Values:
```
DEVELOPER_ID_NAME="John Doe (ABC123DEF4)"
APPLE_TEAM_ID="ABC123DEF4"
MAC_APP_STORE_NAME="John Doe (ABC123DEF4)"
ASC_API_KEY_ID="ABCD123456"
ASC_API_ISSUER_ID="12345678-1234-1234-1234-123456789012"
```

## 🚀 Using the GitHub Actions Workflow

### Automatic Releases (Tag-based)
```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will automatically:
# 1. Build signed app
# 2. Create notarized DMG
# 3. Create GitHub release
# 4. Upload DMG as release asset
```

### Manual Releases
1. **Go to GitHub → Actions**
2. **Select "Build and Release" workflow**
3. **Click "Run workflow"**
4. **Choose:**
   - **Version**: e.g., "v1.0.1"
   - **Target**: "github", "appstore", or "both"
5. **Click "Run workflow"**

### What Happens:
- **GitHub Target**: Creates signed DMG and GitHub release
- **App Store Target**: Builds and uploads to App Store Connect
- **Both**: Does both in parallel

## 🔍 Troubleshooting

### Common Issues:

#### Certificate Not Found
```bash
# List available certificates
security find-identity -v -p codesigning

# Make sure certificate names match exactly
# Use the full name from the security command output
```

#### Keychain Access Denied
```bash
# Unlock keychain
security unlock-keychain ~/Library/Keychains/login.keychain-db

# Set keychain settings
security set-keychain-settings -t 7200 -l ~/Library/Keychains/login.keychain-db
```

#### Notarization Failed
- Check Apple ID and app password are correct
- Ensure app is properly signed with Developer ID
- Check Apple Developer Portal for notarization status

#### GitHub Actions Certificate Import Failed
- Verify base64 encoding is correct
- Check certificate password matches
- Ensure certificates are valid and not expired

### Verification Commands:

```bash
# Verify app signature
codesign --verify --deep --strict --verbose=2 dist/app/Rephrasely.app

# Check Gatekeeper assessment
spctl --assess --type execute --verbose dist/app/Rephrasely.app

# Verify notarization (after notarization)
spctl --assess --type execute --verbose dist/app/Rephrasely.app
stapler validate dist/app/Rephrasely.app
```

## 📚 Additional Resources

- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [App Store Connect Help](https://help.apple.com/app-store-connect/)
- [Notarization Requirements](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution/resolving_common_notarization_issues)

## 🔒 Security Best Practices

1. **Never commit certificates or private keys to git**
2. **Use environment variables for sensitive data**
3. **Rotate App Store Connect API keys regularly**
4. **Use different certificates for development vs production**
5. **Keep certificates in secure keychain with passwords**
6. **Monitor certificate expiration dates**
7. **Use App Store Connect API instead of Apple ID when possible** 
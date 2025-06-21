# Auto-Update Setup Guide

This guide explains how to set up and use Potter's auto-update system with Sparkle framework.

## 🏗️ Architecture Overview

Potter uses the **Sparkle framework** for automatic updates, which provides:
- Secure, code-signed update verification
- User-friendly update prompts
- Background update checking
- Automatic installation

### Components

1. **AutoUpdateManager.swift** - Manages Sparkle integration
2. **appcast.xml** - Update manifest hosted on GitHub
3. **Release Manager** - Automated release process
4. **Settings UI** - User controls for update preferences

## 🚀 Quick Start

### For Development

1. **Build with auto-updates**:
   ```bash
   make build
   ```

2. **Create a new release**:
   ```bash
   make release
   ```

3. **Test updates**:
   - Check "Updates" tab in Potter settings
   - Use "Check for Updates" menu item

### For Production

1. **Set up GitHub repository**
2. **Configure code signing** (see CODE_SIGNING_SETUP.md)
3. **Create first release** with `make release`
4. **Host appcast.xml** on GitHub releases

## 📋 Release Process

### Automated Release (Recommended)

```bash
# Create new patch release (2.0.0 → 2.0.1)
make release

# Create minor release (2.0.0 → 2.1.0)
python3 scripts/release_manager.py --bump minor

# Create major release (2.0.0 → 3.0.0)
python3 scripts/release_manager.py --bump major

# Create specific version
python3 scripts/release_manager.py --version 2.5.0
```

### Manual Release Steps

If you prefer manual control:

```bash
# 1. Update version in files
# Edit scripts/build_app.py: change CFBundleShortVersionString

# 2. Build the app
make build

# 3. Update appcast.xml
python3 scripts/release_manager.py --skip-github --notes "Your release notes"

# 4. Create GitHub release manually
gh release create v2.0.1 dist/Potter-2.0.1.dmg --title "Potter 2.0.1" --notes "Release notes"

# 5. Commit changes
git add scripts/build_app.py releases/appcast.xml
git commit -m "Release 2.0.1"
git push && git push --tags
```

## ⚙️ Configuration

### Update Feed URL

The update feed is configured in `AutoUpdateManager.swift`:

```swift
private let feedURL = "https://raw.githubusercontent.com/jebasingh/potter/main/releases/appcast.xml"
```

### Update Frequency

Default check interval is 24 hours. Modify in `AutoUpdateManager.swift`:

```swift
private let updateCheckInterval: TimeInterval = 60 * 60 * 24 // 24 hours
```

### User Preferences

Users can control updates via:
- **Settings → Updates tab**: Toggle auto-check, view version info
- **Menu Bar → Check for Updates**: Manual update check

## 🔒 Security

### Code Signing Requirements

Auto-updates require proper code signing:

```bash
# Set environment variables
export DEVELOPER_ID_APPLICATION="Developer ID Application: Your Name (TEAM_ID)"
export APPLE_TEAM_ID="YOUR_TEAM_ID"

# For notarization (recommended)
export APPLE_ID="your@apple.id"
export APPLE_APP_PASSWORD="app-specific-password"
```

### Signature Verification

Sparkle automatically verifies:
- ✅ Code signature validity
- ✅ Certificate chain trust
- ✅ DMG integrity
- ✅ Update authenticity

## 🌐 Hosting Setup

### GitHub Pages (Recommended)

1. **Enable GitHub Pages** for your repository
2. **Appcast URL**: `https://username.github.io/repository/releases/appcast.xml`
3. **Update feed URL** in `AutoUpdateManager.swift`

### Raw GitHub (Alternative)

1. **Appcast URL**: `https://raw.githubusercontent.com/username/repository/main/releases/appcast.xml`
2. **Ensure main branch** contains latest appcast

### Custom Server

1. **Host appcast.xml** on your server
2. **Update feedURL** in `AutoUpdateManager.swift`
3. **Configure HTTPS** (required for security)

## 📝 Appcast Format

The appcast.xml follows Sparkle's format:

```xml
<?xml version='1.0' encoding='utf-8'?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
  <channel>
    <title>Potter Updates</title>
    <description>Updates for Potter</description>
    <language>en</language>
    <link>https://github.com/username/potter</link>
    <item>
      <title>Potter 2.0.1</title>
      <description><![CDATA[Release notes here]]></description>
      <pubDate>Thu, 20 Jun 2025 12:00:00 +0000</pubDate>
      <enclosure 
        url="https://github.com/username/potter/releases/download/v2.0.1/Potter-2.0.1.dmg" 
        length="file_size_in_bytes" 
        type="application/octet-stream" 
        sparkle:version="2.0.1" 
        sparkle:shortVersionString="2.0.1" 
        sparkle:dsaSignature="signature_hash" />
    </item>
  </channel>
</rss>
```

## 🧪 Testing Updates

### Local Testing

1. **Build current version**: `make build`
2. **Install to Applications**: Copy `dist/Potter.app` to `/Applications/`
3. **Create test release**: 
   ```bash
   python3 scripts/release_manager.py --version 2.0.1 --notes "Test update"
   ```
4. **Test update check**: Launch app, go to Settings → Updates → "Check for Updates Now"

### Release Testing

1. **Create pre-release**: Use GitHub's pre-release option
2. **Test with staging appcast**: Point to test appcast.xml
3. **Verify update flow**: Download, install, verify functionality
4. **Promote to stable**: Update production appcast

## 🔧 Troubleshooting

### Common Issues

**Updates not found:**
- ✅ Check appcast.xml URL accessibility
- ✅ Verify version numbers in appcast
- ✅ Ensure proper XML format

**Download fails:**
- ✅ Verify DMG file exists at download URL
- ✅ Check file permissions and HTTPS
- ✅ Confirm file size matches appcast

**Installation fails:**
- ✅ Verify code signature on DMG
- ✅ Check app bundle structure
- ✅ Ensure proper entitlements

**Permission denied:**
- ✅ App needs admin rights for /Applications install
- ✅ User may need to authorize installation

### Debug Logging

Enable debug logging in Potter:

1. **Check Settings → Logs** for update-related messages
2. **Look for "autoupdate" category** entries
3. **Monitor Sparkle framework** logs

### Manual Recovery

If auto-update fails:

1. **Download latest DMG** from GitHub releases
2. **Manual installation**: Drag to Applications
3. **Reset preferences**: Delete `~/Library/Preferences/com.potter.swift.plist`

## 📊 Analytics & Monitoring

### Update Success Tracking

Monitor update adoption via:
- **GitHub release download counts**
- **User feedback and support requests**
- **Version distribution in logs**

### Error Monitoring

Watch for common issues:
- Failed update checks (network, server)
- Download interruptions
- Installation failures
- Code signature problems

## 🎯 Best Practices

### Release Frequency

- **Patch releases**: Bug fixes, security updates (as needed)
- **Minor releases**: New features, improvements (monthly)
- **Major releases**: Significant changes, UI overhauls (quarterly)

### Release Notes

Write clear, user-friendly release notes:
- **What's new**: Highlight key features
- **Bug fixes**: List resolved issues
- **Breaking changes**: Note any compatibility issues
- **Acknowledgments**: Credit contributors

### Version Numbering

Follow semantic versioning:
- **Major**: Breaking changes (1.0.0 → 2.0.0)
- **Minor**: New features (1.0.0 → 1.1.0)
- **Patch**: Bug fixes (1.0.0 → 1.0.1)

### Testing Strategy

Before each release:
1. **Unit tests**: `make test`
2. **Manual testing**: Core functionality
3. **Update testing**: Previous version → new version
4. **Signing verification**: Code signature validation
5. **Distribution testing**: DMG download and install

---

## 🎉 You're All Set!

Your Potter app now has professional auto-update capabilities! Users will receive automatic notifications when new versions are available, and updates will install seamlessly with proper security verification.

For more details, see:
- [Sparkle Documentation](https://sparkle-project.org/documentation/)
- [CODE_SIGNING_SETUP.md](CODE_SIGNING_SETUP.md)
- [DISTRIBUTION.md](DISTRIBUTION.md)
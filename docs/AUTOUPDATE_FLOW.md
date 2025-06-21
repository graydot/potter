# Auto-Update Flow Documentation

## 🔄 Complete Auto-Update Process

### Phase 1: Initialization (App Startup)
```
Potter Launches
├── AutoUpdateManager.shared initializes
├── Sparkle SPUStandardUpdaterController created
├── Feed URL configured: https://raw.githubusercontent.com/graydot/rephrasely/main/releases/appcast.xml
├── Check interval set: 24 hours
├── User preference loaded: auto-update enabled/disabled
└── Background check scheduled: +5 seconds after launch
```

### Phase 2: Background Check (Every 24 Hours)
```
Background Timer Triggers
├── Sparkle downloads appcast.xml from GitHub
├── Parses XML and extracts latest version info
├── Compares remote version vs current version
├── If newer version found:
│   ├── Checks if user previously dismissed this version
│   ├── Respects user's auto-update preference
│   └── Proceeds to Phase 3
└── If no update or disabled:
    └── Schedules next check in 24 hours
```

### Phase 3: Update Notification (User Interaction)
```
Update Found - Sparkle shows native dialog:
┌─────────────────────────────────────────┐
│  🎭 A new version of Potter is available │
│                                         │
│  Potter 2.0.1 is now available.        │
│  You have 2.0.0.                       │
│                                         │
│  [Release Notes...] [Show Details ▼]   │
│                                         │
│  [ Skip This Version ]  [ Remind Later ]│
│  [        Install and Relaunch        ] │
└─────────────────────────────────────────┘

User Options:
├── "Install and Relaunch" → Phase 4
├── "Remind Later" → Check again in 24 hours
└── "Skip This Version" → Ignore this version forever
```

### Phase 4: Download Process (Sparkle Handles)
```
User Clicks "Install and Relaunch"
├── Sparkle downloads DMG from GitHub release URL
│   ├── URL: https://github.com/graydot/rephrasely/releases/download/v2.0.1/Potter-2.0.1.dmg
│   ├── Progress bar shown to user
│   ├── Network error handling and retries
│   └── File integrity verification
├── Security verification:
│   ├── Validates DMG code signature
│   ├── Checks DSA signature from appcast
│   ├── Ensures download authenticity
│   └── Prevents tampering/downgrade attacks
└── Proceeds to Phase 5 if all checks pass
```

### Phase 5: Installation Process (Sparkle Handles)
```
DMG Downloaded and Verified
├── Mount DMG automatically
├── Extract Potter.app from DMG
├── Prepare for app replacement:
│   ├── Save current app location (/Applications/Potter.app)
│   ├── Prepare new app for installation
│   └── Handle file permissions and ownership
├── Show final confirmation:
│   ┌─────────────────────────────────────┐
│   │  Ready to install Potter 2.0.1     │
│   │                                     │
│   │  Potter will quit and relaunch     │
│   │  with the new version.             │
│   │                                     │
│   │  [ Cancel ]  [ Install and Quit ]  │
│   └─────────────────────────────────────┘
└── User clicks "Install and Quit" → Phase 6
```

### Phase 6: App Replacement (Sparkle Handles)
```
Sparkle Installer Takes Over
├── Gracefully terminate Potter.app
├── Wait for complete shutdown
├── Atomic replacement:
│   ├── Move old Potter.app to trash/backup
│   ├── Copy new Potter.app to /Applications/
│   ├── Preserve file permissions and attributes
│   └── Update filesystem metadata
├── Cleanup:
│   ├── Unmount and eject DMG
│   ├── Remove temporary download files
│   └── Clear update caches
└── Launch updated Potter.app
```

### Phase 7: Post-Update (New Version Runs)
```
Updated Potter 2.0.1 Launches
├── Normal app initialization
├── AutoUpdateManager detects version change
├── Logs successful update completion
├── User data and preferences preserved
├── Settings, API keys, prompts intact
└── Next update check scheduled for 24 hours
```

## 🛡️ Security & Safety Features

### Code Signing Verification
- **DMG Signature**: Verified against Developer ID
- **App Bundle Signature**: Validated during installation
- **Chain of Trust**: Ensures authentic Apple Developer certificate
- **Gatekeeper Compliance**: Passes macOS security checks

### Download Security
- **HTTPS Only**: All downloads over encrypted connections
- **DSA Signatures**: Cryptographic verification of appcast entries
- **File Integrity**: SHA checksums prevent corruption
- **Replay Protection**: Prevents old version injection

### Installation Safety
- **Atomic Replacement**: All-or-nothing installation
- **Backup Creation**: Old version preserved during update
- **Permission Preservation**: User data and settings maintained
- **Rollback Capability**: Can restore if installation fails

## 🧪 Testing Scenarios

### Test 1: Normal Update Flow
```bash
# Install version 2.0.0
make build && cp -r dist/Potter.app /Applications/

# Create new release
make release  # Creates 2.0.1

# Wait 24 hours OR trigger manual check
# Potter → Settings → Updates → "Check for Updates Now"
```

### Test 2: Network Failure Handling
```bash
# Disconnect internet during download
# Verify graceful error handling and retry logic
```

### Test 3: Installation Failure Recovery
```bash
# Simulate permission issues
# Verify rollback and error reporting
```

### Test 4: User Preference Respect
```bash
# Disable auto-updates in settings
# Verify no automatic checks occur
# Manual checks should still work
```

## 📊 Monitoring & Logging

### Potter's Custom Logging
```
[autoupdate] 🔄 Setting up Sparkle auto-updater...
[autoupdate] 📡 Feed URL: https://raw.githubusercontent.com/graydot/rephrasely/main/releases/appcast.xml
[autoupdate] ⏰ Check interval: 24.0 hours
[autoupdate] 🔧 Auto-check enabled: true
[autoupdate] 🔍 Background update check
[autoupdate] 📡 Successfully loaded appcast
[autoupdate] ✨ Update found: 2.0.1
[autoupdate] 📦 Installing update: 2.0.1
```

### Sparkle's Internal Logging
- Framework handles detailed download progress
- Network error details and retry attempts
- Security verification results
- Installation step tracking

## 🎯 What This Means for Users

### Seamless Experience
1. **Zero Configuration**: Works out of the box
2. **Secure by Default**: All updates verified and signed
3. **Non-Intrusive**: Background checks, user controls timing
4. **Professional UI**: Native macOS dialogs and progress
5. **Data Preservation**: Settings and data always preserved

### User Control
1. **Manual Override**: Can check for updates anytime
2. **Preference Control**: Can disable auto-updates
3. **Version Choice**: Can skip specific versions
4. **Timing Control**: Can defer updates ("Remind Later")

### Enterprise-Grade Reliability
1. **Atomic Updates**: Never leaves app in broken state
2. **Rollback Safety**: Can recover from failed updates
3. **Network Resilience**: Handles connectivity issues
4. **Security First**: Multiple layers of verification

---

## 🎉 Summary

**Sparkle handles 95% of the complexity** - all the hard parts like download management, security verification, UI, installation, and app replacement. 

**We only customize 5%** - feed URL, logging integration, settings UI, and manual triggers.

This gives us enterprise-grade auto-update functionality with minimal code and maximum reliability!
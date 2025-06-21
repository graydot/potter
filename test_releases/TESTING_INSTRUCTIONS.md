
# Auto-Update Testing Instructions

## Test Scenarios Created:

1. **Version 2.0.0** - Base version (current)
2. **Version 2.0.1** - Patch update available  
3. **Version 2.1.0** - Minor update available

## Testing Steps:

### Step 1: Build and Install Current Version
```bash
# Build current version (should be 2.0.0)
make build

# Install to Applications
cp -r dist/Potter.app /Applications/

# Launch Potter
open /Applications/Potter.app
```

### Step 2: Test Manual Update Check
1. Open Potter
2. Click menu bar icon → "Check for Updates..."
3. Should find version 2.1.0 available

### Step 3: Test Settings UI
1. Open Potter → Settings → Updates tab
2. Check current version display
3. Toggle auto-update preference
4. Click "Check for Updates Now"

### Step 4: Test with Local Server (Advanced)
```bash
# Serve test appcast locally
cd test_releases
python3 -m http.server 8000

# Update AutoUpdateManager.swift feedURL to:
# http://localhost:8000/appcast.xml

# Rebuild and test
make build
```

### Step 5: Production Testing
1. Create real GitHub release: `make release`
2. Wait 24 hours or trigger manual check
3. Verify update downloads and installs

## Troubleshooting:

- **No updates found**: Check appcast URL and format
- **Download fails**: Verify DMG exists at GitHub release URL  
- **Install fails**: Check code signing and permissions
- **Version mismatch**: Ensure appcast version > current version


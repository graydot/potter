#!/usr/bin/env python3
"""
Auto-Update Testing Script
Creates test scenarios for Potter's auto-update system
"""

import os
import shutil
import json
from pathlib import Path

def create_test_environment():
    """Set up a complete test environment for auto-updates"""
    
    print("🧪 Setting up auto-update test environment...")
    
    # Create test versions
    versions = [
        {"version": "2.0.0", "notes": "Initial release with auto-updates"},
        {"version": "2.0.1", "notes": "Bug fixes and improvements"},
        {"version": "2.1.0", "notes": "New features and enhanced UI"}
    ]
    
    # Create test appcast
    test_appcast = """<?xml version='1.0' encoding='utf-8'?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
  <channel>
    <title>Potter Updates (Test)</title>
    <description>Test updates for Potter</description>
    <language>en</language>
    <link>https://github.com/jebasingh/potter</link>"""
    
    for i, version_info in enumerate(versions):
        test_appcast += f"""
    <item>
      <title>Potter {version_info['version']}</title>
      <description><![CDATA[{version_info['notes']}]]></description>
      <pubDate>Thu, {20+i} Jun 2025 12:00:00 +0000</pubDate>
      <enclosure 
        url="https://github.com/jebasingh/potter/releases/download/v{version_info['version']}/Potter-{version_info['version']}.dmg" 
        length="10485760" 
        type="application/octet-stream" 
        sparkle:version="{version_info['version']}" 
        sparkle:shortVersionString="{version_info['version']}" 
        sparkle:dsaSignature="test_signature_{i}" />
    </item>"""
    
    test_appcast += """
  </channel>
</rss>"""
    
    # Write test appcast
    os.makedirs("test_releases", exist_ok=True)
    with open("test_releases/appcast.xml", "w") as f:
        f.write(test_appcast)
    
    print("✅ Test appcast created at test_releases/appcast.xml")
    
    # Create test instructions
    test_instructions = """
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

"""
    
    with open("test_releases/TESTING_INSTRUCTIONS.md", "w") as f:
        f.write(test_instructions)
    
    print("✅ Testing instructions created at test_releases/TESTING_INSTRUCTIONS.md")
    print()
    print("🎯 Next steps:")
    print("1. Follow test_releases/TESTING_INSTRUCTIONS.md")
    print("2. Or run: make build && make release")
    print("3. Test update flow with real releases")

if __name__ == "__main__":
    create_test_environment()
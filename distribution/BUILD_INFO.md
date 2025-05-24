# Build Information

- **Version**: e7e28f9
- **Build Date**: 2025-05-23 13:49:46
- **Commit Hash**: e7e28f9
- **App Size**:  42M
- **ZIP Size**:  52M
- **TAR Size**:  19M

## Recent Fixes

✅ **Code Signing Issue Fixed**: The app now has a valid signature after Info.plist modifications
✅ **Launch Helper Added**: Included `launch_helper.sh` to help with Gatekeeper issues
✅ **Comprehensive Documentation**: Added troubleshooting guide for common launch issues

## Distribution Files

- `Rephrasely.app` - Direct macOS application (drag to /Applications)
- `Rephrasely.app.zip` - Compressed version (extract then drag to /Applications)
- `Rephrasely.app.tar.gz` - Compressed version (extract then drag to /Applications)
- `launch_helper.sh` - Helper script for launch issues
- `README.md` - Complete installation and troubleshooting guide

## Installation Options

### Option 1: Direct .app (Recommended)
1. Download `Rephrasely.app`
2. Drag directly to /Applications folder
3. Right-click and select "Open" on first launch (if unsigned)

### Option 2: ZIP Download
1. Download `Rephrasely.app.zip`
2. Extract the ZIP file
3. Drag `Rephrasely.app` to /Applications
4. Right-click and select "Open" on first launch (if unsigned)

### Option 3: TAR Download
1. Download `Rephrasely.app.tar.gz`
2. Extract the TAR file
3. Drag `Rephrasely.app` to /Applications
4. Right-click and select "Open" on first launch (if unsigned)

## If Double-Click Doesn't Work

### Quick Fix
```bash
./launch_helper.sh
```

### Manual Fix
```bash
xattr -r -d com.apple.quarantine Rephrasely.app
open Rephrasely.app
```

Or simply right-click the app and select "Open".


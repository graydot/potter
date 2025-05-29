# 🚀 Potter.app Installation Guide

**Secure installation without giving Terminal accessibility access**

## 📦 What You Have

You now have a **standalone Potter.app** that:
- ✅ Runs independently (no Terminal needed)
- ✅ Only needs accessibility permissions for itself
- ✅ Contains all dependencies bundled inside
- ✅ Has a proper macOS app icon
- ✅ Can be installed like any regular Mac app

## 🛠 Installation Steps

### 1. Install the App
```bash
# Option A: Copy to Applications folder
cp -r dist/Potter.app /Applications/

# Option B: Or just drag & drop
# Drag dist/Potter.app to your Applications folder in Finder
```

### 2. Launch the App
- **Double-click** `Potter.app` in Applications
- **OR** use Spotlight: Press `Cmd+Space`, type "Potter"

### 3. Grant Permissions (First Time Only)
When you first launch:

1. **macOS will show security warnings** - this is normal for unsigned apps
   - Click "Open" when prompted
   - If blocked, go to `System Preferences > Security & Privacy > General`
   - Click "Open Anyway" next to the Potter warning

2. **Grant Accessibility Permissions**
   - macOS will prompt for accessibility permissions
   - Click "Open System Preferences"
   - **Add `Potter.app`** to the accessibility list (NOT Terminal!)
   - Check the box next to Potter to enable it

### 4. Test It Works
- Select any text in any app
- Press `Cmd+Shift+R`
- Watch your text get AI-enhanced!

## 🔐 Security Benefits

### ✅ What This Solves
- **No Terminal access needed** - Potter.app runs independently
- **Minimal permissions** - Only Potter needs accessibility access
- **Sandboxed** - The app is contained and doesn't affect other tools
- **Revokable** - Easy to remove permissions if needed

### 🛡️ Permission Management
To manage permissions later:
1. `System Preferences > Security & Privacy > Privacy`
2. Select `Accessibility`
3. Find `Potter.app` in the list
4. Uncheck to revoke, check to grant

## 📱 Usage

### Basic Usage
- **Global hotkey**: `Cmd+Shift+R` works in any app
- **System tray**: Look for blue "R" icon in menu bar
- **Modes**: Right-click tray icon to switch between:
  - Rephrase (default)
  - Summarize
  - Expand  
  - Casual tone
  - Formal tone

### Quitting the App
- Right-click the tray icon → "Quit"
- **OR** use Activity Monitor if needed

## 🔧 Advanced Options

### Auto-Start on Login
To make Potter start automatically:
1. `System Preferences > Users & Groups > Login Items`
2. Click "+" and add `Potter.app`

### Code Signing (Optional)
For extra security, you can self-sign the app:
```bash
# Sign the app bundle (requires Developer ID)
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/Potter.app
```

### Creating a DMG (Optional)
To create a proper installer:
```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "Potter" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Potter.app" 175 120 \
  --hide-extension "Potter.app" \
  --app-drop-link 425 120 \
  "Potter.dmg" \
  "dist/"
```

## 🆘 Troubleshooting

### App Won't Launch
1. **Check permissions**: Make sure Potter.app has accessibility permissions
2. **Security settings**: Go to Security & Privacy and click "Open Anyway"
3. **Rebuild if needed**: Run `./.venv/bin/python scripts/build_app.py` again

### "App is damaged" Error
This happens with unsigned apps:
```bash
# Remove quarantine attribute
xattr -rd com.apple.quarantine dist/Potter.app
```

### Performance Issues
- The app might take a few seconds to start (normal for bundled Python apps)
- First AI request might be slower (OpenAI connection initialization)

### Logs
If something goes wrong, check logs:
```bash
# View app logs
tail -f /Applications/Potter.app/Contents/MacOS/potter.log
```

## 🎉 Success!

You now have a **secure, standalone Potter.app** that:
- ✅ Doesn't require Terminal permissions
- ✅ Runs like a native Mac app  
- ✅ Can be easily shared or distributed
- ✅ Provides the same great AI text processing functionality

**Enjoy your secure, AI-powered text enhancement!** 🚀 
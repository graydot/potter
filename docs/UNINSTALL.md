# Potter Uninstall Guide

This guide will help you completely remove Potter from your macOS system.

## Complete Uninstall Steps

### 1. Quit the Application
First, make sure Potter is not running:
```bash
# Stop the Python script version
pkill -f "python.*potter.py"

# Stop the bundled app version
pkill -f "Potter"

# Or right-click the tray icon and select "Quit"
```

### 2. Remove Application Files

#### If using the bundled app:
```bash
# Remove the app bundle
rm -rf /Applications/Potter.app
# or
rm -rf ~/Applications/Potter.app
# or wherever you placed the app

# Remove from Downloads if still there
rm -rf ~/Downloads/Potter.app
```

#### If using the Python script:
```bash
# Navigate to and remove the project directory
cd ~/Workspace  # or wherever you cloned it
rm -rf rephrasely  # Note: directory name may still be rephrasely
```

### 3. Remove Application Data

#### Settings and Configuration:
```bash
# Remove settings file (for bundled app)
rm -rf ~/Library/Application\ Support/Potter/

# Remove settings file (for Python script)
rm -f ~/Workspace/rephrasely/config/settings.json  # if it exists
```

#### Log Files:
```bash
# Remove log files
rm -f ~/Library/Logs/potter.log
rm -f ~/Workspace/rephrasely/potter.log  # if using script version
```

#### PID Files:
```bash
# Remove instance lock files
rm -f ~/.potter.pid
```

### 4. Remove System Permissions

#### Accessibility Permission:
1. Open **System Settings** (or **System Preferences** on older macOS)
2. Go to **Privacy & Security** → **Accessibility**
3. Find and remove:
   - **Potter** (if you used the bundled app)
   - **Python** (if you used the Python script)
4. Click the **"-"** button to remove the permission

#### Reset Notification Permissions (if needed):
1. Open **System Settings** → **Notifications**
2. Find **Potter** in the list
3. Turn off all notification settings or remove it entirely

### 5. Remove from Login Items (if enabled)

1. Open **System Settings** → **General** → **Login Items**
2. Look for **Potter** in the list
3. Select it and click the **"-"** button to remove

### 6. Clean Up Terminal/Environment (if used as script)

If you installed dependencies globally:
```bash
# Remove Python packages (only if you don't need them for other projects)
pip uninstall openai pyperclip pystray pynput pillow python-dotenv

# If you used a virtual environment, just delete it:
rm -rf ~/Workspace/rephrasely/venv  # or wherever your venv was
```

### 7. Remove from PATH (if modified)

If you added Potter to your PATH, remove it from:
- `~/.zshrc`
- `~/.bash_profile` 
- `~/.bashrc`

Look for lines like:
```bash
export PATH="$PATH:/path/to/potter"
```

### 8. Clear Application Cache (macOS)

```bash
# Clear any cached application data
rm -rf ~/Library/Caches/com.potter.app/
```

## Verification

To verify complete removal:

```bash
# Check for running processes
ps aux | grep -i potter

# Check for remaining files
find ~ -name "*potter*" -type f 2>/dev/null
find ~ -name "*Potter*" -type f 2>/dev/null

# Check accessibility permissions
# Look in System Settings → Privacy & Security → Accessibility
```

## Quick Uninstall Script

You can also use this one-liner to remove most files:

```bash
#!/bin/bash
echo "🗑️  Removing Potter..."

# Stop processes
pkill -f "python.*potter.py" 2>/dev/null
pkill -f "Potter" 2>/dev/null

# Remove app files
rm -rf /Applications/Potter.app 2>/dev/null
rm -rf ~/Applications/Potter.app 2>/dev/null
rm -rf ~/Downloads/Potter.app 2>/dev/null

# Remove data files
rm -rf ~/Library/Application\ Support/Potter/ 2>/dev/null
rm -f ~/Library/Logs/potter.log 2>/dev/null
rm -f ~/.potter.pid 2>/dev/null
rm -rf ~/Library/Caches/com.potter.app/ 2>/dev/null

# Remove source code (be careful with this!)
# rm -rf ~/Workspace/rephrasely 2>/dev/null

echo "✅ Potter removed! Please manually remove accessibility permissions in System Settings."
```

## Troubleshooting

If you have issues:

1. **Process won't stop**: Force quit using Activity Monitor
2. **Permission denied**: Use `sudo` for system files (be careful)
3. **Files still exist**: Check for hidden files with `ls -la`
4. **Permission still shows in System Settings**: It may take a restart to fully clear

## Need Help?

If you encounter any issues during uninstallation, please:
1. Check the logs first: `~/Library/Logs/potter.log`
2. Open an issue on the GitHub repository
3. Include your macOS version and installation method

---

**Note**: This uninstall process will not remove your OpenAI API key from your system if you stored it elsewhere (like in your shell profile). Make sure to remove that separately if needed. 
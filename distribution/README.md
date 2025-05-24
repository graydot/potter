# Rephrasely for macOS

A powerful AI-powered text processing tool that runs in your menu bar, providing instant access to rephrase, summarize, expand, and tone adjustment features.

## ✨ First-Time Setup Made Easy

Rephrasely now features **automatic first-launch detection**! When you run the app for the first time, it will:

1. **Welcome you** with a friendly setup dialog
2. **Guide you** to configure your OpenAI API key
3. **Let you customize** all preferences in the native macOS settings interface
4. **Automatically restart** with your settings applied

No more command-line configuration needed - everything is handled through the beautiful native UI!

## Installation

### Quick Installation (Recommended)
1. Download `Rephrasely.app` 
2. Drag it to your `/Applications` folder
3. Right-click and select "Open" on first launch (security requirement)

### Alternative: ZIP Download
1. Download `Rephrasely.app.zip`
2. Extract the ZIP file
3. Drag `Rephrasely.app` to your `/Applications` folder
4. Right-click and select "Open" on first launch

### Alternative: TAR Download
1. Download `Rephrasely.app.tar.gz`
2. Extract the TAR file (double-click in Finder)
3. Drag `Rephrasely.app` to your `/Applications` folder
4. Right-click and select "Open" on first launch

## Troubleshooting

### ❓ App Won't Launch (Double-click doesn't work)
1. **Try the Launch Helper**: Run `./launch_helper.sh` from the Terminal in the same folder as Rephrasely.app
2. **Check Gatekeeper**: Right-click Rephrasely.app → "Open" → "Open" (bypasses Gatekeeper)
3. **Remove Quarantine**: Run `xattr -r -d com.apple.quarantine Rephrasely.app` in Terminal

### 🔑 Testing API Key Paste (NEW FIX)
To verify the paste functionality works correctly:
1. Open Rephrasely settings (click menu bar icon → Preferences)
2. Copy your API key from OpenAI dashboard (Cmd+C)
3. Click in the "OpenAI API Key" field
4. Press **Cmd+V** to paste - this should now work!
5. Other keyboard shortcuts that should work:
   - **Cmd+A**: Select all text in field
   - **Cmd+C**: Copy selected text
   - **Cmd+X**: Cut selected text

### 💾 Testing Settings Save (NEW FIX)
To verify the save dialog closes properly:
1. Make any change in settings (like toggling a checkbox)
2. Click "Save" button
3. **Dialog should close immediately** after successful save
4. Check terminal output for detailed debug messages
5. Reopen settings to verify changes were saved

### 🚀 First Launch Experience
On first launch, Rephrasely will:
1. Show a welcome dialog
2. Prompt you to configure your OpenAI API key
3. Open the settings window automatically
4. Guide you through the setup process

### ⌨️ Hotkey Not Working
1. Check hotkey conflicts in Settings → General
2. Try resetting to default: Cmd+Shift+R
3. Make sure no other app is using the same combination
4. Restart Rephrasely after changing hotkey

### 🤖 AI Processing Issues
1. **Verify API Key**: Check that your OpenAI API key is correctly entered in Settings
2. **Check Internet**: Ensure you have a stable internet connection
3. **Select Text First**: Highlight text before pressing the hotkey
4. **Watch Menu Bar**: Look for the processing spinner in the menu bar icon

### 📋 Clipboard Issues
1. **Text Not Copied**: Make sure text is selected before pressing hotkey
2. **Paste Failed**: Processed text is still in clipboard - manually press Cmd+V
3. **Original Text Lost**: Rephrasely preserves original clipboard when possible

### 🔧 Debug Mode
For detailed troubleshooting, check the log file:
```bash
tail -f ~/rephrasely.log
```

### 🆘 Still Having Issues?
1. Try the launch helper script: `./launch_helper.sh`
2. Check Console app for error messages
3. Make sure you're running macOS 10.15 or later
4. Try restarting your Mac if keyboard detection isn't working

## Features

- **Rephrase**: Rewrite text while maintaining meaning
- **Summarize**: Create concise summaries of long text
- **Expand**: Add detail and expand on ideas
- **Casual Tone**: Convert formal text to casual language
- **Formal Tone**: Convert casual text to formal language
- **Custom Hotkey**: Set your preferred keyboard shortcut
- **AI Model Selection**: Choose between GPT-3.5, GPT-4, and GPT-4-turbo

## Usage

1. Launch Rephrasely (it will appear in your menu bar)
2. Select any text in any application
3. Use your configured hotkey (default: Cmd+Shift+R)
4. Choose the desired text transformation
5. The processed text will replace your selection

## Configuration

Click the Rephrasely icon in your menu bar and select "Settings" to:
- Set up your API key
- Customize hotkeys
- Modify AI prompts
- Choose your preferred AI model
- Configure startup behavior

## Need Help?

If you continue to have issues:
1. Try the launch helper script: `./launch_helper.sh`
2. Check the troubleshooting section above
3. Ensure you have the necessary permissions for the app

The app is designed to work seamlessly once properly launched!

# Rephrasely Distribution

This folder contains the built macOS application files ready for download and installation.

## Download Options

Choose your preferred download format:

**Option 1: ZIP Archive (Recommended)**
- **File**: [Rephrasely.app.zip](./Rephrasely.app.zip) 
- **Best for**: Most users, smaller download size
- **Installation**: Extract ZIP → Drag to Applications

**Option 2: Direct App Bundle** 
- **File**: [Rephrasely.app.tar.gz](./Rephrasely.app.tar.gz)
- **Best for**: Preserves file permissions, GitHub compatible
- **Installation**: Extract TAR → Drag to Applications

**Option 3: Uncompressed**
- **File**: [Rephrasely.app](./Rephrasely.app/) (folder)
- **Best for**: Direct access, no extraction needed
- **Installation**: Drag directly to Applications

## Installation Steps

1. **Download** your preferred format from above
2. **Extract** if needed (ZIP/TAR files)
3. **Move** `Rephrasely.app` to your `/Applications` folder
4. **Launch** by double-clicking
5. **Grant permissions** when prompted (Accessibility, Screen Recording)
6. **Add your OpenAI API key** in preferences (right-click menu bar icon)

## System Requirements

- macOS 10.14 (Mojave) or later
- Python 3.8+ (if running from source)

## Features

- ✅ Global hotkey text processing (default: Cmd+Shift+R)
- ✅ Multiple AI prompts (rephrase, summarize, expand, casual, formal)
- ✅ Custom prompt creation with output formats
- ✅ Native macOS interface
- ✅ Menu bar integration
- ✅ Auto-paste functionality

## Usage

1. Select any text in any application
2. Press your configured hotkey (default: Cmd+Shift+R)
3. The AI will process your text and automatically paste the result

## Configuration

Right-click the menu bar icon and select "Preferences" to:
- Customize hotkeys
- Add/edit/remove prompts
- Configure AI model settings
- Set output formats (text, images, PDF)

---

*Built automatically from the latest source code* 
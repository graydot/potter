# Rephrasely for macOS

A powerful AI-powered text processing tool that runs in your menu bar, providing instant access to rephrase, summarize, expand, and tone adjustment features.

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

### App Won't Launch (Double-Click Doesn't Work)

If double-clicking doesn't work, try these solutions:

#### Solution 1: Use the Launch Helper
1. Open Terminal
2. Navigate to the folder containing `Rephrasely.app`
3. Run: `./launch_helper.sh`

#### Solution 2: Remove Quarantine Manually
```bash
# In Terminal, navigate to the folder with Rephrasely.app
xattr -r -d com.apple.quarantine Rephrasely.app
open Rephrasely.app
```

#### Solution 3: Right-Click Method
1. Right-click on `Rephrasely.app`
2. Select "Open" from the context menu
3. Click "Open" in the security dialog

#### Solution 4: System Preferences Override
1. Open System Preferences → Security & Privacy
2. Go to the "General" tab
3. If you see a message about Rephrasely being blocked, click "Open Anyway"

### Security Warnings

Since this app is not signed with an Apple Developer certificate, macOS will show security warnings. This is normal and safe - the app is open source and doesn't contain any malicious code.

**What you might see:**
- "Rephrasely can't be opened because it is from an unidentified developer"
- "macOS cannot verify that this app is free from malware"

**These are safe to override** by using the right-click → Open method.

### App Appears to Not Be Running

Rephrasely runs as a **menu bar application**. After launching:

1. Look for the Rephrasely icon in your menu bar (top of screen)
2. The app may take a few seconds to fully initialize
3. If you don't see the icon, check if the process is running:
   ```bash
   ps aux | grep Rephrasely
   ```

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
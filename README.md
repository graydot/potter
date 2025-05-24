<<<<<<< HEAD
# Potter Releases

This repository contains only release builds of Potter.

## Releases

Release DMG files are available in the [Releases](https://github.com/yourusername/Potter/releases) section.

## Source Code

The source code is maintained in a separate private repository.

---

Potter - A powerful text rephrasing tool for macOS. 
=======
# 🔄 Rephrasely - AI-Powered Text Enhancement for macOS

**Secure, standalone macOS app that transforms your text with AI using global hotkeys**

## ✨ New Features

### 🎛️ **Customizable Settings UI**
- **Visual preferences window** with tabbed interface
- **Custom prompts** for each processing mode
- **Hotkey customization** 
- **AI model selection** (GPT-3.5, GPT-4, GPT-4-turbo)
- **Export/Import settings** for easy backup and sharing
- **Real-time settings application** without restart

### 🎯 **Enhanced Processing Modes**
- **Rephrase**: Make text clearer and more professional
- **Summarize**: Create concise summaries
- **Expand**: Add detail and examples
- **Casual**: Convert to friendly, casual tone
- **Formal**: Make text more professional
- **Custom modes**: Add your own with custom prompts

## 🚀 Features

- **🔥 Global Hotkey**: Works in any app (default: `Cmd+Shift+R`)
- **🤖 AI-Powered**: Uses OpenAI GPT models for text processing
- **🎨 Native macOS UI**: Beautiful settings interface with proper macOS styling
- **🔒 Secure**: Standalone app requiring minimal permissions
- **⚡ Fast**: Instant text processing and replacement
- **🎯 Multiple Modes**: Switch between different processing styles
- **📱 System Tray**: Easy mode switching via menu bar icon
- **⚙️ Highly Customizable**: Edit prompts, hotkeys, and AI parameters

## 📦 Installation

### Option 1: Download from GitHub Releases (Recommended)
1. Visit the [Releases page](https://github.com/yourusername/rephrasely/releases)
2. Download the latest `Rephrasely-X.X.X.dmg` file
3. Double-click the DMG file to open it
4. Drag `Rephrasely.app` to the Applications folder in the window
5. Eject the DMG and launch Rephrasely from Applications
6. Right-click the app and select "Open" on first launch (security requirement)
7. Configure your OpenAI API key in the app settings

### Option 2: Build from Source
For development or customization:

1. **Download or clone** this repository
2. **Set up your API key**:
   ```bash
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```
3. **Build the standalone app**:
   ```bash
   python build_app.py
   ```
4. **Install the app**:
   ```bash
   cp -r dist/Rephrasely.app /Applications/
   ```

### 🚀 **For Developers**
Set up the automated build system:
```bash
# Install git hooks for automatic building
./scripts/setup_hooks.sh

# Test the build system  
./scripts/build_for_distribution.sh
```

See [DISTRIBUTION.md](DISTRIBUTION.md) for complete build system documentation.

### First Launch
1. **Open Rephrasely.app** from Applications
2. **Grant accessibility permissions** when prompted
3. **Look for the blue "R"** in your menu bar
4. **Test with any text**: Select text and press `Cmd+Shift+R`

## ⚙️ Customization

### Opening Preferences
- **Right-click** the menu bar icon → "Preferences..."
- **Or** while the app is focused, use `Cmd+,`

### Settings Tabs

#### 📝 **Prompts Tab**
- **Edit any processing mode prompt**
- **Add context and specific instructions**
- **Reset to defaults** with one click
- **Real-time preview** of your changes

Example custom prompts:
```
Rephrase: "Please rewrite this text to be more persuasive and compelling:"
Summarize: "Create a bullet-point summary highlighting key actions:"
Technical: "Rewrite this with precise technical terminology and clarity:"
```

#### ⚡ **General Tab**
- **Global Hotkey**: Change from default `Cmd+Shift+R`
- **Auto-paste**: Toggle automatic text replacement
- **Notifications**: Show/hide success messages

#### 🤖 **Advanced Tab**
- **AI Model**: Choose between GPT-3.5-turbo, GPT-4, GPT-4-turbo
- **Max Tokens**: Control response length (100-4000)
- **Temperature**: Adjust creativity (0.0-1.0)
- **Export/Import**: Save and share your configurations

### Example Custom Settings
```json
{
  "prompts": {
    "rephrase": "Make this text more engaging and persuasive:",
    "email": "Convert this to a professional email format:",
    "creative": "Rewrite this with more creativity and flair:",
    "technical": "Make this more technically precise and detailed:"
  },
  "hotkey": "cmd+alt+r",
  "model": "gpt-4",
  "temperature": 0.8,
  "auto_paste": true
}
```

## 🎯 Usage

### Basic Operation
1. **Select any text** in any application
2. **Press your hotkey** (default: `Cmd+Shift+R`)
3. **Watch the magic**: Text is automatically enhanced and replaced

### Mode Switching
- **Menu bar icon**: Right-click → Select mode
- **Quick switch**: Choose from Rephrase, Summarize, Expand, Casual, Formal
- **Custom modes**: Add your own via settings

### Hotkey Examples
- `Cmd+Shift+R` - Default
- `Cmd+Alt+T` - Alternative
- `Ctrl+Shift+A` - Windows-style
- `Cmd+Opt+Space` - Spacebar trigger

## 🔧 Advanced Features

### Settings Management
- **Export settings**: Share configurations with team members
- **Import settings**: Load pre-configured setups
- **Reset options**: Return to defaults for any setting
- **Live reload**: Changes apply immediately

### Custom Prompt Ideas
```
Business: "Rewrite this for a C-suite executive audience:"
Social: "Make this suitable for social media posting:"
Academic: "Convert to academic writing style with citations:"
Marketing: "Transform this into compelling marketing copy:"
Support: "Rewrite as a helpful customer support response:"
```

### AI Model Comparison
- **GPT-3.5-turbo**: Fast, cost-effective, great for basic tasks
- **GPT-4**: Higher quality, better reasoning, more expensive
- **GPT-4-turbo**: Latest model, best performance, fastest

## 🛡️ Security & Privacy

### Secure Installation
- ✅ **Standalone app**: No Terminal permissions needed
- ✅ **Minimal access**: Only requires accessibility for Rephrasely.app
- ✅ **No system modification**: Safe, reversible installation
- ✅ **Local processing**: Settings stored locally

### Permission Management
1. **System Preferences** → **Security & Privacy** → **Privacy**
2. **Select "Accessibility"**
3. **Only enable "Rephrasely.app"** (not Terminal or other tools)
4. **Easily revokable** if needed

## 📁 File Structure

```
rephrasely/
├── rephrasely.py          # Main application
├── settings_ui.py         # Preferences interface
├── build_app.py          # App builder
├── requirements.txt      # Dependencies
├── .env                  # API key (you create this)
├── settings.json         # User preferences (auto-created)
├── example_settings.json # Sample configuration
└── dist/
    └── Rephrasely.app    # Built application
```

## 🐛 Troubleshooting

### Settings UI Issues
- **UI not opening**: Check if tkinter is properly installed
- **Settings not saving**: Verify write permissions in app directory
- **Prompts not updating**: Click "Apply" then "Save" in preferences

### Performance Tips
- **Use GPT-3.5-turbo** for faster responses
- **Lower max_tokens** for quicker processing
- **Reduce temperature** for more consistent results

### Common Issues
- **App won't start**: Check `.env` file has valid API key
- **No permissions dialog**: Remove and re-add app in Accessibility settings
- **Hotkey not working**: Try different key combination in preferences

## 🎨 Customization Examples

### Professional Email Mode
```json
{
  "prompts": {
    "email": "Convert this to a professional email with proper greeting, body, and closing:"
  }
}
```

### Social Media Mode
```json
{
  "prompts": {
    "social": "Rewrite this for social media with appropriate hashtags and engaging tone:"
  }
}
```

### Code Documentation Mode
```json
{
  "prompts": {
    "docs": "Rewrite this as clear, professional technical documentation:"
  }
}
```

## 🔄 Updates & Roadmap

### Recent Additions
- ✅ Visual settings interface
- ✅ Custom prompt editing
- ✅ Hotkey customization
- ✅ Model selection
- ✅ Export/import settings

### Coming Soon
- 🔮 Keyboard shortcut for opening preferences
- 🔮 More AI model options
- 🔮 Text preprocessing options
- 🔮 Undo/redo functionality
- 🔮 Batch processing mode

## 💡 Tips & Tricks

### Effective Prompts
- **Be specific**: "Make this more persuasive for sales" vs "make it better"
- **Include context**: "Rewrite for a technical audience familiar with APIs"
- **Set tone**: "Use a friendly but professional tone"
- **Specify format**: "Convert to bullet points" or "Make it a single paragraph"

### Workflow Integration
- **Email writing**: Select draft → Rephrase → Professional communication
- **Documentation**: Select technical notes → Expand → Detailed docs
- **Social media**: Select formal text → Casual → Engaging posts

## 🆘 Support

Having issues? Check these resources:
1. **Review logs**: `rephrasely.log` in the app directory
2. **Check permissions**: Ensure Accessibility access is granted
3. **Verify API key**: Test in `.env` file
4. **Try safe mode**: Use default settings temporarily

## 📄 License

MIT License - feel free to modify and distribute!

---

**Enjoy your AI-powered text enhancement! 🚀** 
>>>>>>> ac4fb4a (partially working)

<<<<<<< HEAD
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
=======
# 🎭 Potter
>>>>>>> db2f5bf (build to potter repo)

A powerful text processing and rephraseing tool for macOS with AI capabilities.

## 📦 Download

### Latest Release
Download the latest version from the [Releases](https://github.com/jebasingh/potter/releases) page.

### Installation
1. Download the `Potter-1.0.0.dmg` file
2. Double-click to mount the DMG
3. Drag Potter to your Applications folder
4. Launch Potter from Applications

## ✨ Features

- **AI-Powered Text Processing** - Advanced text rephrasing and improvement
- **Global Hotkeys** - Quick access from anywhere on your system
- **Native macOS Integration** - Fully signed and notarized
- **Privacy Focused** - All processing respects your privacy settings

## 🚀 Quick Start

1. **Install Potter** from the DMG
2. **Launch the app** from Applications
3. **Configure your preferences** in the Potter settings
4. **Set up global hotkeys** for quick access
5. **Start processing text** with AI assistance

## 🔧 System Requirements

- **macOS 10.14** or later
- **Apple Silicon** or Intel Mac
- **Internet connection** for AI features

## 🛡️ Security & Privacy

Potter is:
- ✅ **Code signed** with Apple Developer ID
- ✅ **Notarized** by Apple for security
- ✅ **Privacy compliant** - no data collection without permission

## 📝 License

This software is provided as-is for personal and commercial use.

<<<<<<< HEAD
```
rephrasely/
<<<<<<< HEAD
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
=======
├── 📂 src/                     # 💻 Source code
│   ├── rephrasely.py          # 🚀 Main application
│   ├── settings_ui.py         # 🎛️ Preferences interface
│   └── cocoa_settings.py      # 🍎 macOS UI components
├── 📂 docs/                    # 📖 Documentation
│   ├── DISTRIBUTION.md         # Build system & releases
│   ├── INSTALLATION.md         # Setup instructions
│   ├── UI_GUIDE.md            # Settings interface guide
│   ├── UNINSTALL.md           # Removal instructions
│   └── SETUP_GITHUB_RELEASES.md # Release automation
├── 📂 scripts/                # 🔨 Build & automation scripts
│   ├── build_app.py           # Main app builder
│   ├── setup.py              # Environment setup
│   ├── run.sh                 # Quick run script
│   ├── test_build.sh          # Build testing
│   ├── test_dmg_creation.sh   # DMG testing
│   ├── create_github_release.sh # Release creation
│   └── manual_release.sh      # Manual release trigger
├── 📂 test_scripts/           # 🧪 Testing & debugging
│   ├── debug_test.py          # Debug utilities
│   ├── test_setup.py          # Setup testing
│   ├── test_settings_migration.py # Settings migration test
│   └── test_ui.py             # UI testing
├── 📂 config/                 # ⚙️ Configuration files
│   ├── example_settings.json  # 📝 Sample configuration
│   └── settings.json          # ⚙️ User preferences (auto-created)
├── 📂 assets/                 # Icons & resources
│   └── dmg_background.png     # DMG installer background
├── 📂 dist/                   # 📦 Built artifacts
│   ├── app/                   # Built application
│   ├── dmg/                   # DMG installers
│   └── archives/              # Release archives
├── 📂 .venv/                  # 🐍 Python virtual environment
├── 📂 .github/                # ⚙️ GitHub workflows
│   └── workflows/
│       └── release.yml        # Automated releases
├── requirements.txt           # 📋 Dependencies
└── README.md                  # 📚 Project documentation
```
>>>>>>> f68e635 (trying out signing)
=======
## 🐛 Support

For issues, feature requests, or questions:
- **Create an issue** in this repository
- **Check existing issues** for solutions

## 🔄 Updates

Potter automatically checks for updates and will notify you when new versions are available.

---

**Potter** - Making text processing magical ✨
>>>>>>> db2f5bf (build to potter repo)

# 🎭 Potter

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

## 🐛 Support

For issues, feature requests, or questions:
- **Create an issue** in this repository
- **Check existing issues** for solutions

## 🔄 Updates

Potter automatically checks for updates and will notify you when new versions are available.

## 🛠️ Development

### Building from Source

Potter uses a Makefile for easy development and building:

```bash
# Build signed app with DMG
make build

# Run tests
make test

# Run the app in development mode
make run

# Create a release (builds, tests, creates GitHub release)
make release
```

### Version Management

```bash
# Show current version
make version

# Set specific version
make version-set VERSION=2.0.0

# Bump version numbers
make version-bump-major    # 1.0.0 → 2.0.0
make version-bump-minor    # 1.0.0 → 1.1.0
make version-bump-patch    # 1.0.0 → 1.0.1
```

### Development Commands

```bash
# Show all available commands
make help

# Clean build artifacts
make clean

# Install to Applications folder
make install

# Check dependencies
make deps
```

### Requirements for Building

- **Xcode Command Line Tools**
- **Swift 5.7+**
- **Python 3.8+**
- **Apple Developer ID** (for code signing)
- **GitHub CLI** (for releases)

---

**Potter** - Making text processing magical ✨
# 🎭 Potter

A powerful text processing and rephraseing tool for macOS with AI capabilities.

## 📦 Download

### Latest Release
Download the latest version from the [Releases](https://github.com/jebasingh/potter/releases) page.

### 🔧 Easy Installation
1. Download `Potter.dmg` from the releases page
2. Open the DMG file
3. Drag Potter.app to your Applications folder
4. Launch Potter from Applications

### ⚙️ Prerequisites
- **macOS 10.14+** (Mojave or later)
- **Architecture**: Intel x64 or Apple Silicon
- **Permissions**: Accessibility access for global hotkeys

## ✨ Features

### 🎯 Core Functionality
- **Global hotkey** (⌘⇧9) for instant text processing from any app
- **AI-powered rephraseing** with multiple providers (OpenAI, Anthropic, Google)
- **Clipboard integration** - processes selected text automatically
- **Custom prompts** - Create and manage your own text processing workflows

### 🛡️ Security & Privacy
- **Secure API key storage** in macOS Keychain
- **Local processing** - your text is only sent to your chosen AI provider
- **No data collection** - Potter respects your privacy

### 🎨 User Experience
- **Native macOS app** with menu bar integration
- **Modern SwiftUI interface** with intuitive settings
- **Auto-updates** via Sparkle framework
- **Creative build names** and version codenames

## 🚀 Usage

1. **Setup**: Configure your AI provider and API key in Settings
2. **Select text** anywhere in macOS
3. **Press ⌘⇧9** to process the selected text
4. **Get results** - processed text replaces your selection

### 🔧 Configuration
- Open Potter settings from the menu bar icon
- Choose your preferred AI provider (OpenAI, Anthropic, or Google)
- Add your API key
- Customize prompts and hotkeys

## 🏗️ Development

Potter is built with modern Swift and SwiftUI for macOS.

### 🛠 Build Requirements
- **Xcode 15+** 
- **Swift 5.9+**
- **macOS 13+ SDK**

### 📋 Commands
- **Run app**: `make run` or `cd swift-potter && swift run`
- **Run tests**: `make test` or `cd swift-potter && swift test --parallel`
- **Build app**: `make build` 
- **Create release**: `make release`

### 🏗️ Architecture
- **Core Engine**: `swift-potter/Sources/PotterCore.swift`
- **LLM Integration**: Multiple provider support with unified interface
- **Settings UI**: Native SwiftUI with modern sidebar design
- **Global Hotkeys**: Carbon APIs for system-wide shortcuts
- **Auto Updates**: Sparkle framework integration

## 📄 License

Potter is proprietary software. All rights reserved.

---

**Enjoy your secure, AI-powered text enhancement!** 🚀
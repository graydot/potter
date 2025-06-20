# Potter Changelog

All notable changes to Potter - AI Text Processing Tool for macOS.

## [2.0.0] - June 19, 2025 🎉 Major Swift Release

### 🚀 Complete Platform Migration
- **Swift-native implementation** - Modern macOS app using Swift and AppKit
- **Native Swift Package Manager** - Modern dependency management and build system
- **Professional app bundling** - Proper .app structure with code signing and notarization
- **Removed Python implementation** - Simplified to Swift-only codebase

### 🤖 Multi-LLM Provider Support
- **OpenAI integration** - GPT-4, GPT-3.5-turbo support
- **Anthropic Claude** - Claude-3-5-Sonnet, Claude-3-Haiku support  
- **Google Gemini** - Gemini-1.5-Pro, Gemini-1.5-Flash support
- **Provider switching** - Easy selection between LLM providers in settings
- **Model selection** - Choose specific models for each provider

### 🔐 Secure API Key Storage
- **Keychain integration** - Secure storage using macOS Keychain Services
- **Storage method selection** - User choice between encrypted keychain vs UserDefaults
- **Lock/unlock toggle** - Easy switching between storage methods in settings
- **API key migration** - Seamless transition from Python to Swift storage
- **Multiple keychain prompts fixed** - Intelligent caching to reduce keychain access

### 🎨 Potter-Themed Design System
- **Custom iconography** - Orange pot app icons replacing generic designs
- **Menu bar icons** - Black pot for light mode, white pot for dark mode
- **Animated status indicators** - Processing, success, and error states in menu bar
- **Professional DMG design** - Clean minimal installation background
- **Modern settings UI** - Native SwiftUI components with sidebar design

### ⌨️ Enhanced Hotkey System
- **Default hotkey change** - Cmd+Shift+9 (safer than previous Cmd+Shift+R)
- **Improved hotkey capture** - Visual pill-based interface for hotkey configuration
- **Global hotkey disabling** - Temporarily disable during hotkey setup to prevent interference
- **Reset button enhancement** - Now triggers capture mode like clicking on pills
- **Full number key support** - Support for 0-9 in hotkey combinations

### 🛠 Advanced Features
- **Cool build names** - Fun identifiers like "Potter_Lightning-Falcon_250619213" instead of UUIDs
- **Comprehensive error management** - Robust error states with user-friendly messaging
- **Dynamic prompt system** - JSON-based prompt management with real-time updates
- **Single instance enforcement** - PID-based duplicate detection with user dialogs
- **Permission management** - Direct navigation to system settings with fallback URLs

### 🧪 Testing & Development
- **Swift testing framework** - 82+ comprehensive unit tests with `swift test --parallel`
- **XCTest integration** - Native Swift testing with async/await support
- **Isolated test data** - Tests use separate data instead of live Application Support
- **Real integration testing** - Minimal mocking, actual file I/O and UserDefaults
- **Performance testing** - Fast execution without network calls

---

## [1.2.0] - May 28, 2025 🏗️ Architecture Refactoring

### 🔄 Major Code Restructuring
- **96% size reduction** in main file (1,385 → 60 lines)
- **Modular architecture** - 8 focused modules replacing monolithic structure
- **Separation of concerns** - Clear module boundaries and responsibilities
- **100% backward compatibility** - Same public API and user experience

### 📦 New Modular Components
- `src/core/service.py` - Main service orchestrator (188 lines)
- `src/core/permissions.py` - macOS accessibility management (129 lines)  
- `src/core/hotkeys.py` - Keyboard event processing (211 lines)
- `src/core/text_processor.py` - AI text processing workflows (182 lines)
- `src/ui/tray_icon.py` - System tray management (298 lines)
- `src/ui/notifications.py` - User feedback system (105 lines)
- `src/utils/instance_checker.py` - Single instance management (84 lines)
- `src/utils/openai_client.py` - API client management (133 lines)

### 🧪 Enhanced Testing
- **Comprehensive test runner** - Auto-discovery finding all `test_*.py` files
- **16/16 tests passing** - 100% test success rate
- **Real integration testing** - Actual file I/O, PyObjC objects, JSON processing
- **Minimal mocking** - Tests real component interactions

### 🛡️ Engineering Best Practices
- **Dependency injection** - Components receive dependencies explicitly
- **Interface segregation** - Small, focused interfaces
- **Enhanced error handling** - Comprehensive exception management
- **Professional logging** - Structured logging with multiple output streams

---

## [1.1.0] - May 23-28, 2025 🐛 Stability & Distribution

### 🚀 Distribution System
- **GitHub Releases migration** - Automated release creation and distribution
- **DMG generation** - Professional disk image creation for distribution
- **Code signing infrastructure** - Notarization and distribution certificates
- **Build versioning** - Intelligent build conflict resolution with user dialogs

### 🔧 Critical Bug Fixes
- **App closure issues fixed** - Proper NSObject AppDelegate implementation prevents app termination
- **API key paste functionality** - Switched from NSSecureTextField to NSTextField for Cmd+V support
- **Hotkey detection reliability** - Normalized key representation and improved modifier handling
- **Settings dialog persistence** - Comprehensive save/close solutions with multiple fallbacks

### 🎯 User Experience Improvements  
- **Enhanced settings panels** - Better visual hierarchy and spacing
- **Improved prompt management** - Better prompt editing and validation
- **Logs preference pane** - Added logging configuration interface
- **Notification enhancements** - Better user feedback for success/error states

### 🛠 Development Infrastructure
- **Pre-commit hooks** - Automated testing on every commit
- **Enhanced logging** - Improved debug output and log file management
- **Test coverage expansion** - Additional test scenarios and edge cases
- **Build documentation** - Comprehensive setup and distribution guides

---

## [1.0.0] - May 23, 2025 🎭 Initial Release

### 🎉 Core Features
- **AI text processing** - OpenAI ChatGPT integration for text transformation
- **Global hotkey support** - Cmd+Shift+R for system-wide activation
- **Clipboard-based workflow** - Copy text → hotkey → process → paste
- **System tray integration** - Native macOS menu bar application
- **Single instance enforcement** - PID file management prevents multiple instances

### ⚙️ Settings & Configuration
- **Native macOS settings window** - PyObjC-based NSWindow interface
- **Tabbed interface** - General and Prompts configuration tabs
- **API key management** - Secure storage and configuration
- **Custom prompts system** - User-defined text processing instructions
- **JSON configuration** - Persistent settings storage

### 🏗️ Technical Foundation
- **Python-based implementation** - PyObjC for native macOS integration
- **Threading model** - Non-blocking text processing
- **Error handling** - Comprehensive exception management
- **Logging system** - Debug and operational logging

### 🎨 User Interface
- **System tray icon** - Custom application icon and menu
- **Settings dialog** - Professional configuration interface
- **Prompt editor** - Custom prompt creation and editing
- **Status indicators** - Visual feedback for processing states

---

## Development Timeline

- **May 23, 2025**: Initial Python implementation with core features
- **May 23-28, 2025**: Stability improvements and distribution system
- **May 28 - June 16, 2025**: Major architecture refactoring and modularization  
- **June 16-19, 2025**: Complete Swift migration with advanced features
- **June 19, 2025**: Swift-only release, Python implementation removed

## Breaking Changes

### Version 2.0.0
- **Platform migration** - Moved from Python to Swift implementation
- **Hotkey change** - Default changed from Cmd+Shift+R to Cmd+Shift+9
- **Storage format** - API keys migrated from JSON to Keychain/UserDefaults
- **Multi-LLM** - Added support for Anthropic Claude and Google Gemini

### Version 1.2.0  
- **Architecture change** - Modular structure may affect custom integrations
- **Import paths** - Module locations changed for Python components

## Migration Guide

### From 1.x to 2.0.0
1. **API Keys**: Will be automatically migrated from JSON to new storage system
2. **Hotkeys**: Default changed to Cmd+Shift+9, reconfigure if needed
3. **Settings**: Most settings will be preserved, may need reconfiguration
4. **Prompts**: Custom prompts should be preserved in new JSON format

### From 1.1.x to 1.2.0
- **No breaking changes** - Fully backward compatible
- **Module imports** - Internal module structure changed but public API unchanged

## Features by Version

| Feature | 1.0.0 | 1.1.0 | 1.2.0 | 2.0.0 |
|---------|-------|-------|-------|-------|
| OpenAI Integration | ✅ | ✅ | ✅ | ✅ |
| Anthropic Claude | ❌ | ❌ | ❌ | ✅ |
| Google Gemini | ❌ | ❌ | ❌ | ✅ |
| Global Hotkeys | ✅ | ✅ | ✅ | ✅ |
| Custom Prompts | ✅ | ✅ | ✅ | ✅ |
| Secure Storage | ❌ | ❌ | ❌ | ✅ |
| Swift Implementation | ❌ | ❌ | ❌ | ✅ |
| Modern UI | ❌ | ❌ | ❌ | ✅ |
| Animated Icons | ❌ | ❌ | ❌ | ✅ |
| Code Signing | ❌ | ✅ | ✅ | ✅ |
| Modular Architecture | ❌ | ❌ | ✅ | ✅ |
| Comprehensive Tests | ❌ | ✅ | ✅ | ✅ |

---

*Potter - AI Text Processing Tool for macOS*  
*Developed with ❤️ for the macOS community*
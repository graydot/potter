# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- **Run app**: `cd swift-potter && swift run`
- **Run tests**: `cd swift-potter && swift test --parallel`
- **Test build** (unsigned): `./scripts/test_build.sh`
- **Production build**: `python scripts/build_app.py --target local`
- **App Store build**: `python scripts/build_app.py --target appstore`

### Using Makefile
- **Run app**: `make run`
- **Run tests**: `make test`
- **Build signed app**: `make build`
- **Build unsigned**: `make build-unsigned`

## Architecture

Potter is a macOS tray application that provides AI-powered text processing with global hotkeys (Cmd+Shift+9).

### Core Flow
1. **Service Orchestration**: `swift-potter/Sources/PotterCore.swift` coordinates all components
2. **Global Hotkeys**: Carbon APIs capture Cmd+Shift+9 system-wide
3. **Text Processing**: LLM integration via multiple providers (OpenAI, Anthropic, Google Gemini)
4. **Native UI**: SwiftUI settings window with modern sidebar design
5. **Tray Management**: NSStatusBar integration for system tray presence

### Key Components
- **Entry point**: `swift-potter/Sources/main.swift` - AppDelegate with menu bar management
- **Core Engine**: `swift-potter/Sources/PotterCore.swift` - Global hotkeys and text processing
- **LLM Integration**: `swift-potter/Sources/LLMManager.swift` + `LLMClient.swift` - Multi-provider support
- **Settings UI**: `swift-potter/Sources/ModernSettingsWindow.swift` - Native SwiftUI interface
- **Process Management**: `swift-potter/Sources/ProcessManager.swift` - Duplicate instance detection
- **Permission System**: `swift-potter/Sources/PermissionManager.swift` - macOS permissions
- **Secure Storage**: `swift-potter/Sources/SecureAPIKeyStorage.swift` - Keychain integration

### Build System
- **Swift Package Manager**: Native Xcode toolchain integration
- **Build commands**: `python scripts/build_app.py --target [local|appstore]`
- **Native compilation**: Direct to executable binary
- **Code signing**: Integrated with Xcode build process
- **Testing**: `swift test` and `swift test --parallel` for comprehensive test suite
- **Dual distribution**: Supports both GitHub releases and Mac App Store
- **Intelligent versioning**: Handles multiple build conflicts with user dialogs

### Dependencies & Permissions
- **Native macOS app**: No external runtime dependencies
- **Multi-LLM support**: OpenAI, Anthropic, Google Gemini APIs via native HTTP clients
- **Settings persistence**: UserDefaults and JSON file management
- **Permission management**: Native PermissionManager with direct system integration
- **Critical permissions**: Accessibility (required), Notifications (graceful degradation)
- **Dynamic prompt system**: JSON-based prompt management with real-time updates
- **Secure storage**: Keychain Services integration for API key storage

### Testing Philosophy
- **Comprehensive unit tests**: 82+ tests across all major components
- **XCTest framework**: Native Swift testing with async/await support
- **Real integration**: Minimal mocking, actual file I/O, real UserDefaults
- **Auto-discovery**: Swift Package Manager finds all test files automatically
- **Test coverage**: LLM clients, settings, permissions, process management, core functionality
- **Performance testing**: Fast execution without network calls
- **Commands**: `swift test`, `swift test --parallel`, `make test`

### Development Notes
- **Single instance enforcement**: PID files with build conflict resolution dialogs
- **Build environment variables**: DEVELOPER_ID_APPLICATION, APPLE_TEAM_ID for signing
- **Logging locations**: `swift-potter/potter_debug.log` (dev), `~/Library/Logs/potter.log` (production)
- **Settings storage**: UserDefaults and JSON files in `swift-potter/config/`
- **Project structure**: All Swift code in `swift-potter/` directory

### User Experience Features
- **Global hotkey**: Cmd+Shift+9 for system-wide text processing
- **Native macOS integration**: NSMenu, NSNotifications, accessibility services
- **Permission management**: Direct navigation to system settings with fallback URLs
- **Enhanced settings UI**: Modern SwiftUI sidebar design with keyboard shortcuts (ESC/Cmd+Enter)
- **Build conflict resolution**: User-friendly dialogs when multiple builds detected
- **Secure API storage**: Keychain Services integration with UserDefaults fallback
- **Dynamic prompts**: JSON-based prompt system with real-time updates
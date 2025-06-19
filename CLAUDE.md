# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- **Run tests**: `python run_tests.py`
- **Test build** (unsigned): `./scripts/test_build.sh`
- **Production build**: `python scripts/build_app.py --target github`
- **App Store build**: `python scripts/build_app.py --target appstore`

### Swift Potter (New)
- **Run Swift tests**: `cd swift-potter && swift test`
- **Build Swift app**: `python scripts/build_swift_app.py --target local`
- **Swift App Store build**: `python scripts/build_swift_app.py --target appstore`

### Testing
- **All tests**: `python run_tests.py` or `python tests/auto_test_runner.py`
- **Single test file**: `python tests/test_enhanced_settings.py`
- **Swift tests**: `cd swift-potter && swift test --parallel`

## Architecture

Potter is a macOS tray application that provides AI-powered text processing with global hotkeys (Cmd+Shift+R).

### Python Version (Legacy)
The original Python implementation, now deprecated in favor of Swift.

#### Core Flow
1. **Service Orchestration**: `src/core/service.py` coordinates all components
2. **Global Hotkeys**: `src/core/hotkeys.py` captures Cmd+Shift+R system-wide
3. **Text Processing**: `src/core/text_processor.py` handles AI interactions via multiple LLM providers
4. **Native UI**: `src/cocoa_settings.py` provides macOS-native settings window with sidebar design
5. **Tray Management**: `src/ui/tray_icon.py` handles system tray presence

#### Key Components
- **Entry point**: `src/potter.py` (60 lines)
- **Settings management**: `src/settings/settings_manager.py`
- **Multi-LLM integration**: `src/utils/llm_client.py` (supports OpenAI, Anthropic, Google Gemini)
- **Build versioning**: `src/utils/instance_checker.py` with intelligent conflict resolution

### Swift Version (Current)
The Swift rewrite provides native macOS performance and better system integration.

#### Core Architecture
- **Native Swift Package**: `swift-potter/Package.swift` targeting macOS 13+
- **Main Entry**: `Sources/main.swift` (290 lines) - AppDelegate with menu bar management
- **Core Engine**: `Sources/PotterCore.swift` (204 lines) - Global hotkeys and text processing
- **LLM Integration**: `Sources/LLMManager.swift` + `LLMClient.swift` (588 lines total)
- **Settings UI**: `Sources/ModernSettingsWindow.swift` (998 lines) - Native SwiftUI interface
- **Process Management**: `Sources/ProcessManager.swift` (237 lines) - Duplicate detection
- **Permission System**: `Sources/PermissionManager.swift` (361 lines) - macOS permissions

#### Swift Component Summary
- **Total**: 4,144 lines across 13 Swift files
- **Average**: 318 lines per component
- **Largest**: ModernSettingsWindow.swift (998 lines) - comprehensive settings UI
- **Core modules**: Well-structured with clear separation of concerns

#### Testing Infrastructure
- **82 comprehensive unit tests** across 7 test files
- **XCTest framework** with async/await support
- **Real integration testing** - minimal mocking, actual file I/O
- **Test commands**: `swift test`, `swift test --parallel`, `./run_tests.sh`

### Refactored Architecture
Originally a monolithic 1,385-line Python file, now available in two implementations:
- **Python**: 96% size reduction (1,385 → 60 lines) with 8 focused components
- **Swift**: Native rewrite with 4,144 lines across 13 focused modules
- **100% backward compatibility** maintained between versions

### Build System

#### Python Build System (Legacy)
- **PyInstaller-based**: Creates standalone app bundles with unique build IDs
- **Code signing required**: All production builds must be signed and notarized
- **Dual distribution**: Supports both GitHub releases and Mac App Store
- **Intelligent versioning**: Handles multiple build conflicts with user dialogs

#### Swift Build System (Current)
- **Swift Package Manager**: Native Xcode toolchain integration
- **Build commands**: `python scripts/build_swift_app.py --target [local|appstore]`
- **Native compilation**: Direct to executable binary
- **Code signing**: Integrated with Xcode build process
- **Testing**: `swift test` and `swift test --parallel` for comprehensive test suite

### Dependencies & Permissions

#### Python Version (Legacy)
- **Python application** requiring macOS accessibility permissions for global hotkeys
- **Multi-LLM support**: OpenAI, Anthropic, Google Gemini APIs
- **Settings persistence**: Application Support for app bundles, config/ for development
- **Critical permissions**: Accessibility (required), Notifications (graceful degradation)

#### Swift Version (Current)
- **Native macOS app**: No external runtime dependencies
- **Multi-LLM support**: OpenAI, Anthropic, Google Gemini APIs via native HTTP clients
- **Settings persistence**: UserDefaults and JSON file management
- **Permission management**: Native PermissionManager with direct system integration
- **Critical permissions**: Accessibility (required), Notifications (graceful degradation)
- **Dynamic prompt system**: JSON-based prompt management with real-time updates

### Testing Philosophy

#### Python Testing (Legacy)
- **Minimal mocking**: Tests use real file I/O, actual PyObjC objects, real JSON processing
- **Auto-discovery**: Test runner finds all `test_*.py` files automatically
- **100% test success rate**: 30+ tests across 6 test suites
- **Real integration**: Tests actual component interaction vs mocked behavior

#### Swift Testing (Current)
- **82 comprehensive unit tests** across all major components
- **XCTest framework**: Native Swift testing with async/await support
- **Real integration**: Minimal mocking, actual file I/O, real UserDefaults
- **Auto-discovery**: Swift Package Manager finds all test files automatically
- **Test coverage**: LLM clients, settings, permissions, process management, core functionality
- **Performance testing**: Fast execution without network calls

### Development Notes
- **Single instance enforcement**: PID files with build conflict resolution dialogs
- **Build environment variables**: DEVELOPER_ID_APPLICATION, APPLE_TEAM_ID for signing
- **Logging locations**: `potter.log` (dev), `~/Library/Logs/potter.log` (production)
- **Settings storage**: App bundles use Application Support, development uses config/

### User Experience Features
- **Global hotkey**: Cmd+Shift+R for system-wide text processing
- **Native macOS integration**: NSMenu, NSNotifications, accessibility services
- **Permission management**: Direct navigation to system settings with fallback URLs
- **Enhanced settings UI**: Modern sidebar design with keyboard shortcuts (ESC/Cmd+Enter)
- **Build conflict resolution**: User-friendly dialogs when multiple builds detected
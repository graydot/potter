# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- **Run tests**: `python run_tests.py`
- **Test build** (unsigned): `./scripts/test_build.sh`
- **Production build**: `python scripts/build_app.py --target github`
- **App Store build**: `python scripts/build_app.py --target appstore`

### Testing
- **All tests**: `python run_tests.py` or `python tests/auto_test_runner.py`
- **Single test file**: `python tests/test_enhanced_settings.py`

## Architecture

Potter is a macOS tray application that provides AI-powered text processing with global hotkeys (Cmd+Shift+R).

### Core Flow
1. **Service Orchestration**: `src/core/service.py` coordinates all components
2. **Global Hotkeys**: `src/core/hotkeys.py` captures Cmd+Shift+R system-wide
3. **Text Processing**: `src/core/text_processor.py` handles AI interactions via multiple LLM providers
4. **Native UI**: `src/cocoa_settings.py` provides macOS-native settings window with sidebar design
5. **Tray Management**: `src/ui/tray_icon.py` handles system tray presence

### Key Components
- **Entry point**: `src/potter.py` (60 lines)
- **Settings management**: `src/settings/settings_manager.py`
- **Multi-LLM integration**: `src/utils/openai_client.py` (supports OpenAI, Anthropic, Google Gemini)
- **Build versioning**: `src/utils/instance_checker.py` with intelligent conflict resolution

### Refactored Architecture
Originally a monolithic 1,385-line file, now modularized into 8 focused components:
- **96% size reduction** in main file (1,385 → 60 lines)
- **Core modules** average 162 lines each
- **100% backward compatibility** maintained

### Build System
- **PyInstaller-based**: Creates standalone app bundles with unique build IDs
- **Code signing required**: All production builds must be signed and notarized
- **Dual distribution**: Supports both GitHub releases and Mac App Store
- **Intelligent versioning**: Handles multiple build conflicts with user dialogs

### Dependencies & Permissions
- **Python application** requiring macOS accessibility permissions for global hotkeys
- **Multi-LLM support**: OpenAI, Anthropic, Google Gemini APIs
- **Settings persistence**: Application Support for app bundles, config/ for development
- **Critical permissions**: Accessibility (required), Notifications (graceful degradation)

### Testing Philosophy
- **Minimal mocking**: Tests use real file I/O, actual PyObjC objects, real JSON processing
- **Auto-discovery**: Test runner finds all `test_*.py` files automatically
- **100% test success rate**: 30+ tests across 6 test suites
- **Real integration**: Tests actual component interaction vs mocked behavior

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
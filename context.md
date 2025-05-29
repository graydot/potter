# Potter - Project Context & Background

## Project Overview
Potter is a macOS productivity app for AI-powered text processing using OpenAI's API. Originally called "Rephrasely," it provides system-wide text enhancement via global hotkeys.

## Key Functionality

- **Global Hotkey Processing**: Uses Cmd+Shift+R to capture selected text system-wide
- **AI Text Processing**: Integrates with OpenAI API for text enhancement and rephrasing
- **Menu Bar Interface**: Native macOS menu bar application with dropdown settings
- **Custom Prompts**: Users can add/edit custom processing prompts
- **Notification System**: Shows processing completion notifications

## Distribution Strategy

### Regular Distribution
- **Target**: Direct distribution outside App Store
- **Signing**: Developer ID certificates for notarization
- **Permissions**: Full accessibility permissions for global hotkeys
- **Build**: `Potter.spec` with standard entitlements

### Mac App Store Distribution
- **Target**: Official App Store submission
- **Signing**: App Store certificates (3rd Party Developer)
- **Limitations**: Sandboxed environment, limited accessibility access
- **Build**: `Potter-AppStore.spec` with App Store entitlements
- **Note**: Global hotkeys may not be approved by App Store review

## Technical Architecture

### Core Technologies
- **Python**: Main application logic
- **PyObjC**: Native macOS integration (NSMenu, NSNotifications, etc.)
- **PyInstaller**: App bundle creation
- **pystray**: Menu bar integration
- **OpenAI API**: Text processing backend

### macOS Integration
- **Accessibility Services**: Required for global hotkey capture
- **User Notifications**: Native macOS notification system
- **Hardened Runtime**: Security compliance for code signing
- **App Sandbox**: Required for App Store submission

## Permission Requirements

### Accessibility Permission
- **Purpose**: Capture global keyboard events (Cmd+Shift+R)
- **Critical**: App cannot function without this permission
- **User Experience**: Clear error messaging when permission missing
- **Implementation**: Automatic detection and guidance in settings

### Notification Permission
- **Purpose**: Show processing completion notifications
- **Behavior**: Graceful degradation when denied
- **Detection**: Monitors system Do Not Disturb/Focus mode status
- **Implementation**: Runtime permission checking with status display

## Developer Preferences & Style Guidelines

### Communication Style
- **Clarity**: Prefers direct, actionable communication over verbose explanations
- **Visual Aids**: Appreciates emoji usage for step-by-step guidance (🔧, ✅, ❌, etc.)
- **Thoroughness**: Values comprehensive solutions that handle edge cases
- **Results-Oriented**: Prefers solutions that "just work" without requiring user intervention

### Code Quality Standards
- **Defensive Programming**: Strong preference for robust error handling (try/catch/finally patterns)
- **User Experience Focus**: Prioritizes intuitive interfaces and smooth user interactions
- **Minimal Redundancy**: Dislikes duplicate UI elements (e.g., removing redundant checkmarks)
- **Comprehensive Coverage**: Prefers solutions that address multiple related issues simultaneously
- **Clean Organization**: Values well-structured, readable code with logical organization

### Problem-Solving Approach
- **Root Cause Analysis**: Prefers understanding underlying issues rather than surface fixes
- **Edge Case Consideration**: Wants solutions that handle unexpected scenarios gracefully
- **Multiple Execution Prevention**: Values protection against race conditions and simultaneous operations
- **System Integration**: Appreciates deep integration with native platform capabilities
- **Future-Proofing**: Considers long-term maintainability and extensibility

### UI/UX Philosophy
- **Native Feel**: Strongly prefers native macOS UI components over custom implementations
- **Logical Grouping**: Wants related features organized together (e.g., notifications near accessibility)
- **Real-time Feedback**: Values immediate status updates and permission state display
- **Graceful Degradation**: Prefers apps that work well even when some features are unavailable
- **Minimal User Friction**: Wants automated setup and configuration where possible

### Testing & Validation
- **Real-world Testing**: Prefers testing across actual user scenarios and edge cases
- **Permission States**: Values thorough testing of different system permission configurations
- **Error Scenarios**: Wants comprehensive testing of failure modes and recovery
- **Performance Validation**: Appreciates attention to responsiveness and resource usage

## Development History & Decisions

### Repository Migration
- Original "Rephrasely" repository became private/inaccessible
- Complete rebrand to "Potter" required updating all user-facing references
- New repository created for publishing releases only. Development still happens in rephrasely workspace but all user-facing elements use "Potter" branding

### UI/UX Improvements
- **Menu Organization**: Notifications moved next to accessibility for logical grouping
- **Permission Feedback**: Real-time status display for system permissions
- **Error Handling**: Robust dialog management with guaranteed closure
- **Multiple Execution Prevention**: Protection against simultaneous hotkey triggers

### Build Process Evolution
- **Automated Builds**: Scripts for both regular and App Store builds
- **Code Signing**: Separate certificate handling for different distribution methods
- **Environment Management**: Secure credential storage for signing process
- **DMG Creation**: Automated disk image creation for distribution

## User Experience Considerations

### Onboarding
- **Permission Setup**: Clear guidance for required accessibility permissions
- **Initial Configuration**: OpenAI API key setup and testing
- **Hotkey Training**: User education on Cmd+Shift+R usage

### Error Handling
- **Network Failures**: Graceful API error handling
- **Permission Issues**: Clear messaging and resolution steps
- **System Compatibility**: macOS version checking and warnings

### Performance
- **Hotkey Responsiveness**: Fast text capture and processing initiation
- **Background Processing**: Non-blocking API calls with progress indication
- **Memory Management**: Efficient handling of text processing and clipboard operations

## Security & Privacy

### Data Handling
- **Local Storage**: Settings stored in Application Support directory
- **API Communication**: Direct encrypted communication with OpenAI
- **Clipboard Access**: Temporary clipboard usage for text capture
- **No Data Retention**: Processed text not stored locally

### Code Signing
- **Developer ID**: For direct distribution and notarization
- **App Store Certificates**: For App Store submission
- **Hardened Runtime**: Security compliance requirements
- **Entitlements**: Minimal permissions for functionality

## Known Limitations

### App Store Version
- **Global Hotkeys**: May not be approved by App Store review team
- **Accessibility Access**: Limited by sandbox restrictions
- **Alternative UX**: May require different interaction model for App Store

### System Dependencies
- **macOS Version**: Minimum 10.14.0 (Mojave) required
- **Accessibility API**: Dependent on macOS accessibility framework
- **Network Access**: Requires internet connection for AI processing

## Future Considerations

### Feature Expansion
- **Multiple Hotkeys**: Support for different processing modes
- **Local AI Models**: Reduce dependency on external APIs
- **Text History**: Optional processing history with user control
- **Custom Integrations**: Plugin system for third-party text processors

### Distribution
- **Auto-Updates**: Implement automatic update mechanism
- **Beta Testing**: TestFlight for App Store beta distribution
- **Enterprise**: Consideration for enterprise deployment options

## Development Environment

### Build Requirements
- **Python 3.x**: Core runtime environment
- **Virtual Environment**: Isolated dependency management
- **Xcode Command Line Tools**: Required for macOS development
- **Apple Developer Account**: Required for code signing and distribution

### Testing Strategy
- **Permission Testing**: Manual testing across different permission states
- **System Integration**: Testing across macOS versions and configurations
- **API Integration**: Mocking and testing OpenAI API interactions
- **UI Testing**: Manual testing of native macOS UI components

## Current Status
- **Refactored Architecture**: Successfully modularized from monolithic `potter.py` (1,385 lines) into 8 focused modules
- **Modern Settings UI**: Implemented sidebar navigation with SF Symbols, NSSwitch controls, and improved visual hierarchy
- **PyObjC Fixes**: Resolved method naming conflicts by moving helper functions outside NSWindowController class
- **Build Configuration**: App requires signing and notarization (user preference)
- **Testing Strategy**: Added real integration tests to catch actual issues vs heavily mocked tests

## Recent Fixes
- **Settings UI**: Fixed PyObjC BadPrototypeError by moving `create_section_header`, `create_section_separator`, `create_modern_switch`, and `create_sidebar_button` functions outside the SettingsWindow class
- **Preferences Integration**: Fixed `_show_preferences` method to use correct `show_settings(settings_manager)` function call
- **Window Initialization**: Fixed settings window not opening due to initialization order issues in `createSidebarFooter()` method
- **Missing References**: Added `log_status_label` and other missing UI elements to prevent runtime errors

## Testing Analysis

### Heavily Mocked Tests Identified:
1. **`tests/test_app_integration.py`**:
   - `test_startup_opens_settings_no_api_key()` - Mocks entire UI layer and permission system
   - `test_service_creation()` - Creates service but doesn't verify it actually works
   - Problem: These tests mock away critical integration points

2. **`tests/test_ui_components.py`**:
   - All tests avoid actual UI components, testing only business logic
   - `test_settings_dialog_*` - Tests file I/O, not actual NSWindow dialogs
   - Problem: Logic tests disguised as UI tests

### Real Integration Tests Added:
Created `tests/test_real_integration.py` with minimal mocking:
- **Real Settings Window Creation** - Actually instantiates NSWindowController
- **Real PyObjC Integration** - Verifies PyObjC method binding works
- **Real Component Imports** - Tests all modules import without crashes
- **Real Settings Persistence** - Verifies file I/O and data persistence
- **Real API Key Detection** - Tests OpenAI client availability logic
- **Real Service Integration** - Verifies method existence and structure

**Results**: 6/6 tests passing - Catches real issues that mocked tests miss

## App Logging Locations
When the app is running and you need to check logs:

**For Development (script mode)**:
- Main logs: `potter.log` in project root
- Console output: Terminal where you ran the script

**For Production (.app bundle)**:
- System logs: `~/Library/Logs/potter.log`
- Console.app: Search for "Potter" in system logs
- Terminal: `tail -f ~/Library/Logs/potter.log`

**Debugging crashes**:
- Crash reports: `~/Library/Logs/DiagnosticReports/Potter*`
- System log: Console.app → System Reports

The app logs startup, permission checks, API calls, errors, and settings changes.

## Build Commands
- **Development Build**: `python scripts/build_app.py` (includes signing and notarization)
- **Production Build**: `python scripts/build_app.py` (includes signing and notarization)
- **Auto-quarantine Removal**: All builds automatically remove quarantine attributes for immediate testing

## Architecture Overview

### Core Modules (src/core/):
- `service.py` (339 lines) - Main PotterService orchestrator
- `permissions.py` (140 lines) - macOS accessibility permission management  
- `hotkeys.py` (226 lines) - Hotkey parsing, detection, and keyboard events
- `text_processor.py` (206 lines) - Clipboard operations and processing workflows

### UI Modules (src/ui/):
- `tray_icon.py` (323 lines) - System tray icon and menu management
- `notifications.py` (113 lines) - System notifications and user feedback

### Utils Modules (src/utils/):
- `instance_checker.py` (84 lines) - Single application instance management
- `openai_client.py` (156 lines) - OpenAI API integration and text processing

### Main Entry Point:
- `potter.py` (60 lines) - Clean main entry point

### Settings UI:
- `cocoa_settings.py` (2,286 lines) - Native macOS settings UI with modern sidebar design

## Test Coverage
- **Integration Tests**: 8/8 passing (test_app_integration.py)
- **UI Component Tests**: 8/8 passing (test_ui_components.py)
- **Total Success Rate**: 100% (16/16 tests passing)

## Key Metrics
- **Main file reduction**: 96% (1,385 → 57 lines)
- **Modularity**: 1 monolithic file → 8 focused modules  
- **Largest module reduction**: 78% (1,385 → 339 lines)
- **Average module size**: 162 lines (88% reduction from original)
- **Backward compatibility**: 100% maintained

## Dependencies
- PyObjC for native macOS UI
- OpenAI API for text processing
- pynput for global hotkey detection
- PyInstaller for app bundling

## Next Steps
- Continue with production builds including signing and notarization
- Monitor app performance and user feedback
- Consider additional UI enhancements based on user needs

---

*This document captures project context that cannot be deduced from code alone. Update as the project evolves.* 
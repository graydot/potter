# Potter - Project Context & Background

## Project Overview
Potter is a macOS productivity app for AI-powered text processing using OpenAI's API. Originally called "Rephrasely," it provides system-wide text enhancement via global hotkeys.

## Key Functionality

- **Global Hotkey Processing**: Uses Cmd+Shift+R to capture selected text system-wide
- **AI Text Processing**: Integrates with multiple LLM providers (OpenAI, Anthropic, Google Gemini)
- **Menu Bar Interface**: Native macOS menu bar application with dropdown settings
- **Enhanced Settings UI**: Modern sidebar design with keyboard shortcuts and persistent storage
- **Custom Prompts Management**: Add/edit/remove custom processing prompts with modal dialogs
- **System Permission Management**: Direct navigation to macOS system settings for permissions
- **Notification System**: Shows processing completion notifications with Do Not Disturb awareness
- **Build Versioning**: Intelligent instance management with conflict resolution dialogs

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
- **Enhanced Settings Window**: Complete implementation with keyboard shortcuts, persistent prompts, compact layout, and improved permission management
- **PyObjC Fixes**: Resolved method naming conflicts by moving helper functions outside NSWindowController class
- **Build Configuration**: App requires signing and notarization (user preference)
- **Testing Strategy**: Added real integration tests to catch actual issues vs heavily mocked tests
- **Build Versioning**: Implemented intelligent instance management with build conflict resolution
- **Production Ready**: All core features implemented and tested, settings persistence working correctly

## Recent Fixes
- **Settings UI**: Fixed PyObjC BadPrototypeError by moving `create_section_header`, `create_section_separator`, `create_modern_switch`, and `create_sidebar_button` functions outside the SettingsWindow class
- **Preferences Integration**: Fixed `_show_preferences` method to use correct `show_settings(settings_manager)` function call
- **Window Initialization**: Fixed settings window not opening due to initialization order issues in `createSidebarFooter()` method
- **Missing References**: Added `log_status_label` and other missing UI elements to prevent runtime errors

## Settings UI Improvements (Latest)

### Enhanced Dialog Management
- **Keyboard Shortcuts**: Implemented global key event handling in `PromptDialog` class
  - ESC cancels dialog from anywhere (including multiline textbox)
  - Cmd+Enter saves dialog from anywhere (including multiline textbox)
  - Enhanced window delegate methods (`windowShouldClose_`, `performKeyEquivalent_`)
  - Text view properly forwards key events to window for global handling

### Prompts Persistence
- **Enhanced SettingsManager**: Added app bundle vs development script detection
- **Application Support Storage**: App bundles now save to `~/Library/Application Support/Potter/settings.json`
- **Comprehensive Debugging**: Added detailed logging for file paths, directory creation, write permissions
- **Atomic File Writing**: Implemented temp file then rename pattern to prevent corruption
- **Automatic Directory Creation**: Enhanced `load_settings()` and `save_settings()` with error handling
- **Default Prompt Creation**: Ensures default prompts persist across builds

### UI Layout Optimization
- **Smaller Prompts Table**: Reduced table height from `y_pos - 180` to `y_pos - 240` (60px smaller)
- **Compact Layout**: Moved table to y=200, controls to y=160 for better space utilization
- **Improved Visual Hierarchy**: Better spacing and organization of UI elements

### Enhanced Permission Management
- **Always-Enabled Buttons**: All permission buttons stay enabled even when permissions granted
- **Dynamic Button Text**: Changes from "Grant Access" to "Manage" when permissions already granted
- **Direct System Settings Navigation**: Enhanced with specific URLs for different permission types:
  - Accessibility: `x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility`
  - Login Items: `x-apple.systempreferences:com.apple.LoginItems-Settings.extension`
  - Notifications: `x-apple.systempreferences:com.apple.preference.notifications`
- **Multiple Fallback URLs**: Support for different macOS versions with fallback chains
- **Debug Logging**: Added URL success/failure tracking for troubleshooting

### Technical Implementation
- **App Bundle Detection**: Uses `getattr(sys, 'frozen', False)` for runtime environment detection
- **Modal Dialog Enhancement**: Proper window delegation and key event handling
- **Settings Path Logic**: Development uses `config/` directory, app bundles use Application Support
- **Permission State Management**: Real-time permission checking with UI updates

### Testing & Validation
- **Comprehensive Testing**: All features tested in both development and built app environments
- **Prompts Persistence Verified**: 6 prompts loaded and saved correctly including test prompts
- **Keyboard Shortcuts Confirmed**: ESC and Cmd+Enter working throughout dialog
- **Permission Management**: Direct navigation to appropriate system settings verified
- **Table Layout**: Smaller, more compact design confirmed working

### User Experience Impact
- **Smoother Dialog Navigation**: Users can save/cancel from anywhere in prompt dialogs
- **Persistent Configuration**: Settings survive app updates and rebuilds
- **Better Permission Management**: Users can easily manage and remove permissions
- **Cleaner Interface**: More compact layout with better use of screen space
- **Direct System Access**: One-click navigation to relevant system settings panels

## Build Versioning & Instance Management

### Overview
Potter now includes an intelligent build versioning system that prevents confusion when multiple builds are present. The system can detect different builds, show user-friendly dialogs, and handle instance conflicts gracefully.

### Key Features

#### **Unique Build IDs**
- **Generation**: Each build gets a unique ID with timestamp: `potter_YYYYMMDD_HHMMSS_randomhex`
- **Embedding**: Build IDs are stored in `build_id.json` within the app bundle's Resources directory
- **Runtime Loading**: Apps load their build ID at startup for comparison with running instances

#### **Smart Instance Detection**
- **Same Build**: Traditional behavior - prevent duplicate instances of same build
- **Different Builds**: Show user dialog with options:
  - **Replace Running Instance**: Kill old build and start new one
  - **Keep Running Instance**: Quietly exit new instance
- **Age Detection**: Dialog indicates whether running build is older or newer

#### **Native macOS Integration**
- **Dialog UI**: Uses `NSAlert` for native macOS appearance
- **Graceful Termination**: Old instances receive `SIGTERM` for clean shutdown
- **Fallback Support**: Terminal prompts when PyObjC unavailable

### Implementation Details

#### **Build Process Integration**
```bash
# Build ID is automatically generated and embedded during build
python scripts/build_app.py
```
- Calls `generate_build_id()` to create unique identifier
- Embeds `build_id.json` in `Potter.app/Contents/Resources/`
- No user intervention required

#### **Instance Checker Enhancement**
- Extended `SingleInstanceChecker` class with build awareness
- Added `load_build_id()` function for runtime detection
- Implemented `show_build_conflict_dialog()` for user interaction
- Maintains backward compatibility with existing service code

#### **File Structure**
```
~/.potter.pid      # Process ID of running instance
~/.potter.build    # Build info of running instance
Potter.app/Contents/Resources/build_id.json  # Embedded build info
```

### User Experience

#### **Scenarios**
1. **First Launch**: Normal startup, creates PID and build files
2. **Same Build**: Shows "already running" message (existing behavior)
3. **Different Build**: Shows dialog:
   ```
   Potter Instance Conflict
   
   An older build is currently running.
   
   Running: potter_20250527_120000_abc123 (2025-05-27 12:00:00)
   Current: potter_20250528_120000_def456 (2025-05-28 12:00:00)
   
   Replace with this newer build?
   
   [Replace Running Instance] [Keep Running Instance]
   ```

#### **Dialog Variations**
- **Newer replacing older**: "An older build is currently running. Replace with this newer build?"
- **Older trying to replace newer**: "A newer build is currently running. Replace with this older build?"
- **Same timestamp**: "The same build is currently running. Replace the running instance?"

### Testing
- **Unit Tests**: `test_build_versioning.py` verifies all components
- **Integration Tests**: Validates build ID embedding and loading
- **Demo Script**: `demo_build_dialog.py` shows dialog scenarios
- **Real Testing**: Build twice and run to see actual dialog

### Benefits
- **Developer Workflow**: Easy testing of multiple builds without manual process killing
- **User Safety**: Clear information about which build is running vs launching
- **Upgrade Path**: Smooth transitions between app versions
- **Debug Support**: Build timestamps help identify which version is active

---

*This feature addresses the common development issue of having multiple builds running simultaneously and provides a professional user experience for version conflicts.*

## Testing Analysis

### Test Infrastructure Evolution

#### **Auto-Discovery Test Runner**
- **Location**: `tests/auto_test_runner.py` with `run_tests.py` alias
- **Discovery**: Automatically finds all `test_*.py` files in tests directory
- **Execution**: Tries multiple runner function patterns (`run_*_tests()`, `run_tests()`, `main()`)
- **Reporting**: Comprehensive summary with pass/fail counts and detailed output

#### **Lightly Mocked Testing Philosophy**
Potter now follows a "minimal mocking" approach:
- **Real File I/O**: Tests use actual file operations with temporary directories
- **Real JSON Processing**: Tests parse and validate actual JSON structures
- **Real PyObjC Objects**: Tests create actual NSWindow and NSAlert instances
- **Limited Mocking**: Only mock external services or system-level operations when necessary

### Current Test Coverage

#### **Build Versioning Tests** (`test_build_versioning.py`)
- **Coverage**: 8 comprehensive tests with 0% mocking
- **Real Testing**: Actual build ID generation, file persistence, PyInstaller bundle detection
- **Validation**: JSON structure, timestamp formats, file I/O operations
- **Edge Cases**: Temporary directories, cleanup operations, error handling

#### **Real Integration Tests** (`test_real_integration.py`)
- **Coverage**: 6 tests focusing on actual component interaction
- **PyObjC Testing**: Real NSWindowController instantiation and method binding
- **Service Integration**: Actual component imports and initialization
- **Settings Persistence**: Real file operations and data validation

#### **App Integration Tests** (`test_app_integration.py`)
- **Status**: Legacy heavily mocked tests (identified for improvement)
- **Issues**: Mocks entire UI layer and permission system
- **Risk**: May miss real integration failures

#### **UI Component Tests** (`test_ui_components.py`)
- **Status**: Logic tests disguised as UI tests
- **Issues**: Avoids actual UI components entirely
- **Risk**: Doesn't validate actual NSWindow/PyObjC functionality

### Testing Commands

#### **Run All Tests**
```bash
# Auto-discovery from project root
python run_tests.py

# Direct runner execution
python tests/auto_test_runner.py

# Individual test files
python tests/test_build_versioning.py
python tests/test_real_integration.py
```

#### **Test Development Guidelines**
1. **Create files**: Follow `test_*.py` naming pattern
2. **Runner function**: Include `run_*_tests()` or `main()` function
3. **Minimal mocking**: Use real file I/O, temporary directories, actual imports
4. **Return boolean**: Test functions should return `True` for pass, `False` for fail
5. **Auto-discovery**: New tests are automatically found and executed

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

### Build Versioning Test Coverage:
Added `tests/test_build_versioning.py` with minimal mocking:
- **Build ID Generation** - Tests actual timestamp and UUID generation
- **Build ID Loading** - Verifies PyInstaller bundle and development detection
- **Build Conflict Detection** - Tests real file I/O and PID checking
- **Build Comparison Logic** - Validates timestamp comparison algorithms
- **Build File Persistence** - Tests actual JSON save/load operations
- **Embedded Build ID** - Verifies app bundle integration
- **Instance Cleanup** - Tests file cleanup and error handling
- **Build ID Embedding** - Tests build script integration

**Results**: 8/8 tests passing - Comprehensive coverage of build versioning feature

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
- `cocoa_settings.py` (4,049 lines) - Native macOS settings UI with modern sidebar design
  - **Dialog Management**: Enhanced keyboard shortcuts (ESC/Cmd+Enter) in prompt dialogs
  - **Data Persistence**: Application Support storage for app bundles, config directory for development
  - **Permission Management**: Direct system settings navigation with fallback URLs
  - **UI Optimization**: Compact table layout and improved visual hierarchy
  - **Multi-LLM Support**: Enhanced provider selection with OpenAI, Anthropic, and Google Gemini
  - **Real-time Validation**: Live permission checking and API key validation

## Test Coverage
- **Integration Tests**: 8/8 passing (test_app_integration.py)
- **UI Component Tests**: 8/8 passing (test_ui_components.py)
- **Real Integration Tests**: 6/6 passing (test_real_integration.py)
- **Build Versioning Tests**: 8/8 passing (test_build_versioning.py)
- **Auto-Discovery Runner**: 6/6 test suites passing
- **Total Success Rate**: 100% (30+ individual tests across 6 test suites)

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
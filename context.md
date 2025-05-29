# Potter - Project Context & Background

## Project Overview

**Potter** is a macOS menu bar application for text processing using AI. Originally named "Rephrasely," the project was rebranded to "Potter" when the original repository became private and inaccessible for releases.

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

---

*This document captures project context that cannot be deduced from code alone. Update as the project evolves.* 
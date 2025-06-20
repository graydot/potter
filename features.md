# Potter Features Documentation

Comprehensive documentation of all features in Potter v2.0.0 - AI Text Processing Tool for macOS.

## 🎯 Core Features

### 1.1 AI Text Processing Pipeline
**Files**: `PotterCore.swift`, `main.swift`

**Purpose**: Transform text using AI with global hotkey activation

**How it Works**:
1. User copies text and presses global hotkey (⌘⇧9)
2. App captures clipboard content and validates it
3. Sends text to selected LLM provider with chosen prompt
4. Replaces clipboard with AI-processed result
5. User can paste the transformed text anywhere

**Key Components**:
- `processClipboardText()` - Main entry point triggered by hotkey
- `performTextProcessing()` - Core processing logic with error handling
- Clipboard validation (non-empty, not our own messages)
- Progress indication via menu bar icon states

**Error Handling**:
- Empty clipboard detection with user messaging
- LLM API failures with graceful degradation
- Network connectivity issues
- Invalid API key handling

---

### 1.2 Multi-LLM Provider Support
**Files**: `LLMClient.swift`, `LLMManager.swift`

**Supported Providers**:

#### OpenAI
- **Models**: o1-mini, o1-preview, GPT-4o, GPT-4o-mini, GPT-4.0-turbo, GPT-3.5-turbo
- **API**: Chat Completions endpoint
- **Validation**: Model-specific validation endpoint

#### Anthropic Claude
- **Models**: Claude-3-5-Sonnet, Claude-3-5-Haiku, Claude-3-Opus, Claude-3-Sonnet, Claude-3-Haiku
- **API**: Messages endpoint with proper headers
- **Validation**: Real-time API key testing

#### Google Gemini
- **Models**: Gemini-1.5-Pro, Gemini-1.5-Flash, Gemini-1.0-Pro
- **API**: GenerateContent endpoint
- **Validation**: Model availability checking

**Provider Management**:
- Dynamic model selection per provider
- Real-time API key validation with async/await
- Automatic provider/model persistence
- Graceful error handling for all providers

**Key Methods**:
- `validateAndSaveAPIKey()` - Async validation with UI feedback
- `processText()` - Unified text processing interface
- `selectProvider()` / `selectModel()` - Dynamic switching
- `hasValidProvider()` - Configuration validation

---

### 1.3 Global Hotkey System
**Files**: `PotterCore.swift`

**Default Configuration**: ⌘⇧9 (Command+Shift+9)

**Technology**: Carbon Event Manager for system-wide capture

**Capabilities**:
- **Full Keyboard Support**: A-Z, 0-9, all modifier keys
- **Custom Combinations**: User-configurable through settings
- **Conflict Detection**: System shortcut validation
- **Dynamic Updates**: Live hotkey changes without restart

**Key Components**:
- `setupGlobalHotkey()` - Initial registration with Carbon Events
- `updateHotkey()` - Runtime hotkey modification
- `parseHotkeyCombo()` - Key combination parsing (supports all keys)
- `disableGlobalHotkey()` / `enableGlobalHotkey()` - Temporary suspension

**Accessibility Integration**:
- Requires macOS Accessibility permissions
- Automatic permission checking and user guidance
- Graceful degradation when permissions denied

**Storage**: UserDefaults persistence for custom combinations

---

### 1.4 Settings Management
**Files**: `PotterSettings.swift`, `ModernSettingsWindow.swift`

**Observable Properties** (SwiftUI with @Published):
- LLM provider selection
- Model selection per provider
- Current prompt selection  
- Notifications preference
- Login items configuration

**Persistent Storage**:
- **UserDefaults Integration**: Automatic property persistence
- **Key Storage Schema**:
  - `llm_provider` - Selected LLM provider
  - `selected_model` - Model choice per provider
  - `current_prompt` - Active prompt name
  - `notifications_enabled` - Notification preference
  - `global_hotkey` - Custom hotkey combination

**Real-time Updates**: All changes immediately reflected in UI and core functionality

---

## 🎨 UI Features

### 2.1 Modern Settings Window
**Files**: `ModernSettingsWindow.swift`

**Design**: Native SwiftUI with sidebar navigation

**Sections**:

#### General Tab
- **LLM Provider Configuration**: Provider/model selection with validation
- **API Key Management**: Secure input with storage method selection
- **Hotkey Configuration**: Visual key capture with pill interface
- **Permissions Status**: Real-time accessibility/notification status
- **Login Items**: Start at login toggle with system integration

#### Prompts Tab
- **Prompt Management**: CRUD operations on custom prompts
- **Default Prompts**: Summarize, Formal, Casual, Friendly
- **Real-time Editing**: Inline editing with validation
- **Character Limits**: Name (1-50), Content (1-5000)

#### About Tab
- **Build Information**: Version, build ID, build date
- **Environment Details**: Swift version, macOS version
- **Developer Credits**: Link to graydot.ai
- **Support Links**: Documentation and issue tracking

#### Logs Tab
- **Real-time Logs**: Live application log display
- **Level Filtering**: Info, Warning, Error, Debug levels
- **Color Coding**: Visual distinction by log level
- **Export**: Save logs for debugging

**Keyboard Shortcuts**:
- **ESC**: Close settings window
- **⌘,**: Open settings (global)
- **Tab Navigation**: Between sections and controls

---

### 2.2 LLM Provider Configuration
**Files**: `LLMProviderView.swift`

**Provider Selection**:
- Dropdown with completion indicators (✅/❌)
- Dynamic model list per provider
- Real-time availability checking

**API Key Management**:
- Secure text input with show/hide toggle
- Real-time format validation
- Storage method selection (Keychain vs UserDefaults)
- Migration between storage methods

**Validation Features**:
- Async API key testing with progress indication
- Provider-specific validation endpoints
- Detailed error messaging for invalid keys
- Success confirmation with visual feedback

**Storage Method Toggle**:
- **Keychain (Encrypted)**: Secure, requires system permission
- **UserDefaults (Plain Text)**: Compatible, visible in defaults
- Seamless migration between methods
- Clear security implications explained

---

### 2.3 Advanced Hotkey Configuration
**Files**: `ModernSettingsWindow.swift` (HotkeyConfigurationView)

**Visual Key Capture**:
- **Pill Interface**: Shows current hotkey as visual pills (⌘ ⇧ 9)
- **Live Capture**: Real-time key combination display
- **Placeholder Pills**: "?" indicators during capture

**Capture Features**:
- **Click Activation**: Click any pill to start capture
- **Reset Button**: Activates capture with default combination
- **ESC Cancellation**: Restore previous hotkey
- **3+ Key Requirement**: Ensures meaningful combinations

**Validation**:
- Conflict detection with system shortcuts
- Invalid combination prevention
- Clear error messaging for issues

**Accessibility Integration**:
- Permission status display
- Direct System Settings navigation
- Help text for denied permissions

---

### 2.4 Menu Bar Integration
**Files**: `main.swift` (AppDelegate)

**Dynamic Status Icons**:
- **Adaptive Theming**: Black pot (light mode), white pot (dark mode)
- **State Indicators**:
  - **Normal**: Static Potter pot icon
  - **Processing**: Animated yellow spinner
  - **Success**: Green dot (5-second display)
  - **Error**: Red dot with message (10-second display)

**Context Menu System**:
- **Process Text**: Main action with current hotkey display
- **Permission Status**: Real-time status with color indicators
  - 🟢 Granted, 🔴 Denied, 🟡 Not Determined, ⚪ Unknown
- **Dynamic Prompt Selection**: Current prompt with checkmark
- **Settings Access**: Direct settings window launch
- **Error Display**: Contextual error messages

**Icon Resources**:
- Multiple resolutions (16px, 18px, 32px)
- Retina support (@2x variants)
- Fallback mechanisms for missing icons

**Menu Updates**:
- **Real-time Updates**: 30-second refresh cycle
- **Permission Monitoring**: Live status checking
- **Error State Management**: Automatic error clearing

---

### 2.5 Prompt Management System
**Files**: `ModernSettingsWindow.swift`, `PromptEditDialog.swift`

**Prompt CRUD Operations**:

#### Create
- **New Prompt Dialog**: Modal AppKit window
- **Validation**: Name uniqueness, length limits
- **Real-time Feedback**: Character counters, error messages

#### Read
- **JSON Loading**: From Application Support directory
- **Fallback Defaults**: Built-in prompts if file missing
- **Error Recovery**: Graceful handling of corrupted files

#### Update
- **In-place Editing**: Direct modification in settings
- **Conflict Detection**: Duplicate name prevention
- **Live Preview**: Immediate UI updates

#### Delete
- **Confirmation Dialog**: Prevent accidental deletion
- **Safe Removal**: Maintains prompt selection consistency

**Prompt Editor Dialog** (`PromptEditDialog.swift`):
- **Modal Interface**: Custom NSWindow with proper key handling
- **Character Limits**: Live validation (Name: 1-50, Content: 1-5000)
- **Keyboard Shortcuts**: ESC (cancel), ⌘⏎ (save)
- **Full Text Editing**: NSTextView with undo/redo support

**Default Prompts**:
- **summarize**: "Please provide a concise summary..."
- **formal**: "Please rewrite in formal, professional tone..."
- **casual**: "Please rewrite in casual, relaxed tone..."
- **friendly**: "Please rewrite in warm, approachable tone..."

**Storage**: JSON file in `~/Library/Application Support/Potter/prompts.json`

---

## 🔧 System Integration Features

### 3.1 Permission Management
**Files**: `PermissionManager.swift`, `PermissionsView.swift`

**Permission Types**:

#### Accessibility Permission
- **Purpose**: Required for global hotkey functionality
- **Detection**: `AXIsProcessTrusted()` API checking
- **Request Flow**: System Settings deep-linking to Privacy & Security → Accessibility
- **Monitoring**: 1-second intervals for 1 minute, then 10-second intervals
- **Auto-restart Prompts**: Suggests restart after permission grant

#### Notification Permission
- **Purpose**: Optional status notifications
- **Framework**: UNUserNotificationCenter integration
- **States**: Authorized, denied, notDetermined, provisional
- **Graceful Degradation**: Works without notifications if denied

**Permission Interface**:
- **Status Indicators**: Color-coded status display
- **Action Buttons**: Direct System Settings navigation with fallbacks
- **Combined Sections**: Unified accessibility + hotkey configuration
- **Reset Functionality**: Complete permission reset via tccutil

**Monitoring System**:
- **Smart Polling**: Adaptive polling intervals (1s → 10s)
- **Automatic Timeout**: 6-minute maximum monitoring
- **Change Detection**: Only prompts restart on newly granted permissions
- **Deep Linking**: Multiple fallback URLs for System Settings access

---

### 3.2 Process Management
**Files**: `ProcessManager.swift`

**Duplicate Process Detection**:
- **Lock File System**: JSON lock files in Application Support
- **PID Validation**: Active process verification using `kill(pid, 0)`
- **Build Metadata**: Version, build ID, timestamp tracking

**Lock File Structure**:
```json
{
  "pid": 12345,
  "buildId": "unique-identifier",
  "version": "2.0.0",
  "buildDate": "2025-06-19T..."
}
```

**Conflict Resolution**:
- **User Choice Dialog**: Kill others vs exit current process
- **Build Information Display**: Shows conflicting build details
- **Graceful Termination**: SIGTERM → SIGKILL sequence
- **Cleanup**: Automatic stale lock file removal

**Build Tracking**:
- **Unique Build IDs**: UUID-based identification
- **Version Comparison**: Semantic versioning support
- **Timestamp Tracking**: ISO date format
- **Process Monitoring**: Real-time PID validation

---

### 3.3 Secure Storage Systems
**Files**: `SecureAPIKeyStorage.swift`, `KeychainManager.swift`

**Dual Storage Architecture**:

#### Keychain Storage (Secure)
- **Technology**: macOS Security framework
- **Encryption**: Hardware-based encryption via Secure Enclave
- **Access Control**: Device-only, when-unlocked access
- **Service Name**: "Potter-API-Keys"
- **Format**: JSON dictionary with all API keys

#### UserDefaults Storage (Compatible)
- **Technology**: NSUserDefaults
- **Format**: Plain text key-value pairs
- **Visibility**: Accessible via `defaults read com.potter.Potter`
- **Migration**: Seamless migration to/from keychain

**Storage Operations**:
- **Unified Interface**: SecureAPIKeyStorage as single access point
- **Method Tracking**: Per-provider storage method preferences
- **Thread Safety**: DispatchQueue for keychain operations
- **Error Handling**: Graceful fallback mechanisms
- **Cache System**: In-memory caching to minimize keychain prompts

**Migration Features**:
- **Bidirectional**: Keychain ↔ UserDefaults migration
- **Atomic Operations**: Save new location before removing old
- **Bulk Migration**: All providers migrated together
- **User Choice**: Clear explanation of security implications

---

### 3.4 Application Lifecycle
**Files**: `main.swift`, `ProcessManager.swift`, `LoginItemsManager.swift`

**Startup Sequence**:
1. **App Icon Setup**: Custom Potter icon configuration
2. **Edit Menu Creation**: Standard macOS edit menu for keyboard shortcuts
3. **Duplicate Process Check**: Process conflict detection and resolution
4. **Menu Bar Setup**: Status item creation with icon and menu
5. **Core Initialization**: PotterCore setup with hotkey registration
6. **Permission Validation**: Accessibility permission checking
7. **Settings Auto-Show**: Automatic settings if no API key configured
8. **Menu Update Timer**: 30-second status refresh cycle

**Shutdown Sequence**:
- **Timer Cleanup**: Menu update timer invalidation
- **Lock File Removal**: Process lock file cleanup
- **Graceful Termination**: Proper NSApplication exit
- **Resource Cleanup**: Memory and handle cleanup

**Login Items Management** (`LoginItemsManager.swift`):
- **Modern API**: SMAppService integration (macOS 13+)
- **Status Monitoring**: Real-time login item status
- **Enable/Disable**: Toggle login item registration
- **Error Handling**: User-friendly error dialogs
- **System Settings Integration**: Direct navigation on failures

---

## 🚀 Advanced Features

### 4.1 Comprehensive Logging System
**Files**: `PotterLogger.swift`

**Multi-Level Logging**:
- **Info**: General operational information
- **Warning**: Non-critical issues and recoverable errors
- **Error**: Critical failures and exceptions
- **Debug**: Detailed diagnostic information

**Component-Based Organization**:
- **startup**: Application launch and initialization
- **hotkey**: Global hotkey registration and handling
- **text_processor**: AI text processing operations
- **settings**: Settings changes and validation
- **permissions**: Permission status and changes
- **ui**: User interface interactions and updates
- **llm_manager**: LLM provider operations
- **keychain**: Secure storage operations

**Output Destinations**:
- **Console**: Real-time console output via `print()`
- **OSLog**: System logging framework integration
- **Memory Buffer**: 500-entry circular buffer for UI display

**Log Management**:
- **Memory Limits**: Automatic cleanup at 500 entries
- **Thread Safety**: Main queue for UI updates
- **Real-time Updates**: Observable properties for SwiftUI
- **Export**: File export capability for debugging

**Log Viewer Integration**:
- **Live Display**: Real-time log view in Settings → Logs
- **Color Coding**: Level-based visual indicators
- **Filtering**: Show/hide specific log levels
- **Text Selection**: Copy log entries for support

---

### 4.2 Error Handling Architecture
**Files**: Throughout codebase

**Hierarchical Error Types**:

#### LLMError (LLM operations)
- `noResponse` - Empty API response
- `invalidAPIKey` - Authentication failure
- `apiError(Int, String)` - HTTP errors with details
- `networkError(Error)` - Network connectivity issues

#### Permission Errors
- Clear messaging about required permissions
- Direct navigation to system settings
- Graceful degradation when permissions denied

#### Storage Errors
- Keychain access failures
- JSON parsing errors
- File system issues
- Automatic fallback mechanisms

**User Feedback Systems**:
- **Menu Bar Icons**: Visual status indicators (spinner, green, red)
- **Error Messages**: User-friendly error explanations
- **System Notifications**: Optional notification alerts
- **Dialog Messages**: Detailed error dialogs with actions

**Error Recovery**:
- **Automatic Retry**: For transient network errors
- **Fallback Storage**: UserDefaults when keychain fails
- **Permission Guidance**: Step-by-step permission instructions
- **Graceful Degradation**: Core functionality maintained during errors

---

### 4.3 Performance Optimizations
**Files**: Various

**Async Operations**:
- **LLM Processing**: Fully async API calls with proper error handling
- **Permission Checking**: Non-blocking status updates
- **UI Updates**: MainActor for thread-safe UI operations
- **Validation**: Async API key validation without UI blocking

**Memory Management**:
- **Weak References**: Proper delegate patterns to prevent retain cycles
- **Timer Cleanup**: Automatic timer invalidation
- **Log Limits**: Circular buffer to prevent memory growth
- **Cache Systems**: Efficient API key caching with minimal keychain access

**Resource Optimization**:
- **Icon Loading**: Multiple resolution support with intelligent fallbacks
- **JSON Processing**: Efficient prompt storage and loading
- **Thread Safety**: Proper queue management for concurrent operations
- **Lazy Loading**: Deferred resource loading where appropriate

**Network Optimization**:
- **Request Reuse**: Efficient HTTP client usage
- **Error Handling**: Proper timeout and retry mechanisms
- **Response Processing**: Efficient JSON parsing and validation

---

### 4.4 Build and Development Integration
**Files**: Various configuration and resource files

**Build System Support**:
- **Swift Package Manager**: Native dependency management
- **Bundle Configuration**: Proper macOS app bundle structure
- **Resource Management**: Organized asset and configuration files
- **Code Signing Preparation**: Ready for distribution signing

**Development Features**:
- **Debug Logging**: Comprehensive debug output
- **Test Mode Support**: API validation testing
- **Error Simulation**: Graceful error state testing
- **Development Shortcuts**: Debug-only features and enhanced logging

**Resource Organization**:
- **Icons**: Multiple resolutions in Resources/AppIcon/
- **Prompts**: Default prompts in Resources/
- **Configuration**: Build metadata and version tracking
- **Assets**: Images, backgrounds, and UI resources

---

## 📊 Configuration Points

### User-Configurable Options

#### LLM Configuration
- **Provider Selection**: OpenAI, Anthropic, Google
- **Model Selection**: Provider-specific model choice
- **API Key Management**: Secure storage with method selection

#### Interface Configuration
- **Hotkey Customization**: Full keyboard support for global hotkeys
- **Prompt Management**: Complete CRUD operations on prompts
- **Notification Preferences**: Enable/disable system notifications
- **Storage Method**: Choose encryption level (Keychain vs UserDefaults)

#### System Integration
- **Login Items**: Automatic startup configuration
- **Permission Management**: Guided accessibility and notification setup
- **Theme Adaptation**: Automatic light/dark mode icon switching

### File Locations

#### Application Data
- **Prompts**: `~/Library/Application Support/Potter/prompts.json`
- **Lock Files**: `~/Library/Application Support/Potter/potter.lock`
- **Logs**: Console and in-memory (no persistent log files)

#### System Integration
- **Settings**: UserDefaults with app-specific keys
- **API Keys**: Keychain ("Potter-API-Keys" service) or UserDefaults
- **Permissions**: System-managed accessibility and notification permissions

### Key APIs and Integrations

#### macOS System APIs
- **Accessibility**: `AXIsProcessTrusted()` for global hotkey permissions
- **Notifications**: `UNUserNotificationCenter` for status notifications
- **Keychain**: Security framework for encrypted API key storage
- **Carbon Events**: Global hotkey registration and handling
- **Login Items**: SMAppService for startup integration

#### External APIs
- **OpenAI**: Chat Completions API with latest models
- **Anthropic**: Messages API with Claude models
- **Google**: GenerateContent API with Gemini models

#### Internal Architecture
- **SwiftUI**: Modern reactive UI framework
- **Combine**: Reactive programming for data flow
- **AppKit**: Native macOS integration for system features
- **Swift Package Manager**: Dependency and build management

---

## 🔧 Technical Implementation Details

### Thread Safety
- **Main Queue**: All UI updates on MainActor
- **Background Queues**: Network operations and file I/O
- **Synchronization**: Proper queue management for shared resources

### Error Boundaries
- **UI Isolation**: UI errors don't crash core functionality
- **Network Isolation**: Network failures don't affect local operations
- **Storage Isolation**: Storage errors have fallback mechanisms

### Performance Characteristics
- **Startup Time**: < 3 seconds typical startup
- **Memory Usage**: < 50MB typical footprint
- **Network Usage**: Minimal (only during text processing)
- **CPU Usage**: Near-zero idle, brief spikes during processing

### Security Features
- **API Key Encryption**: Optional keychain encryption
- **Network Security**: HTTPS-only communications
- **Permission Model**: Minimal required permissions
- **Data Privacy**: No telemetry or user data collection

---

*Potter Features Documentation v2.0.0*  
*Complete feature reference for development and refactoring*  
*Last Updated: June 19, 2025*
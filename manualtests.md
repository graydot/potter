# Potter Manual Test Plan

Comprehensive testing guide for Potter - AI Text Processing Tool for macOS.

## Pre-Test Setup

### Environment Preparation
1. **Clean test environment**:
   ```bash
   # Remove existing configurations
   rm -rf ~/Library/Application\ Support/Potter
   rm -f ~/Library/Logs/potter.log
   defaults delete com.potter.Potter 2>/dev/null || true
   
   # Remove keychain entries
   security delete-generic-password -s "Potter_OpenAI_API_Key" 2>/dev/null || true
   security delete-generic-password -s "Potter_Anthropic_API_Key" 2>/dev/null || true
   security delete-generic-password -s "Potter_Google_API_Key" 2>/dev/null || true
   ```

2. **Build fresh app**:
   ```bash
   cd swift-potter
   swift build
   # OR build signed app
   python ../scripts/build_app.py --target local
   ```

3. **Prepare test API keys** (use test/development keys):
   - OpenAI API key (GPT-3.5-turbo access)
   - Anthropic Claude API key (optional)
   - Google Gemini API key (optional)

---

## Test Suite 1: First Launch & Initial Setup

### T1.1: Clean First Launch
**Objective**: Verify app launches correctly on clean system

**Steps**:
1. Launch Potter.app for first time
2. Observe system permission requests
3. Check if settings dialog opens automatically

**Expected Results**:
- App launches without crashes
- Accessibility permission request appears
- Settings dialog opens automatically (no API keys configured)
- Menu bar icon appears (orange pot design)

**Pass Criteria**: ✅ All expected results occur

---

### T1.2: Permission Handling
**Objective**: Test accessibility permission flow

**Steps**:
1. When prompted for accessibility permissions, click "Deny"
2. Try to use global hotkey (Cmd+Shift+9)
3. Check menu bar icon and permissions status
4. Go to Settings → General to check permission status
5. Click on permission status to open System Settings
6. Grant accessibility permissions
7. Return to Potter and verify permission status

**Expected Results**:
- Denied permissions show as "🔴 Accessibility: Denied" in menu
- Global hotkey doesn't work when denied
- Settings show permission status with help text
- Clicking permission status opens System Settings→Privacy & Security→Accessibility
- After granting, status updates to "🟢 Accessibility: Granted"
- Global hotkey works after granting permissions

**Pass Criteria**: ✅ Permission flow works correctly with proper feedback

---

### T1.3: API Key Configuration - OpenAI
**Objective**: Test API key setup and validation

**Steps**:
1. Open Settings (Cmd+, or menu)
2. Navigate to "General" tab
3. Select "OpenAI" as provider
4. Enter invalid API key (e.g., "sk-invalid")
5. Click "Validate & Save"
6. Observe error handling
7. Enter valid OpenAI API key
8. Click "Validate & Save"
9. Verify success feedback

**Expected Results**:
- Invalid key shows validation error with specific message
- Valid key shows "✅ API key validated successfully"
- Provider shows as configured in menu
- Settings dialog can be closed after successful validation

**Pass Criteria**: ✅ API key validation and storage works correctly

---

## Test Suite 2: Core Functionality

### T2.1: Basic Text Processing
**Objective**: Test core text transformation workflow

**Steps**:
1. Open any text editor (TextEdit, Notes, etc.)
2. Type: "This is a test sentence that needs to be summarized."
3. Select all text (Cmd+A)
4. Copy text (Cmd+C)
5. Press global hotkey (Cmd+Shift+9)
6. Wait for processing
7. Paste result (Cmd+V)

**Expected Results**:
- Menu bar icon shows processing state (yellow spinner)
- Processing completes within 10 seconds
- Menu bar icon shows success state (green)
- Clipboard contains summarized text
- Original text is replaced with AI-processed version

**Pass Criteria**: ✅ Text processing workflow completes successfully

---

### T2.2: Multiple LLM Providers
**Objective**: Test switching between different AI providers

**Prerequisite**: Configure API keys for multiple providers

**Steps**:
1. Process text with OpenAI (default)
2. Open Settings → General
3. Switch to "Anthropic Claude"
4. Close settings and process same text
5. Switch to "Google Gemini" 
6. Process text again
7. Compare results from different providers

**Expected Results**:
- Each provider produces different but valid responses
- Provider switching works without errors
- Processing times may vary between providers
- Menu bar feedback works for all providers

**Pass Criteria**: ✅ All configured providers work correctly

---

### T2.3: Custom Prompts
**Objective**: Test custom prompt functionality

**Steps**:
1. Open Settings → Prompts
2. Note default prompts (Summarize, Formal, Casual)
3. Click "+" to add new prompt
4. Create prompt: Name="Translate to French", Prompt="Translate the following text to French:"
5. Save prompt
6. Verify prompt appears in both settings and menu bar menu
7. Select text: "Hello, how are you today?"
8. Select "Translate to French" from menu bar menu
9. Process text

**Expected Results**:
- New prompt saved successfully
- Prompt appears in menu with checkmark when selected
- Text is translated to French when processed
- Menu updates to show selected prompt

**Pass Criteria**: ✅ Custom prompts creation and usage works

---

## Test Suite 3: Settings & Configuration

### T3.1: Hotkey Configuration
**Objective**: Test hotkey customization

**Steps**:
1. Open Settings → General
2. Find hotkey configuration section
3. Click on current hotkey pills (⌘ ⇧ 9)
4. Verify capture mode activates (pills show "?" placeholders)
5. Press new combination: Cmd+Shift+T
6. Verify hotkey updates
7. Test new hotkey works for text processing
8. Click "Reset" button
9. Verify hotkey returns to default (Cmd+Shift+9)

**Expected Results**:
- Clicking pills activates capture mode
- Global hotkey is disabled during capture
- New hotkey combination is captured correctly
- Old hotkey stops working, new hotkey works
- Reset button activates capture mode with default values
- ESC cancels capture and restores previous hotkey

**Pass Criteria**: ✅ Hotkey configuration works with proper feedback

---

### T3.2: Secure Storage Options
**Objective**: Test keychain vs UserDefaults storage

**Steps**:
1. Configure API key with "Keychain (Encrypted)" selected
2. Quit and restart Potter
3. Verify API key persists and works
4. Open Settings → General
5. Switch to "UserDefaults (Plain Text)" 
6. Verify migration dialog or confirmation
7. Quit and restart Potter again
8. Verify API key still works
9. Check storage location differences

**Expected Results**:
- Keychain storage requires system permission on first use
- API keys persist across app restarts regardless of storage method
- Switching storage methods migrates keys correctly
- UserDefaults keys visible in: `defaults read com.potter.Potter`
- Keychain keys accessible via Keychain Access.app

**Pass Criteria**: ✅ Both storage methods work with proper migration

---

### T3.3: Settings Window Navigation
**Objective**: Test settings UI functionality

**Steps**:
1. Open settings with various methods:
   - Menu bar → Preferences
   - Keyboard shortcut (Cmd+,)
   - Right-click menu bar icon
2. Navigate between tabs using:
   - Sidebar clicks
   - Keyboard navigation
3. Test keyboard shortcuts:
   - ESC to close
   - Cmd+Enter to save (if applicable)
4. Test window management:
   - Close with red button
   - Hide/show window
   - Multiple settings window attempts

**Expected Results**:
- Settings opens via all methods
- Sidebar navigation works smoothly
- ESC closes settings window
- Only one settings window can be open
- Window appears centered and at appropriate size

**Pass Criteria**: ✅ Settings UI is responsive and well-behaved

---

## Test Suite 4: Error Handling & Edge Cases

### T4.1: Network Connectivity Issues
**Objective**: Test behavior when network is unavailable

**Steps**:
1. Disconnect from internet (WiFi off)
2. Try to process text with global hotkey
3. Observe error handling and user feedback
4. Reconnect to internet
5. Try processing same text again

**Expected Results**:
- Network error is detected and handled gracefully
- Menu bar icon shows error state (red)
- Error message appears in menu bar menu
- Processing works after reconnecting
- No app crashes or freezes

**Pass Criteria**: ✅ Network errors handled gracefully

---

### T4.2: Invalid API Keys
**Objective**: Test handling of revoked/invalid API keys

**Steps**:
1. Configure Potter with valid API key
2. Process text successfully
3. Externally revoke/invalidate API key (or use expired key)
4. Try processing text
5. Observe error handling
6. Update to valid API key
7. Verify recovery

**Expected Results**:
- Invalid API key error is clearly communicated
- Menu bar shows error state
- User can easily navigate to settings to fix
- Recovery works after fixing API key
- No app crashes during error state

**Pass Criteria**: ✅ API key errors handled appropriately

---

### T4.3: Large Text Processing
**Objective**: Test limits and performance with large text

**Steps**:
1. Create large text document (10,000+ words)
2. Select all text and copy
3. Try processing with global hotkey
4. Monitor performance and memory usage
5. Test with extremely large text (100,000+ words)

**Expected Results**:
- Large text processed without crashes
- Reasonable processing time (under 30 seconds for 10k words)
- Memory usage remains stable
- Extremely large text either processes or fails gracefully with error message
- UI remains responsive during processing

**Pass Criteria**: ✅ Large text handled appropriately without crashes

---

### T4.4: Clipboard Edge Cases
**Objective**: Test various clipboard scenarios

**Steps**:
1. Clear clipboard completely
2. Try global hotkey with empty clipboard
3. Copy non-text content (image, file)
4. Try global hotkey with non-text clipboard
5. Copy text with special characters (emojis, unicode)
6. Process special character text
7. Copy extremely long single line
8. Process long single line

**Expected Results**:
- Empty clipboard shows appropriate error/warning
- Non-text clipboard content handled gracefully
- Special characters preserved in processing
- Long lines handled without truncation
- All edge cases show user-friendly messages

**Pass Criteria**: ✅ Clipboard edge cases handled properly

---

## Test Suite 5: System Integration

### T5.1: Multiple Instance Prevention
**Objective**: Test single instance enforcement

**Steps**:
1. Launch Potter.app normally
2. Try launching Potter.app again while first instance running
3. Observe duplicate instance dialog
4. Choose "Exit This Process"
5. Verify first instance continues running
6. Launch Potter again
7. Choose "Kill Others and Continue"
8. Verify new instance takes over

**Expected Results**:
- Duplicate instance detected and dialog shown
- Options clearly explained to user
- "Exit This Process" preserves original instance
- "Kill Others and Continue" replaces with new instance
- Process management works reliably

**Pass Criteria**: ✅ Single instance enforcement works correctly

---

### T5.2: Menu Bar Integration
**Objective**: Test menu bar behavior and integration

**Steps**:
1. Verify menu bar icon appears in correct location
2. Test icon visibility in both light and dark macOS themes
3. Right-click menu bar icon
4. Left-click menu bar icon  
5. Test menu responsiveness
6. Check icon state changes during text processing
7. Verify icon persists through app lifecycle

**Expected Results**:
- Icon uses correct Potter pot design
- Icon adapts to light/dark themes (black/white pot)
- Both left and right clicks show menu
- Menu items are functional and up-to-date
- Processing states clearly visible (spinner, green, red)
- Icon remains stable in menu bar

**Pass Criteria**: ✅ Menu bar integration works seamlessly

---

### T5.3: System Theme Changes
**Objective**: Test adaptation to macOS theme changes

**Steps**:
1. Start Potter in light mode
2. Verify menu bar icon is black pot
3. Switch to dark mode (System Settings → Appearance)
4. Verify menu bar icon changes to white pot
5. Switch back to light mode
6. Confirm icon updates correctly
7. Test settings window appearance in both themes

**Expected Results**:
- Menu bar icon automatically updates for theme changes
- Settings window follows system theme
- All UI elements adapt appropriately
- No visual glitches during theme transitions

**Pass Criteria**: ✅ Theme adaptation works correctly

---

### T5.4: App Lifecycle Management
**Objective**: Test app startup, running, and shutdown

**Steps**:
1. Launch Potter and note startup time
2. Use app normally for extended period
3. Put Mac to sleep with Potter running
4. Wake Mac and verify Potter still functional
5. Log out and log back in
6. Verify Potter auto-starts if configured
7. Quit Potter via menu bar → Quit
8. Verify clean shutdown

**Expected Results**:
- Fast startup (under 3 seconds)
- Stable operation during extended use
- Survives sleep/wake cycles
- Clean shutdown without hanging
- Optional auto-start works if enabled
- No memory leaks during extended operation

**Pass Criteria**: ✅ App lifecycle is stable and reliable

---

## Test Suite 6: Advanced Features

### T6.1: Prompt Management
**Objective**: Test advanced prompt operations

**Steps**:
1. Create 10+ custom prompts
2. Edit existing prompts
3. Delete prompts (test confirmation)
4. Try creating prompt with invalid characters
5. Test very long prompt names and content
6. Export/import prompts (if feature exists)
7. Test prompt ordering and organization

**Expected Results**:
- Large number of prompts handled efficiently
- Edit operations work smoothly
- Delete confirmation prevents accidents
- Input validation prevents invalid prompts
- Long content handled appropriately
- Prompt management is user-friendly

**Pass Criteria**: ✅ Advanced prompt management works correctly

---

### T6.2: Build Information & Diagnostics
**Objective**: Test diagnostic features and build info

**Steps**:
1. Open Settings → About
2. Verify build information is accurate
3. Check version numbers match expectations
4. Test any diagnostic features
5. Look for debug logs in appropriate locations
6. Verify build ID and version consistency

**Expected Results**:
- Build information is accurate and helpful
- Version numbers are consistent across UI
- Debug logs are properly located and formatted
- Diagnostic features provide useful information
- Build IDs are unique and trackable

**Pass Criteria**: ✅ Diagnostic features work and provide useful info

---

## Test Suite 7: Performance & Reliability

### T7.1: Memory Usage
**Objective**: Monitor memory usage and detect leaks

**Tools**: Activity Monitor, memory profiling tools

**Steps**:
1. Launch Potter and note initial memory usage
2. Process 100 text samples sequentially
3. Monitor memory usage throughout
4. Leave Potter running for 24+ hours
5. Check for memory leaks or growth
6. Stress test with rapid hotkey usage

**Expected Results**:
- Initial memory usage under 50MB
- Memory usage remains stable during heavy use
- No significant memory leaks over time
- Performance remains consistent
- App handles stress testing without issues

**Pass Criteria**: ✅ Memory usage is stable and efficient

---

### T7.2: CPU Usage
**Objective**: Monitor CPU usage patterns

**Steps**:
1. Monitor CPU usage during idle state
2. Process various text sizes and monitor CPU
3. Test with different LLM providers
4. Monitor during UI interactions
5. Check for CPU spikes or sustained high usage

**Expected Results**:
- Idle CPU usage near 0%
- CPU spikes only during active processing
- CPU usage returns to idle after processing
- UI interactions don't cause excessive CPU load
- Different providers show similar CPU patterns

**Pass Criteria**: ✅ CPU usage is appropriate and efficient

---

## Test Suite 8: Security & Privacy

### T8.1: API Key Security
**Objective**: Verify API key storage security

**Steps**:
1. Configure API key using keychain storage
2. Verify key not visible in plain text anywhere
3. Check UserDefaults, plist files, logs
4. Switch to UserDefaults storage
5. Verify key is now visible in UserDefaults
6. Test keychain access permissions

**Expected Results**:
- Keychain storage keeps keys encrypted
- No API keys appear in logs or plain text files
- UserDefaults storage shows keys in plain text (as expected)
- Keychain access requires proper permissions
- User understands security implications of each option

**Pass Criteria**: ✅ API key security works as designed

---

### T8.2: Network Security
**Objective**: Test network communication security

**Tools**: Network monitoring tools (optional)

**Steps**:
1. Monitor network traffic during API calls
2. Verify HTTPS is used for all LLM providers
3. Check for any insecure connections
4. Verify no sensitive data in URLs or headers
5. Test certificate validation

**Expected Results**:
- All API calls use HTTPS/TLS encryption
- No API keys in URL parameters
- Proper certificate validation
- No insecure fallback connections
- Network traffic appears properly encrypted

**Pass Criteria**: ✅ Network communication is secure

---

## Test Reports

### Test Execution Log

| Test ID | Test Name | Date | Status | Notes |
|---------|-----------|------|--------|-------|
| T1.1 | Clean First Launch | ___ | ⏳ | |
| T1.2 | Permission Handling | ___ | ⏳ | |
| T1.3 | API Key Configuration | ___ | ⏳ | |
| T2.1 | Basic Text Processing | ___ | ⏳ | |
| T2.2 | Multiple LLM Providers | ___ | ⏳ | |
| T2.3 | Custom Prompts | ___ | ⏳ | |
| T3.1 | Hotkey Configuration | ___ | ⏳ | |
| T3.2 | Secure Storage Options | ___ | ⏳ | |
| T3.3 | Settings Window Navigation | ___ | ⏳ | |
| T4.1 | Network Connectivity Issues | ___ | ⏳ | |
| T4.2 | Invalid API Keys | ___ | ⏳ | |
| T4.3 | Large Text Processing | ___ | ⏳ | |
| T4.4 | Clipboard Edge Cases | ___ | ⏳ | |
| T5.1 | Multiple Instance Prevention | ___ | ⏳ | |
| T5.2 | Menu Bar Integration | ___ | ⏳ | |
| T5.3 | System Theme Changes | ___ | ⏳ | |
| T5.4 | App Lifecycle Management | ___ | ⏳ | |
| T6.1 | Prompt Management | ___ | ⏳ | |
| T6.2 | Build Information | ___ | ⏳ | |
| T7.1 | Memory Usage | ___ | ⏳ | |
| T7.2 | CPU Usage | ___ | ⏳ | |
| T8.1 | API Key Security | ___ | ⏳ | |
| T8.2 | Network Security | ___ | ⏳ | |

### Status Legend
- ⏳ Not Started
- 🔄 In Progress  
- ✅ Passed
- ❌ Failed
- ⚠️ Partial/Issues

---

## Quick Smoke Test

For rapid verification, execute this minimal test sequence:

1. **Launch**: Start Potter.app
2. **Permissions**: Grant accessibility permissions
3. **Configure**: Add OpenAI API key
4. **Process**: Copy text, use Cmd+Shift+9, verify result
5. **Settings**: Open settings, change a setting, close
6. **Quit**: Clean exit via menu bar

**Expected**: All steps complete without errors in under 5 minutes.

---

## Test Environment Requirements

### macOS Versions
- **Primary**: macOS 13.0+ (Ventura)
- **Secondary**: macOS 14.0+ (Sonoma)
- **Tertiary**: macOS 15.0+ (Sequoia)

### Hardware
- **Minimum**: 8GB RAM, 2GB free disk space
- **Recommended**: 16GB RAM, 5GB free disk space
- **Architecture**: Apple Silicon (M1/M2/M3) and Intel x86_64

### Network
- **Internet**: Required for LLM API access
- **Firewall**: Should allow outbound HTTPS (443)
- **Proxy**: Test with/without corporate proxies

---

*Potter Manual Test Plan v2.0.0*  
*Last Updated: June 19, 2025*
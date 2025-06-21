# Potter Refactoring Plan

Comprehensive refactoring strategy for Potter v2.0.0 to improve code quality, maintainability, security, and architecture while preserving all existing functionality.

## 📋 Executive Summary

**Current State**: Potter is a functional Swift macOS application with 4,144 lines across 13 Swift files. While the app works well, there are architectural issues, security vulnerabilities, and code quality problems that need addressing.

**Goal**: Transform Potter into a production-ready, maintainable, secure, and elegant codebase while preserving 100% of existing functionality.

**Approach**: Incremental refactoring in phases to minimize risk and ensure continuous functionality.

---

## 🎯 Refactoring Objectives

### Primary Goals
1. **Security Hardening**: Fix critical security vulnerabilities
2. **Architecture Improvement**: Proper separation of concerns and dependency injection
3. **Code Quality**: Eliminate code smells and improve maintainability
4. **Error Handling**: Standardize error handling patterns
5. **Testing**: Improve testability and test coverage
6. **Performance**: Address performance bottlenecks
7. **Documentation**: Comprehensive code documentation

### Success Criteria
- ✅ All existing features preserved
- ✅ All security vulnerabilities addressed
- ✅ Code coverage > 80%
- ✅ Zero force unwraps (`!`) in production code
- ✅ Consistent error handling patterns
- ✅ Clear separation of concerns
- ✅ Comprehensive documentation

---

## 🔄 Refactoring Phases

## Phase 1: Security & Critical Fixes (Week 1)
**Priority**: 🔴 Critical
**Risk**: Low (isolated changes)

### 1.1 API Key Security ✅ COMPLETED
**Problem**: API keys logged in plain text  
**Files**: `PotterLogger.swift`, all logging calls
**Status**: ✅ Implemented comprehensive log sanitization with regex patterns for OpenAI, Anthropic, Google, AWS, Azure keys. Also sanitizes URL parameters, JSON fields, user content, file paths, and authorization headers.

**Refactoring**:
```swift
// BEFORE
PotterLogger.shared.info("validation", "🔍 OpenAI validation URL: \(url.absoluteString)")

// AFTER  
PotterLogger.shared.info("validation", "🔍 OpenAI validation URL: \(sanitizedURL)")

// New in PotterLogger.swift
extension PotterLogger {
    private func sanitizeMessage(_ message: String) -> String {
        var sanitized = message
        
        // Redact API keys
        let apiKeyPatterns = [
            #"sk-[A-Za-z0-9]+"#,           // OpenAI
            #"sk-ant-[A-Za-z0-9-]+"#,     // Anthropic  
            #"AIza[A-Za-z0-9_-]+"#        // Google
        ]
        
        for pattern in apiKeyPatterns {
            sanitized = sanitized.replacingOccurrences(
                of: pattern, 
                with: "[API_KEY_REDACTED]", 
                options: .regularExpression
            )
        }
        
        // Redact user text
        if message.contains("|||||") {
            return "Processing user text [CONTENT_REDACTED]"
        }
        
        return sanitized
    }
}
```

### 1.2 Google API Security Fix ✅ COMPLETED
**Problem**: API key in URL parameter  
**Files**: `LLMClient.swift` line 242
**Status**: ✅ Fixed Google API to use x-goog-api-key header instead of URL parameter, eliminating exposure in logs and URL history.

**Refactoring**:
```swift
// BEFORE
let url = URL(string: "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=\(apiKey)")!

// AFTER
let baseURL = URL(string: "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent")!
var request = URLRequest(url: baseURL)
request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
```

### 1.3 Storage Race Condition Fix ✅ COMPLETED
**Problem**: API key loss during migration  
**Files**: `SecureAPIKeyStorage.swift`, new `AtomicStorageManager.swift`
**Status**: ✅ Created modular AtomicStorageManager with race-condition-free operations. Implemented atomic save, migrate, and remove operations with rollback capabilities and validation. Simplified storage management as requested.

### 1.4 Force Unwrap Elimination ✅ COMPLETED  
**Problem**: Crash risk from forced unwrapping  
**Files**: All Swift files
**Status**: ✅ Fixed critical force unwraps in AtomicStorageManager.getStorageStatus(), ProcessManager.lockFileURL, main.swift potterCore, PotterCore llmManager, and ModernSettingsWindow. Improved app stability and crash prevention.

**Strategy**:
```swift
// BEFORE
let url = URL(string: urlString)!

// AFTER
guard let url = URL(string: urlString) else {
    throw AppError.invalidURL(urlString)
}
```

**Expected Outcome**: Zero security vulnerabilities, improved app stability

## ✅ PHASE 1 COMPLETED SUCCESSFULLY
**Duration**: 1 session  
**Key Achievements**:
- ✅ API key exposure eliminated through comprehensive log sanitization  
- ✅ Google API security vulnerability fixed (header-based auth)
- ✅ Storage race conditions prevented with atomic operations
- ✅ Critical force unwraps eliminated, crash risk reduced
- ✅ Storage system simplified and modularized as requested
- ✅ Keychain access issue during testing resolved

**Commits**: 
- `dd97861` - Implement Phase 1.1-1.2: Critical security fixes for API key exposure
- `8b60082` - Fix keychain access issue in testing mode  
- `597151d` - Clean up any remaining changes in SecureAPIKeyStorage
- `3806b74` - Remove incorrect testing flag logic from AtomicStorageManager
- `a763c8d` - Fix Test & Save keychain access issue  
- `8a434e3` - Simplify storage management logic
- `2015143` - Phase 1.4: Eliminate dangerous force unwraps

**Next Phase**: Ready to proceed with Phase 2 (Error Handling Standardization) or selected focus area.

---

## Phase 2: Error Handling Standardization (Week 2)
**Priority**: 🟠 High  
**Risk**: Medium (affects error flows)

### 2.1 Unified Error Types
**Problem**: Inconsistent error handling patterns  
**Files**: Throughout codebase

**New Error Architecture**:
```swift
// Core error types
enum PotterError: LocalizedError {
    case configuration(ConfigurationError)
    case network(NetworkError)
    case storage(StorageError)
    case permission(PermissionError)
    case validation(ValidationError)
    
    var errorDescription: String? {
        switch self {
        case .configuration(let error): return error.userMessage
        case .network(let error): return error.userMessage
        case .storage(let error): return error.userMessage
        case .permission(let error): return error.userMessage
        case .validation(let error): return error.userMessage
        }
    }
}

enum ConfigurationError: LocalizedError {
    case invalidAPIKey(provider: String)
    case missingConfiguration(String)
    case invalidFormat(String)
    
    var userMessage: String {
        switch self {
        case .invalidAPIKey(let provider):
            return "Please check your \(provider) API key and try again."
        case .missingConfiguration(let config):
            return "Missing required configuration: \(config)"
        case .invalidFormat(let detail):
            return "Invalid configuration format: \(detail)"
        }
    }
}
```

### 2.2 Result Type Adoption
**Problem**: Mix of throwing functions and optionals  
**Files**: All service classes

**Refactoring**:
```swift
// BEFORE
func saveAPIKey(_ key: String, for provider: LLMProvider) -> Bool
func loadAPIKey(for provider: LLMProvider) -> String?

// AFTER
func saveAPIKey(_ key: String, for provider: LLMProvider) -> Result<Void, PotterError>
func loadAPIKey(for provider: LLMProvider) -> Result<String, PotterError>
```

### 2.3 Error Reporting Service
**New Component**: Centralized error handling and user feedback

```swift
protocol ErrorReporting {
    func report(_ error: PotterError, context: String)
    func showUserError(_ error: PotterError, in window: NSWindow?)
}

class ErrorReportingService: ErrorReporting {
    func report(_ error: PotterError, context: String) {
        PotterLogger.shared.error("error_service", "[\(context)] \(error.localizedDescription)")
        
        // Update UI state
        NotificationCenter.default.post(
            name: .potterErrorOccurred,
            object: error
        )
    }
    
    func showUserError(_ error: PotterError, in window: NSWindow?) {
        let alert = NSAlert()
        alert.messageText = "Potter Error"
        alert.informativeText = error.localizedDescription
        alert.addButton(withTitle: "OK")
        
        if let window = window {
            alert.beginSheetModal(for: window)
        } else {
            alert.runModal()
        }
    }
}
```

**Expected Outcome**: Consistent, user-friendly error handling throughout the app

---

## Phase 3: Architecture Separation (Week 3-4)
**Priority**: 🟠 High  
**Risk**: Medium (large changes but well-isolated)

### 3.1 Dependency Injection Framework
**Problem**: Tight coupling, hard to test  
**Files**: Throughout codebase

**New Architecture**:
```swift
// Core dependency container
protocol DependencyContainer {
    var llmService: LLMService { get }
    var storageService: StorageService { get }
    var hotkeyService: HotkeyService { get }
    var permissionService: PermissionService { get }
    var errorReporting: ErrorReporting { get }
}

class PotterDependencyContainer: DependencyContainer {
    lazy var llmService: LLMService = LLMServiceImpl(
        storageService: storageService,
        errorReporting: errorReporting
    )
    
    lazy var storageService: StorageService = StorageServiceImpl(
        errorReporting: errorReporting
    )
    
    lazy var hotkeyService: HotkeyService = HotkeyServiceImpl(
        errorReporting: errorReporting
    )
    
    lazy var permissionService: PermissionService = PermissionServiceImpl(
        errorReporting: errorReporting
    )
    
    lazy var errorReporting: ErrorReporting = ErrorReportingService()
}
```

### 3.2 Service Layer Extraction
**Problem**: Business logic mixed with UI logic  
**Files**: `ModernSettingsWindow.swift`, `main.swift`

**New Service Interfaces**:
```swift
// LLM Service
protocol LLMService {
    func getProviders() -> [LLMProvider]
    func getModels(for provider: LLMProvider) -> [LLMModel]
    func validateAPIKey(_ key: String, for provider: LLMProvider) async -> Result<Void, PotterError>
    func processText(_ text: String, with prompt: String, using provider: LLMProvider) async -> Result<String, PotterError>
}

// Storage Service  
protocol StorageService {
    func saveAPIKey(_ key: String, for provider: LLMProvider, using method: StorageMethod) -> Result<Void, PotterError>
    func loadAPIKey(for provider: LLMProvider) -> Result<String, PotterError>
    func saveSettings(_ settings: AppSettings) -> Result<Void, PotterError>
    func loadSettings() -> Result<AppSettings, PotterError>
}

// Hotkey Service
protocol HotkeyService {
    func registerHotkey(_ combination: [String]) -> Result<Void, PotterError>
    func updateHotkey(_ combination: [String]) -> Result<Void, PotterError>
    func disableHotkey() -> Result<Void, PotterError>
    func enableHotkey() -> Result<Void, PotterError>
}
```

### 3.3 UI Layer Refactoring
**Problem**: UI directly accessing business logic  
**Files**: `ModernSettingsWindow.swift`

**New ViewModel Pattern**:
```swift
// Settings ViewModel
@MainActor
class SettingsViewModel: ObservableObject {
    @Published var selectedProvider: LLMProvider = .openAI
    @Published var apiKey: String = ""
    @Published var isValidating = false
    @Published var validationMessage: String = ""
    
    private let llmService: LLMService
    private let storageService: StorageService
    private let errorReporting: ErrorReporting
    
    init(dependencies: DependencyContainer) {
        self.llmService = dependencies.llmService
        self.storageService = dependencies.storageService
        self.errorReporting = dependencies.errorReporting
    }
    
    func validateAndSaveAPIKey() async {
        isValidating = true
        defer { isValidating = false }
        
        let result = await llmService.validateAPIKey(apiKey, for: selectedProvider)
        
        switch result {
        case .success:
            validationMessage = "✅ API key validated successfully"
            await saveAPIKey()
        case .failure(let error):
            validationMessage = "❌ \(error.localizedDescription)"
            errorReporting.report(error, context: "API key validation")
        }
    }
    
    private func saveAPIKey() async {
        let result = storageService.saveAPIKey(apiKey, for: selectedProvider, using: .keychain)
        
        switch result {
        case .success:
            break
        case .failure(let error):
            errorReporting.report(error, context: "API key storage")
        }
    }
}
```

**Expected Outcome**: Clean separation between UI and business logic, improved testability

---

## Phase 4: Code Quality & Performance (Week 5)
**Priority**: 🟡 Medium  
**Risk**: Low (internal improvements)

### 4.1 Magic Number Elimination
**Problem**: Hardcoded values throughout codebase  
**Files**: All files

**New Configuration System**:
```swift
struct AppConstants {
    struct UI {
        static let validationDelay: TimeInterval = 0.8
        static let successDisplayDuration: TimeInterval = 5.0
        static let errorDisplayDuration: TimeInterval = 10.0
        static let menuUpdateInterval: TimeInterval = 30.0
    }
    
    struct Limits {
        static let promptNameMaxLength = 50
        static let promptContentMaxLength = 5000
        static let maxLogEntries = 500
        static let apiKeyMinLength = 10
    }
    
    struct Network {
        static let requestTimeout: TimeInterval = 30.0
        static let retryCount = 3
        static let retryDelay: TimeInterval = 1.0
    }
}
```

### 4.2 Memory Management Audit
**Problem**: Potential retain cycles and memory leaks  
**Files**: All delegate patterns

**Improvements**:
```swift
// Timer management
class TimerManager {
    private var timers: [String: Timer] = [:]
    
    func schedule(identifier: String, interval: TimeInterval, repeats: Bool, action: @escaping () -> Void) {
        invalidate(identifier: identifier)
        
        let timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: repeats) { [weak self] _ in
            action()
            if !repeats {
                self?.timers.removeValue(forKey: identifier)
            }
        }
        
        timers[identifier] = timer
    }
    
    func invalidate(identifier: String) {
        timers[identifier]?.invalidate()
        timers.removeValue(forKey: identifier)
    }
    
    func invalidateAll() {
        timers.values.forEach { $0.invalidate() }
        timers.removeAll()
    }
    
    deinit {
        invalidateAll()
    }
}
```

### 4.3 Performance Optimization
**Problem**: Inefficient operations and unnecessary work  
**Files**: Various

**Optimizations**:
```swift
// Lazy loading for expensive operations
class ResourceManager {
    private lazy var iconCache: [String: NSImage] = [:]
    
    func icon(named name: String) -> NSImage? {
        if let cached = iconCache[name] {
            return cached
        }
        
        guard let icon = loadIcon(named: name) else { return nil }
        iconCache[name] = icon
        return icon
    }
    
    private func loadIcon(named name: String) -> NSImage? {
        // Expensive icon loading logic
        return NSImage(named: name)
    }
}

// Debounced operations
class DebouncedOperation {
    private var workItem: DispatchWorkItem?
    private let delay: TimeInterval
    private let queue: DispatchQueue
    
    init(delay: TimeInterval, queue: DispatchQueue = .main) {
        self.delay = delay
        self.queue = queue
    }
    
    func execute(_ action: @escaping () -> Void) {
        workItem?.cancel()
        
        let newWorkItem = DispatchWorkItem(block: action)
        workItem = newWorkItem
        
        queue.asyncAfter(deadline: .now() + delay, execute: newWorkItem)
    }
}
```

**Expected Outcome**: Improved performance, reduced memory usage, eliminated magic numbers

---

## Phase 5: Testing & Documentation (Week 6)
**Priority**: 🟡 Medium  
**Risk**: Low (additive changes)

### 5.1 Comprehensive Testing Strategy
**Problem**: Limited test coverage  
**Current**: Basic unit tests  
**Target**: >80% code coverage

**Testing Architecture**:
```swift
// Test support
class MockDependencyContainer: DependencyContainer {
    let llmService: LLMService = MockLLMService()
    let storageService: StorageService = MockStorageService()
    let hotkeyService: HotkeyService = MockHotkeyService()
    let permissionService: PermissionService = MockPermissionService()
    let errorReporting: ErrorReporting = MockErrorReporting()
}

// Integration tests
class SettingsIntegrationTests: XCTestCase {
    var container: MockDependencyContainer!
    var viewModel: SettingsViewModel!
    
    override func setUp() {
        super.setUp()
        container = MockDependencyContainer()
        viewModel = SettingsViewModel(dependencies: container)
    }
    
    func testAPIKeyValidationFlow() async {
        // Given
        viewModel.apiKey = "valid-key"
        viewModel.selectedProvider = .openAI
        
        // When
        await viewModel.validateAndSaveAPIKey()
        
        // Then
        XCTAssertTrue(viewModel.validationMessage.contains("✅"))
        XCTAssertFalse(viewModel.isValidating)
    }
}
```

### 5.2 Documentation Enhancement
**Problem**: Limited code documentation  
**Files**: All Swift files

**Documentation Standards**:
```swift
/// Service responsible for managing LLM provider interactions
/// 
/// This service provides a unified interface for interacting with different
/// LLM providers (OpenAI, Anthropic, Google) and handles:
/// - API key validation and storage
/// - Model selection and management
/// - Text processing requests
/// - Error handling and user feedback
///
/// - Important: All methods are async and return Result types for proper error handling
/// - Note: API keys are stored securely using the StorageService
protocol LLMService {
    /// Validates an API key for the specified provider
    /// 
    /// - Parameters:
    ///   - key: The API key to validate
    ///   - provider: The LLM provider to validate against
    /// - Returns: Result indicating success or validation error
    /// - Important: This method makes a network request and may take several seconds
    func validateAPIKey(_ key: String, for provider: LLMProvider) async -> Result<Void, PotterError>
}
```

### 5.3 Accessibility Improvements
**Problem**: Limited accessibility support  
**Files**: UI components

**Accessibility Enhancements**:
```swift
extension View {
    func makeAccessible(
        label: String,
        hint: String? = nil,
        traits: AccessibilityTraits = []
    ) -> some View {
        self
            .accessibility(label: Text(label))
            .accessibility(hint: hint.map(Text.init))
            .accessibility(addTraits: traits)
    }
}

// Usage
hotkeyPill("⌘", isActive: false)
    .makeAccessible(
        label: "Command key",
        hint: "Part of the global hotkey combination. Tap to change.",
        traits: .isButton
    )
```

**Expected Outcome**: High test coverage, comprehensive documentation, full accessibility support

---

## 📁 New File Structure

```
swift-potter/Sources/
├── Core/
│   ├── Services/
│   │   ├── LLMService.swift
│   │   ├── StorageService.swift
│   │   ├── HotkeyService.swift
│   │   ├── PermissionService.swift
│   │   └── ErrorReportingService.swift
│   ├── Models/
│   │   ├── AppSettings.swift
│   │   ├── LLMProvider.swift
│   │   ├── Prompt.swift
│   │   └── Errors.swift
│   └── Utils/
│       ├── Constants.swift
│       ├── TimerManager.swift
│       ├── ResourceManager.swift
│       └── Extensions/
├── UI/
│   ├── ViewModels/
│   │   ├── SettingsViewModel.swift
│   │   ├── PromptsViewModel.swift
│   │   └── AboutViewModel.swift
│   ├── Views/
│   │   ├── SettingsWindow/
│   │   ├── Components/
│   │   └── Helpers/
│   └── Coordinators/
├── Infrastructure/
│   ├── Storage/
│   │   ├── KeychainStorage.swift
│   │   ├── UserDefaultsStorage.swift
│   │   └── FileStorage.swift
│   ├── Network/
│   │   ├── HTTPClient.swift
│   │   ├── APIClients/
│   │   └── Models/
│   └── System/
│       ├── ProcessManager.swift
│       ├── PermissionManager.swift
│       └── HotkeyManager.swift
├── Application/
│   ├── AppDelegate.swift
│   ├── DependencyContainer.swift
│   └── main.swift
├── Resources/
└── Tests/
    ├── Unit/
    ├── Integration/
    └── Mocks/
```

---

## 🔄 Migration Strategy

### Phase-by-Phase Migration
1. **Create new structure** alongside existing code
2. **Migrate one service at a time** with feature flags
3. **Update UI components** to use new services
4. **Remove old code** once new code is proven
5. **Add comprehensive tests** for each migrated component

### Risk Mitigation
- **Feature flags** for new vs old code paths
- **Comprehensive testing** at each phase
- **Rollback capability** at any point
- **User acceptance testing** throughout process

### Testing Strategy
- **Unit tests** for all new services
- **Integration tests** for critical workflows
- **Manual testing** against existing test plan
- **Performance testing** to ensure no regression

---

## 📊 Expected Outcomes

### Code Quality Metrics
- **Lines of Code**: ~5,000 (from 4,144) - growth due to proper separation
- **Cyclomatic Complexity**: <10 per method (from ~15 average)
- **Test Coverage**: >80% (from ~40%)
- **Documentation Coverage**: >90% (from ~10%)

### Performance Improvements
- **Startup Time**: <2 seconds (from ~3 seconds)
- **Memory Usage**: <40MB (from ~50MB)
- **Network Efficiency**: 50% fewer API calls through caching
- **UI Responsiveness**: <100ms for all interactions

### Maintainability Improvements
- **Single Responsibility**: Each class/method has one clear purpose
- **Dependency Injection**: Easy to mock and test
- **Error Handling**: Consistent patterns throughout
- **Documentation**: Clear API documentation for all public interfaces

### Security Improvements
- **Zero API Key Exposure**: No sensitive data in logs
- **Secure Network**: All APIs use proper authentication headers
- **Atomic Operations**: No data loss during migrations
- **Input Validation**: Comprehensive validation for all inputs

---

## ⚠️ Risks & Mitigation

### High Risk Items
1. **Breaking existing functionality**
   - **Mitigation**: Comprehensive test suite, feature flags, rollback capability
2. **Performance regression**
   - **Mitigation**: Performance testing at each phase
3. **User interface changes**
   - **Mitigation**: Preserve existing UI patterns, add features gradually

### Medium Risk Items
1. **Complex merge conflicts**
   - **Mitigation**: Small, focused commits with clear scope
2. **Testing gaps**
   - **Mitigation**: Test-driven development, code review process
3. **Documentation maintenance**
   - **Mitigation**: Documentation as part of definition of done

### Low Risk Items
1. **Code style consistency**
   - **Mitigation**: SwiftLint integration, code review guidelines
2. **Performance optimization complexity**
   - **Mitigation**: Profile before optimizing, measure improvements

---

## 🎯 Success Criteria

### Must Have (Definition of Done)
- ✅ All existing features work identically
- ✅ All security vulnerabilities fixed
- ✅ Zero force unwraps in production code
- ✅ >80% test coverage
- ✅ Consistent error handling throughout
- ✅ All magic numbers eliminated

### Should Have (Quality Goals)
- ✅ <2 second startup time
- ✅ <40MB memory usage
- ✅ Clean architecture with proper separation
- ✅ Comprehensive documentation
- ✅ Full accessibility support

### Could Have (Future Improvements)
- ✅ Automated performance testing
- ✅ Continuous integration pipeline
- ✅ Advanced error analytics
- ✅ User usage analytics (privacy-preserving)

---

## 📅 Timeline

| Phase | Duration | Key Deliverables | Risk Level |
|-------|----------|------------------|------------|
| Phase 1 | Week 1 | Security fixes, force unwrap elimination | Low |
| Phase 2 | Week 2 | Error handling standardization | Medium |
| Phase 3 | Week 3-4 | Architecture separation, dependency injection | Medium |
| Phase 4 | Week 5 | Code quality improvements, performance optimization | Low |
| Phase 5 | Week 6 | Testing, documentation, accessibility | Low |

**Total Duration**: 6 weeks  
**Total Effort**: ~150-200 hours (25-35 hours per week)

---

## 🚀 Getting Started

### Immediate Actions (Day 1)
1. **Create refactoring branch**: `git checkout -b refactor/architecture-v2`
2. **Set up new folder structure**: Create Core/, UI/, Infrastructure/ folders
3. **Implement log sanitization**: Fix API key exposure immediately
4. **Add basic unit test framework**: Set up testing infrastructure

### Week 1 Checklist
- [ ] Log sanitization implemented and tested
- [ ] Google API key moved to headers
- [ ] Storage race condition fixed
- [ ] Force unwraps identified and elimination plan created
- [ ] Basic error types defined
- [ ] Unit test infrastructure set up

### Tools & Resources
- **Static Analysis**: SwiftLint for code style consistency
- **Testing**: XCTest for unit and integration tests
- **Documentation**: Swift-DocC for API documentation
- **Performance**: Instruments for memory and performance profiling

---

*Potter Refactoring Plan v2.0.0*  
*Comprehensive architecture improvement strategy*  
*Created: June 19, 2025*
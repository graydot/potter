import XCTest
@testable import Potter

// MARK: - Mock Implementations

/// Mock implementation of PromptRepository for testing
class MockPromptRepository: PromptRepository {
    var prompts: [PromptItem] = []
    var currentPromptName: String = ""

    // Track calls for verification
    var loadPromptsCalled = false
    var savePromptCalled = false
    var deletePromptCalled = false
    var getPromptCalled = false
    var getCurrentPromptTextCalled = false

    // Configurable return values
    var loadPromptsResult: [PromptItem] = []
    var savePromptResult: Result<Void, PromptServiceError> = .success(())
    var deletePromptResult: Result<Void, PromptServiceError> = .success(())
    var getPromptResult: PromptItem? = nil
    var getCurrentPromptTextResult: String? = nil

    func loadPrompts() -> [PromptItem] {
        loadPromptsCalled = true
        prompts = loadPromptsResult
        return loadPromptsResult
    }

    func savePrompt(_ prompt: PromptItem, at index: Int?) -> Result<Void, PromptServiceError> {
        savePromptCalled = true
        return savePromptResult
    }

    func deletePrompt(at index: Int) -> Result<Void, PromptServiceError> {
        deletePromptCalled = true
        return deletePromptResult
    }

    func getPrompt(named name: String) -> PromptItem? {
        getPromptCalled = true
        return getPromptResult
    }

    func getCurrentPromptText() -> String? {
        getCurrentPromptTextCalled = true
        return getCurrentPromptTextResult
    }
}

/// Mock implementation of KeyValidationService for testing
class MockKeyValidationService: KeyValidationService {
    // Track calls
    var getAPIKeyCalled = false
    var isProviderConfiguredCalled = false
    var saveAPIKeyCalled = false
    var validateAndSaveAPIKeyCalled = false
    var getValidationStateCalled = false

    // Configurable return values
    var getAPIKeyResult: String? = nil
    var isProviderConfiguredResult: Bool = false
    var saveAPIKeyResult: Result<Void, APIKeyServiceError> = .success(())
    var validateAndSaveAPIKeyResult: ValidationResult = .success
    var getValidationStateResult: ValidationState = .notValidated

    // Required protocol properties (new in KeyValidationService)
    var validationStates: [LLMProvider: ValidationState] = {
        var states: [LLMProvider: ValidationState] = [:]
        for provider in LLMProvider.allCases { states[provider] = .notValidated }
        return states
    }()
    var isValidating: Bool = false

    func getAPIKey(for provider: LLMProvider) -> String? {
        getAPIKeyCalled = true
        return getAPIKeyResult
    }

    func isProviderConfigured(_ provider: LLMProvider) -> Bool {
        isProviderConfiguredCalled = true
        return isProviderConfiguredResult
    }

    func saveAPIKey(_ key: String, for provider: LLMProvider) -> Result<Void, APIKeyServiceError> {
        saveAPIKeyCalled = true
        return saveAPIKeyResult
    }

    func validateAndSaveAPIKey(_ key: String, for provider: LLMProvider, using model: LLMModel?) async -> ValidationResult {
        validateAndSaveAPIKeyCalled = true
        return validateAndSaveAPIKeyResult
    }

    func getValidationState(for provider: LLMProvider) -> ValidationState {
        getValidationStateCalled = true
        return getValidationStateResult
    }
}

/// Mock implementation of PermissionChecker for testing
class MockPermissionChecker: PermissionChecker {
    // Track calls
    var hasRequiredPermissionsCalled = false
    var checkAllPermissionsCalled = false

    // Configurable return values
    var hasRequiredPermissionsResult: Bool = true
    var accessibilityStatus: PermissionStatus = .granted

    func hasRequiredPermissions() -> Bool {
        hasRequiredPermissionsCalled = true
        return hasRequiredPermissionsResult
    }

    func checkAllPermissions() {
        checkAllPermissionsCalled = true
    }
}

// MARK: - Protocol Existence Tests

/// Tests that verify protocols exist and have the correct signatures.
/// These tests will FAIL until the protocols are defined in source code.
class ProtocolExistenceTests: TestBase {

    // MARK: - PromptRepository Protocol

    func testPromptRepositoryProtocolExists() {
        // Verify the protocol type exists and can be used as a type constraint
        let mock: any PromptRepository = MockPromptRepository()
        XCTAssertNotNil(mock)
    }

    func testPromptRepositoryHasPromptsProperty() {
        let mock = MockPromptRepository()
        let repo: any PromptRepository = mock
        // Access the prompts property - proves it exists on the protocol
        let prompts: [PromptItem] = repo.prompts
        XCTAssertTrue(prompts.isEmpty)
    }

    func testPromptRepositoryHasCurrentPromptNameProperty() {
        var mock = MockPromptRepository()
        mock.currentPromptName = "Test Prompt"
        let repo: any PromptRepository = mock
        XCTAssertEqual(repo.currentPromptName, "Test Prompt")
    }

    func testPromptRepositoryCurrentPromptNameIsSettable() {
        var repo: any PromptRepository = MockPromptRepository()
        repo.currentPromptName = "New Name"
        XCTAssertEqual(repo.currentPromptName, "New Name")
    }

    func testPromptRepositoryHasLoadPromptsMethod() {
        let repo: any PromptRepository = MockPromptRepository()
        let result: [PromptItem] = repo.loadPrompts()
        XCTAssertTrue(result.isEmpty)
    }

    func testPromptRepositoryHasSavePromptMethod() {
        let repo: any PromptRepository = MockPromptRepository()
        let prompt = PromptItem(name: "Test", prompt: "Test content")
        let result: Result<Void, PromptServiceError> = repo.savePrompt(prompt, at: nil)
        XCTAssertNoThrow(try result.get())
    }

    func testPromptRepositoryHasDeletePromptMethod() {
        let repo: any PromptRepository = MockPromptRepository()
        let result: Result<Void, PromptServiceError> = repo.deletePrompt(at: 0)
        XCTAssertNoThrow(try result.get())
    }

    func testPromptRepositoryHasGetPromptByNameMethod() {
        let repo: any PromptRepository = MockPromptRepository()
        let result: PromptItem? = repo.getPrompt(named: "Test")
        XCTAssertNil(result)
    }

    func testPromptRepositoryHasGetCurrentPromptTextMethod() {
        let repo: any PromptRepository = MockPromptRepository()
        let result: String? = repo.getCurrentPromptText()
        XCTAssertNil(result)
    }

    // MARK: - KeyValidationService Protocol

    func testKeyValidationServiceProtocolExists() {
        let mock: any KeyValidationService = MockKeyValidationService()
        XCTAssertNotNil(mock)
    }

    func testKeyValidationServiceHasGetAPIKeyMethod() {
        let service: any KeyValidationService = MockKeyValidationService()
        let result: String? = service.getAPIKey(for: .anthropic)
        XCTAssertNil(result)
    }

    func testKeyValidationServiceHasIsProviderConfiguredMethod() {
        let service: any KeyValidationService = MockKeyValidationService()
        let result: Bool = service.isProviderConfigured(.anthropic)
        XCTAssertFalse(result)
    }

    func testKeyValidationServiceHasSaveAPIKeyMethod() {
        let service: any KeyValidationService = MockKeyValidationService()
        let result: Result<Void, APIKeyServiceError> = service.saveAPIKey("test-key", for: .anthropic)
        XCTAssertNoThrow(try result.get())
    }

    func testKeyValidationServiceHasValidateAndSaveAPIKeyMethod() async {
        let service: any KeyValidationService = MockKeyValidationService()
        let result: ValidationResult = await service.validateAndSaveAPIKey("test-key", for: .anthropic, using: nil)
        XCTAssertTrue(result.isSuccess)
    }

    func testKeyValidationServiceHasGetValidationStateMethod() {
        let service: any KeyValidationService = MockKeyValidationService()
        let result: ValidationState = service.getValidationState(for: .anthropic)
        XCTAssertEqual(result, .notValidated)
    }

    // MARK: - PermissionChecker Protocol

    func testPermissionCheckerProtocolExists() {
        let mock: any PermissionChecker = MockPermissionChecker()
        XCTAssertNotNil(mock)
    }

    func testPermissionCheckerHasHasRequiredPermissionsMethod() {
        let checker: any PermissionChecker = MockPermissionChecker()
        let result: Bool = checker.hasRequiredPermissions()
        XCTAssertTrue(result)
    }

    func testPermissionCheckerHasCheckAllPermissionsMethod() {
        let checker: any PermissionChecker = MockPermissionChecker()
        checker.checkAllPermissions()
        // Method exists and is callable - test passes if it compiles
    }

    func testPermissionCheckerHasAccessibilityStatusProperty() {
        let checker: any PermissionChecker = MockPermissionChecker()
        let status: PermissionStatus = checker.accessibilityStatus
        XCTAssertEqual(status, .granted)
    }
}

// MARK: - Conformance Tests

/// Tests that verify concrete types conform to their protocols.
/// These tests will FAIL until conformance declarations are added.
class ConformanceTests: TestBase {

    func testPromptServiceConformsToPromptRepository() {
        // PromptService.shared should be usable as a PromptRepository
        let service: any PromptRepository = PromptService.shared
        XCTAssertNotNil(service)
    }

    func testAPIKeyServiceConformsToKeyValidationService() {
        // APIKeyService.shared should be usable as a KeyValidationService
        let service: any KeyValidationService = APIKeyService.shared
        XCTAssertNotNil(service)
    }

    @MainActor
    func testPermissionManagerConformsToPermissionChecker() {
        // PermissionManager.shared should be usable as a PermissionChecker
        let checker: any PermissionChecker = PermissionManager.shared
        XCTAssertNotNil(checker)
    }
}

// MARK: - Mock Behavior Tests

/// Tests that verify mock implementations work correctly and can stand in for real services.
class MockBehaviorTests: TestBase {

    // MARK: - MockPromptRepository Behavior

    func testMockPromptRepositoryTracksLoadPromptsCalls() {
        let mock = MockPromptRepository()
        XCTAssertFalse(mock.loadPromptsCalled)
        _ = mock.loadPrompts()
        XCTAssertTrue(mock.loadPromptsCalled)
    }

    func testMockPromptRepositoryReturnsConfiguredPrompts() {
        let mock = MockPromptRepository()
        let expectedPrompts = [
            PromptItem(name: "Prompt 1", prompt: "Content 1"),
            PromptItem(name: "Prompt 2", prompt: "Content 2")
        ]
        mock.loadPromptsResult = expectedPrompts
        let result = mock.loadPrompts()
        XCTAssertEqual(result.count, 2)
        XCTAssertEqual(result[0].name, "Prompt 1")
        XCTAssertEqual(result[1].name, "Prompt 2")
    }

    func testMockPromptRepositoryReturnsConfiguredSaveResult() {
        let mock = MockPromptRepository()
        mock.savePromptResult = .failure(.duplicatePromptName)
        let prompt = PromptItem(name: "Test", prompt: "Content")
        let result = mock.savePrompt(prompt, at: nil)
        if case .failure(.duplicatePromptName) = result {
            // Expected
        } else {
            XCTFail("Expected duplicatePromptName error")
        }
    }

    func testMockPromptRepositoryReturnsConfiguredDeleteResult() {
        let mock = MockPromptRepository()
        mock.deletePromptResult = .failure(.cannotDeleteLastPrompt)
        let result = mock.deletePrompt(at: 0)
        if case .failure(.cannotDeleteLastPrompt) = result {
            // Expected
        } else {
            XCTFail("Expected cannotDeleteLastPrompt error")
        }
    }

    func testMockPromptRepositoryReturnsConfiguredGetPromptResult() {
        let mock = MockPromptRepository()
        let expectedPrompt = PromptItem(name: "Found", prompt: "Found content")
        mock.getPromptResult = expectedPrompt
        let result = mock.getPrompt(named: "Found")
        XCTAssertEqual(result?.name, "Found")
        XCTAssertTrue(mock.getPromptCalled)
    }

    func testMockPromptRepositoryReturnsConfiguredCurrentPromptText() {
        let mock = MockPromptRepository()
        mock.getCurrentPromptTextResult = "System prompt text"
        let result = mock.getCurrentPromptText()
        XCTAssertEqual(result, "System prompt text")
        XCTAssertTrue(mock.getCurrentPromptTextCalled)
    }

    // MARK: - MockKeyValidationService Behavior

    func testMockKeyValidationServiceTracksGetAPIKeyCalls() {
        let mock = MockKeyValidationService()
        XCTAssertFalse(mock.getAPIKeyCalled)
        _ = mock.getAPIKey(for: .anthropic)
        XCTAssertTrue(mock.getAPIKeyCalled)
    }

    func testMockKeyValidationServiceReturnsConfiguredAPIKey() {
        let mock = MockKeyValidationService()
        mock.getAPIKeyResult = "sk-test-key-123"
        let result = mock.getAPIKey(for: .anthropic)
        XCTAssertEqual(result, "sk-test-key-123")
    }

    func testMockKeyValidationServiceReturnsConfiguredProviderStatus() {
        let mock = MockKeyValidationService()
        mock.isProviderConfiguredResult = true
        XCTAssertTrue(mock.isProviderConfigured(.google))
        XCTAssertTrue(mock.isProviderConfiguredCalled)
    }

    func testMockKeyValidationServiceReturnsConfiguredSaveResult() {
        let mock = MockKeyValidationService()
        mock.saveAPIKeyResult = .failure(.storageError(NSError(domain: "test", code: 1)))
        let result = mock.saveAPIKey("key", for: .anthropic)
        if case .failure = result {
            // Expected
        } else {
            XCTFail("Expected failure result")
        }
    }

    func testMockKeyValidationServiceReturnsConfiguredValidationResult() async {
        let mock = MockKeyValidationService()
        mock.validateAndSaveAPIKeyResult = .failure(.invalidKey("Bad key"))
        let result = await mock.validateAndSaveAPIKey("bad", for: .anthropic, using: nil)
        XCTAssertFalse(result.isSuccess)
        XCTAssertTrue(mock.validateAndSaveAPIKeyCalled)
    }

    func testMockKeyValidationServiceReturnsConfiguredValidationState() {
        let mock = MockKeyValidationService()
        mock.getValidationStateResult = .valid
        let result = mock.getValidationState(for: .anthropic)
        XCTAssertEqual(result, .valid)
        XCTAssertTrue(mock.getValidationStateCalled)
    }

    // MARK: - MockPermissionChecker Behavior

    func testMockPermissionCheckerTracksHasRequiredPermissionsCalls() {
        let mock = MockPermissionChecker()
        XCTAssertFalse(mock.hasRequiredPermissionsCalled)
        _ = mock.hasRequiredPermissions()
        XCTAssertTrue(mock.hasRequiredPermissionsCalled)
    }

    func testMockPermissionCheckerReturnsConfiguredPermissionStatus() {
        let mock = MockPermissionChecker()
        mock.hasRequiredPermissionsResult = false
        XCTAssertFalse(mock.hasRequiredPermissions())
    }

    func testMockPermissionCheckerTracksCheckAllPermissionsCalls() {
        let mock = MockPermissionChecker()
        XCTAssertFalse(mock.checkAllPermissionsCalled)
        mock.checkAllPermissions()
        XCTAssertTrue(mock.checkAllPermissionsCalled)
    }

    func testMockPermissionCheckerReturnsConfiguredAccessibilityStatus() {
        let mock = MockPermissionChecker()
        mock.accessibilityStatus = .denied
        XCTAssertEqual(mock.accessibilityStatus, .denied)
    }
}

// MARK: - Polymorphism Tests

/// Tests that verify mocks can be used interchangeably with real implementations
/// through protocol-typed parameters. These prove dependency injection works.
class PolymorphismTests: TestBase {

    // MARK: - Helper functions that accept protocol types

    /// A function that operates on any PromptRepository
    private func getPromptCount(from repository: any PromptRepository) -> Int {
        return repository.prompts.count
    }

    /// A function that loads and returns prompts from any PromptRepository
    private func loadAllPrompts(from repository: any PromptRepository) -> [PromptItem] {
        return repository.loadPrompts()
    }

    /// A function that checks provider configuration via any KeyValidationService
    private func checkProviderReady(_ provider: LLMProvider, service: any KeyValidationService) -> Bool {
        return service.isProviderConfigured(provider)
    }

    /// A function that checks permissions via any PermissionChecker
    private func isAppReady(checker: any PermissionChecker) -> Bool {
        return checker.hasRequiredPermissions()
    }

    // MARK: - Tests using mocks through protocol-typed parameters

    func testMockPromptRepositoryWorksInProtocolTypedFunction() {
        let mock = MockPromptRepository()
        mock.prompts = [
            PromptItem(name: "A", prompt: "Prompt A"),
            PromptItem(name: "B", prompt: "Prompt B"),
            PromptItem(name: "C", prompt: "Prompt C")
        ]
        let count = getPromptCount(from: mock)
        XCTAssertEqual(count, 3)
    }

    func testMockPromptRepositoryLoadPromptsWorksPolymorphically() {
        let mock = MockPromptRepository()
        mock.loadPromptsResult = [PromptItem(name: "Loaded", prompt: "Content")]
        let prompts = loadAllPrompts(from: mock)
        XCTAssertEqual(prompts.count, 1)
        XCTAssertEqual(prompts.first?.name, "Loaded")
    }

    func testRealPromptServiceWorksInProtocolTypedFunction() {
        // PromptService.shared should also work in the same function
        let count = getPromptCount(from: PromptService.shared)
        // We don't assert a specific count - just that it compiles and runs
        XCTAssertGreaterThanOrEqual(count, 0)
    }

    func testMockKeyValidationServiceWorksInProtocolTypedFunction() {
        let mock = MockKeyValidationService()
        mock.isProviderConfiguredResult = true
        let ready = checkProviderReady(.anthropic, service: mock)
        XCTAssertTrue(ready)
    }

    func testRealAPIKeyServiceWorksInProtocolTypedFunction() {
        // APIKeyService.shared should also work in the same function
        let ready = checkProviderReady(.anthropic, service: APIKeyService.shared)
        // Just verify it compiles and runs - don't assert specific value
        _ = ready
    }

    func testMockPermissionCheckerWorksInProtocolTypedFunction() {
        let mock = MockPermissionChecker()
        mock.hasRequiredPermissionsResult = true
        let ready = isAppReady(checker: mock)
        XCTAssertTrue(ready)
    }

    @MainActor
    func testRealPermissionManagerWorksInProtocolTypedFunction() {
        // PermissionManager.shared should also work in the same function
        let ready = isAppReady(checker: PermissionManager.shared)
        // Just verify it compiles and runs
        _ = ready
    }

    // MARK: - Swappability tests

    func testCanSwapMockForRealPromptRepository() {
        // Demonstrate that a variable typed as the protocol can hold either
        var repo: any PromptRepository

        // Start with mock
        let mock = MockPromptRepository()
        mock.prompts = [PromptItem(name: "Mock", prompt: "Mock content")]
        repo = mock
        XCTAssertEqual(repo.prompts.first?.name, "Mock")

        // Swap to real implementation
        repo = PromptService.shared
        XCTAssertNotNil(repo.prompts)
    }

    func testCanSwapMockForRealKeyValidationService() {
        var service: any KeyValidationService

        // Start with mock
        let mock = MockKeyValidationService()
        mock.isProviderConfiguredResult = true
        service = mock
        XCTAssertTrue(service.isProviderConfigured(.anthropic))

        // Swap to real implementation
        service = APIKeyService.shared
        _ = service.isProviderConfigured(.anthropic)
    }

    @MainActor
    func testCanSwapMockForRealPermissionChecker() {
        var checker: any PermissionChecker

        // Start with mock
        let mock = MockPermissionChecker()
        mock.accessibilityStatus = .granted
        checker = mock
        XCTAssertEqual(checker.accessibilityStatus, .granted)

        // Swap to real implementation
        checker = PermissionManager.shared
        _ = checker.accessibilityStatus
    }
}

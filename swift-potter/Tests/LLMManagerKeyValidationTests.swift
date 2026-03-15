import Testing
import Foundation
@testable import Potter

// MARK: - MockKeyValidationServiceDI

/// Mock conforming to KeyValidationService for testing LLMManager DI.
final class MockKeyValidationServiceDI: KeyValidationService {

    // MARK: - State tracking

    var validationStates: [LLMProvider: ValidationState] = {
        var states: [LLMProvider: ValidationState] = [:]
        for provider in LLMProvider.allCases {
            states[provider] = .notValidated
        }
        return states
    }()

    var isValidating: Bool = false

    // Stored keys (keyed by provider)
    private var storedKeys: [LLMProvider: String] = [:]

    // Call-tracking
    var getAPIKeyCallCount = 0
    var lastGetAPIKeyProvider: LLMProvider?

    var isProviderConfiguredCallCount = 0
    var lastIsProviderConfiguredProvider: LLMProvider?

    var saveAPIKeyCallCount = 0
    var lastSaveAPIKeyKey: String?
    var lastSaveAPIKeyProvider: LLMProvider?
    var saveAPIKeyShouldFail = false

    var validateAndSaveCallCount = 0
    var lastValidateAndSaveKey: String?
    var lastValidateAndSaveProvider: LLMProvider?
    var lastValidateAndSaveModel: LLMModel?
    var validateAndSaveResult: ValidationResult = .success

    var getValidationStateCallCount = 0
    var lastGetValidationStateProvider: LLMProvider?

    // MARK: - KeyValidationService conformance

    func getAPIKey(for provider: LLMProvider) -> String? {
        getAPIKeyCallCount += 1
        lastGetAPIKeyProvider = provider
        return storedKeys[provider]
    }

    func isProviderConfigured(_ provider: LLMProvider) -> Bool {
        isProviderConfiguredCallCount += 1
        lastIsProviderConfiguredProvider = provider
        if case .valid = validationStates[provider] ?? .notValidated {
            return true
        }
        return storedKeys[provider].map { !$0.isEmpty } ?? false
    }

    func saveAPIKey(_ key: String, for provider: LLMProvider) -> Result<Void, APIKeyServiceError> {
        saveAPIKeyCallCount += 1
        lastSaveAPIKeyKey = key
        lastSaveAPIKeyProvider = provider
        if saveAPIKeyShouldFail {
            return .failure(.storageError(NSError(domain: "MockError", code: 1, userInfo: [NSLocalizedDescriptionKey: "Mock storage failure"])))
        }
        storedKeys[provider] = key
        return .success(())
    }

    func validateAndSaveAPIKey(_ key: String, for provider: LLMProvider, using model: LLMModel?) async -> ValidationResult {
        validateAndSaveCallCount += 1
        lastValidateAndSaveKey = key
        lastValidateAndSaveProvider = provider
        lastValidateAndSaveModel = model
        if case .success = validateAndSaveResult {
            storedKeys[provider] = key
            validationStates[provider] = .valid
        } else {
            validationStates[provider] = ValidationState.invalid("Mock invalid key")
        }
        return validateAndSaveResult
    }

    func getValidationState(for provider: LLMProvider) -> ValidationState {
        getValidationStateCallCount += 1
        lastGetValidationStateProvider = provider
        return validationStates[provider] ?? .notValidated
    }

    // MARK: - Helpers

    func setKey(_ key: String, for provider: LLMProvider) {
        storedKeys[provider] = key
    }

    func setValidationState(_ state: ValidationState, for provider: LLMProvider) {
        validationStates[provider] = state
    }
}

// MARK: - LLMManager Key Validation DI Tests

@Suite("LLMManager Key Validation Dependency Injection")
@MainActor
struct LLMManagerKeyValidationTests {

    // Convenience: create a fresh mock + manager pair with StorageAdapter
    // configured to use UserDefaults (avoids keychain prompts in tests).
    func makeSUT() -> (manager: LLMManager, mock: MockKeyValidationServiceDI) {
        StorageAdapter.shared.forceUserDefaultsForTesting = true
        let testDefaults = UserDefaults(suiteName: "com.potter.tests.di.\(UUID().uuidString)")
        StorageAdapter.shared.testUserDefaults = testDefaults
        let mock = MockKeyValidationServiceDI()
        let manager = LLMManager(keyValidationService: mock)
        return (manager, mock)
    }

    func tearDownSUT() {
        StorageAdapter.shared.forceUserDefaultsForTesting = false
        StorageAdapter.shared.testUserDefaults = nil
    }

    // MARK: - Test 1: LLMManager uses the injected validation service

    @Test("LLMManager uses injected validation service instead of APIKeyService.shared")
    func injectedServiceIsUsed() {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        mock.setKey("injected-key", for: LLMProvider.anthropic)
        let key = manager.getAPIKey(for: LLMProvider.anthropic)

        #expect(key == "injected-key", "getAPIKey should route through the injected mock")
        #expect(mock.getAPIKeyCallCount > 0, "Mock's getAPIKey should have been called")
    }

    // MARK: - Test 2: LLMManager correctly handles a valid API key from the mock

    @Test("LLMManager treats provider as configured when mock returns valid state")
    func validAPIKeyFromMock() {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        mock.setValidationState(ValidationState.valid, for: LLMProvider.anthropic)

        #expect(manager.isProviderConfigured(LLMProvider.anthropic) == true,
                "isProviderConfigured should return true when mock has a valid state")
        #expect(manager.hasValidProvider() == true,
                "hasValidProvider should return true for the selected (anthropic) provider")
    }

    // MARK: - Test 3: LLMManager correctly handles invalid/missing API key from mock

    @Test("LLMManager treats provider as not configured when mock has no key or invalid state")
    func invalidOrMissingAPIKeyFromMock() {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        // Default mock state: notValidated, no stored key
        #expect(manager.isProviderConfigured(LLMProvider.anthropic) == false,
                "isProviderConfigured should return false when no key or valid state in mock")
        #expect(manager.hasValidProvider() == false,
                "hasValidProvider should return false when provider is not configured")

        // Explicitly mark as invalid
        mock.setValidationState(ValidationState.invalid("bad key"), for: LLMProvider.anthropic)
        #expect(manager.isProviderConfigured(LLMProvider.anthropic) == false,
                "isProviderConfigured should return false when validation state is invalid")
    }

    // MARK: - Test 4: Mock receives the correct provider when a key is requested

    @Test("Mock receives correct provider when LLMManager requests an API key")
    func mockReceivesCorrectProvider() {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        _ = manager.getAPIKey(for: LLMProvider.anthropic)

        #expect(mock.lastGetAPIKeyProvider == LLMProvider.anthropic,
                "Mock should have been queried with the .anthropic provider")
    }

    // MARK: - Test 5: validationStates is delegated to the mock

    @Test("LLMManager.validationStates delegates to the injected mock")
    func validationStatesDelegatedToMock() {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        mock.setValidationState(ValidationState.validating, for: LLMProvider.google)

        let states = manager.validationStates
        #expect(states[LLMProvider.google] == ValidationState.validating,
                "LLMManager.validationStates should reflect the mock's state for .google")
    }

    // MARK: - Test 6: getCurrentValidationState queries the mock with selectedProvider

    @Test("getCurrentValidationState returns mock's state for the selected provider")
    func getCurrentValidationStateQueriesMock() {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        manager.selectedProvider = LLMProvider.anthropic
        mock.setValidationState(ValidationState.valid, for: LLMProvider.anthropic)

        let state = manager.getCurrentValidationState()

        #expect(state == ValidationState.valid,
                "getCurrentValidationState should return .valid from the mock")
        #expect(mock.lastGetValidationStateProvider == LLMProvider.anthropic,
                "Mock should have been queried for the .anthropic provider")
    }

    // MARK: - Test 7: setAPIKey routes through the mock's saveAPIKey

    @Test("setAPIKey delegates to mock's saveAPIKey with correct arguments")
    func setAPIKeyDelegatesToMock() {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        manager.setAPIKey("sk-test-123", for: LLMProvider.anthropic)

        #expect(mock.saveAPIKeyCallCount == 1,
                "Mock's saveAPIKey should be called exactly once")
        #expect(mock.lastSaveAPIKeyKey == "sk-test-123",
                "Mock should receive the exact key string")
        #expect(mock.lastSaveAPIKeyProvider == LLMProvider.anthropic,
                "Mock should receive the correct provider")
    }

    // MARK: - Test 8: validateAndSaveAPIKey with empty key results in non-valid state

    @Test("validateAndSaveAPIKey with empty string does not result in a valid state")
    func emptyKeyResultsInNonValidState() async {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        // The mock's validateAndSaveAPIKey will be called regardless;
        // configure it to return failure (reflecting that an empty key should fail).
        mock.validateAndSaveResult = ValidationResult.failure(APIKeyValidationError.invalidKey("empty key"))

        await manager.validateAndSaveAPIKey("", for: LLMProvider.anthropic)

        let state = manager.validationStates[LLMProvider.anthropic]
        #expect(state?.isValid == false,
                "Empty key should not result in a valid state")
    }

    // MARK: - Test 9: validateAndSaveAPIKey success path sets valid state via mock

    @Test("validateAndSaveAPIKey success updates state to valid via mock")
    func validateAndSaveSuccessPath() async {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        mock.validateAndSaveResult = ValidationResult.success

        await manager.validateAndSaveAPIKey("sk-valid-key", for: LLMProvider.anthropic)

        #expect(mock.validateAndSaveCallCount == 1,
                "Mock's validateAndSaveAPIKey should be called once")
        #expect(mock.lastValidateAndSaveKey == "sk-valid-key",
                "Mock should receive the correct key")
        #expect(mock.lastValidateAndSaveProvider == LLMProvider.anthropic,
                "Mock should receive the correct provider")
        #expect(manager.validationStates[LLMProvider.anthropic] == ValidationState.valid,
                "Validation state should be .valid after a successful mock validation")
    }

    // MARK: - Test 10: validateAndSaveAPIKey failure path leaves state invalid

    @Test("validateAndSaveAPIKey failure leaves state as invalid via mock")
    func validateAndSaveFailurePath() async {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        mock.validateAndSaveResult = ValidationResult.failure(APIKeyValidationError.invalidKey("bad key"))

        await manager.validateAndSaveAPIKey("sk-bad-key", for: LLMProvider.anthropic)

        let state = manager.validationStates[LLMProvider.anthropic]
        #expect(state?.isValid == false,
                "Validation state should not be valid after a failed mock validation")
    }

    // MARK: - Test 11: Default init (nil service) still works — backward compat

    @Test("LLMManager() with no keyValidationService argument is backward compatible")
    func backwardCompatInit() {
        StorageAdapter.shared.forceUserDefaultsForTesting = true
        defer {
            StorageAdapter.shared.forceUserDefaultsForTesting = false
            StorageAdapter.shared.testUserDefaults = nil
        }
        let manager = LLMManager()
        #expect(manager.selectedProvider == LLMProvider.anthropic,
                "Default init should set selectedProvider to .anthropic")
        #expect(manager.selectedModel != nil,
                "Default init should select a default model")
    }

    // MARK: - Test 12: isValidating reflects mock's isValidating

    @Test("LLMManager.isValidating reflects mock's isValidating flag")
    func isValidatingReflectsMock() {
        let (manager, mock) = makeSUT()
        defer { tearDownSUT() }

        mock.isValidating = false
        #expect(manager.isValidating == false,
                "isValidating should be false when mock and local flag are both false")

        mock.isValidating = true
        #expect(manager.isValidating == true,
                "isValidating should be true when mock reports isValidating = true")
    }
}

import Foundation

// MARK: - PromptRepository Protocol

/// Abstraction over prompt storage and retrieval.
/// Implemented by PromptService; mockable for testing.
protocol PromptRepository: AnyObject {
    var prompts: [PromptItem] { get }
    var currentPromptName: String { get set }

    func loadPrompts() -> [PromptItem]
    func savePrompt(_ prompt: PromptItem, at index: Int?) -> Result<Void, PromptServiceError>
    func deletePrompt(at index: Int) -> Result<Void, PromptServiceError>
    func getPrompt(named name: String) -> PromptItem?
    func getCurrentPromptText() -> String?
}

// MARK: - KeyValidationService Protocol

/// Abstraction over API key management and validation.
/// Implemented by APIKeyService; mockable for testing.
protocol KeyValidationService: AnyObject {
    func getAPIKey(for provider: LLMProvider) -> String?
    func isProviderConfigured(_ provider: LLMProvider) -> Bool
    func saveAPIKey(_ key: String, for provider: LLMProvider) -> Result<Void, APIKeyServiceError>
    func validateAndSaveAPIKey(_ key: String, for provider: LLMProvider, using model: LLMModel?) async -> ValidationResult
    func getValidationState(for provider: LLMProvider) -> ValidationState
}

// MARK: - PermissionChecker Protocol

/// Abstraction over system permission checks.
/// Implemented by PermissionManager; mockable for testing.
protocol PermissionChecker: AnyObject {
    var accessibilityStatus: PermissionStatus { get }
    func hasRequiredPermissions() -> Bool
    func checkAllPermissions()
}

// MARK: - PromptProviding Protocol

/// Provides the current prompt text for text processing.
protocol PromptProviding {
    func getCurrentPromptText() -> String?
    var currentPromptName: String { get }
}

// MARK: - LLMProcessing Protocol

/// Processes text with an LLM given a prompt.
protocol LLMProcessing {
    func processText(_ text: String, prompt: String) async throws -> String
}

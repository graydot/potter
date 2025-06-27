import Foundation

// MARK: - APIKeyService
/// Service class responsible for all API key management business logic
/// Separates API key operations from UI concerns
class APIKeyService: ObservableObject {
    static let shared = APIKeyService()
    
    // MARK: - Published Properties for UI Binding
    @Published var validationStates: [LLMProvider: ValidationState] = [:]
    @Published var isValidating = false
    
    // MARK: - Private Properties
    private var validationCache: [String: ValidationResult] = [:]
    private let cacheTimeout: TimeInterval = 300 // 5 minutes
    
    // MARK: - Initialization
    private init() {
        initializeValidationStates()
    }
    
    // MARK: - Public API
    
    /// Validate an API key for a specific provider
    func validateAPIKey(_ key: String, for provider: LLMProvider) async -> ValidationResult {
        let cacheKey = "\(provider.rawValue):\(key.prefix(8))" // Use prefix for cache key
        
        // Check cache first
        if let cached = validationCache[cacheKey],
           cached.timestamp.timeIntervalSinceNow > -cacheTimeout {
            PotterLogger.shared.debug("api_key", "🎯 Using cached validation result for \(provider.displayName)")
            return cached
        }
        
        // Update UI state
        await MainActor.run {
            isValidating = true
            validationStates[provider] = .validating
        }
        
        let result = await performValidation(key: key, provider: provider)
        
        // Cache the result
        validationCache[cacheKey] = result
        
        // Update UI state
        await MainActor.run {
            isValidating = false
            validationStates[provider] = ValidationState.from(result)
        }
        
        return result
    }
    
    /// Validate and save an API key
    func validateAndSaveAPIKey(_ key: String, for provider: LLMProvider) async -> ValidationResult {
        guard !key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            let result = ValidationResult.failure(.invalidKey("API key cannot be empty"))
            await MainActor.run {
                validationStates[provider] = ValidationState.from(result)
            }
            return result
        }
        
        let result = await validateAPIKey(key, for: provider)
        
        if case .success = result {
            let saveResult = saveAPIKey(key, for: provider)
            if case .failure(let error) = saveResult {
                PotterLogger.shared.error("api_key", "❌ Failed to save API key: \(error)")
                let failedResult = ValidationResult.failure(.storageError(error))
                await MainActor.run {
                    validationStates[provider] = ValidationState.from(failedResult)
                }
                return failedResult
            }
            PotterLogger.shared.info("api_key", "✅ API key validated and saved for \(provider.displayName)")
        }
        
        return result
    }
    
    /// Save an API key for a provider
    func saveAPIKey(_ key: String, for provider: LLMProvider) -> Result<Void, APIKeyServiceError> {
        let storageMethod = SecureAPIKeyStorage.shared.getStorageMethod(for: provider)
        let result = SecureAPIKeyStorage.shared.saveAPIKey(key, for: provider, using: storageMethod)
        
        switch result {
        case .success:
            PotterLogger.shared.info("api_key", "💾 API key saved for \(provider.displayName)")
            return .success(())
        case .failure(let error):
            PotterLogger.shared.error("api_key", "❌ Failed to save API key for \(provider.displayName): \(error)")
            return .failure(.storageError(error))
        }
    }
    
    /// Get an API key for a provider
    func getAPIKey(for provider: LLMProvider) -> String? {
        let result = SecureAPIKeyStorage.shared.loadAPIKey(for: provider)
        switch result {
        case .success(let key):
            if !key.isEmpty {
                PotterLogger.shared.debug("api_key", "🔑 Retrieved API key for \(provider.displayName)")
                return key
            }
            return nil
        case .failure(let error):
            PotterLogger.shared.error("api_key", "❌ Failed to retrieve API key for \(provider.displayName): \(error)")
            return nil
        }
    }
    
    /// Check if a provider is properly configured
    func isProviderConfigured(_ provider: LLMProvider) -> Bool {
        guard let key = getAPIKey(for: provider) else { return false }
        return !key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
    
    /// Get current validation state for a provider
    func getValidationState(for provider: LLMProvider) -> ValidationState {
        return validationStates[provider] ?? .notValidated
    }
    
    /// Clear validation cache
    func clearValidationCache() {
        validationCache.removeAll()
        PotterLogger.shared.debug("api_key", "🗑️ Validation cache cleared")
    }
    
    /// Migrate storage method
    func migrateStorage(to method: StorageMethod) async -> Result<Void, APIKeyServiceError> {
        await MainActor.run {
            isValidating = true
        }
        
        let result = StorageAdapter.shared.migrate(to: method)
        
        await MainActor.run {
            isValidating = false
        }
        
        switch result {
        case .success:
            PotterLogger.shared.info("api_key", "✅ Storage migration successful")
            // Refresh validation states after migration
            refreshValidationStates()
            return .success(())
        case .failure(let error):
            PotterLogger.shared.error("api_key", "❌ Storage migration failed: \(error)")
            return .failure(.migrationError(error))
        }
    }
    
    /// Load provider state (for UI initialization)
    func loadProviderState(for provider: LLMProvider) -> (hasKey: Bool, validationState: ValidationState) {
        let hasKey = isProviderConfigured(provider)
        let validationState = getValidationState(for: provider)
        
        // If we have a key but no validation state, assume it needs validation
        let finalState: ValidationState = hasKey && validationState == .notValidated ? .notValidated : validationState
        
        return (hasKey: hasKey, validationState: finalState)
    }
    
    // MARK: - Private Methods
    
    private func initializeValidationStates() {
        for provider in LLMProvider.allCases {
            validationStates[provider] = .notValidated
        }
    }
    
    private func refreshValidationStates() {
        for provider in LLMProvider.allCases {
            let hasKey = isProviderConfigured(provider)
            if !hasKey {
                validationStates[provider] = .notValidated
            }
            // Keep existing validation states for providers that still have keys
        }
    }
    
    private func performValidation(key: String, provider: LLMProvider) async -> ValidationResult {
        PotterLogger.shared.info("api_key", "🔍 Validating API key for \(provider.displayName)")
        
        // Create appropriate LLM client for validation
        let client: LLMClient
        switch provider {
        case .openAI:
            client = OpenAIClient(apiKey: key)
        case .anthropic:
            client = AnthropicClient(apiKey: key)
        case .google:
            client = GoogleClient(apiKey: key)
        }
        
        do {
            // Perform a simple validation request
            let testPrompt = "Hello"
            let testMessage = "Say 'API key is valid' if you can read this."
            
            // Use the first available model for the provider
            let model = provider.models.first?.id ?? ""
            _ = try await client.processText(testPrompt, prompt: testMessage, model: model)
            
            PotterLogger.shared.info("api_key", "✅ API key validation successful for \(provider.displayName)")
            return .success
            
        } catch {
            PotterLogger.shared.warning("api_key", "❌ API key validation failed for \(provider.displayName): \(error)")
            
            if let potterError = error as? PotterError {
                switch potterError {
                case .network(.unauthorized):
                    return .failure(.invalidKey("Invalid API key"))
                case .network(.rateLimited):
                    return .failure(.rateLimited)
                case .network(.serverError(let statusCode, let message)):
                    return .failure(.serverError(statusCode, message ?? "Unknown server error"))
                default:
                    return .failure(.networkError(error))
                }
            }
            
            return .failure(.networkError(error))
        }
    }
    
    // MARK: - Testing Support
    #if DEBUG
    /// For testing only - directly set validation state
    func setValidationStateForTesting(_ state: ValidationState, for provider: LLMProvider) {
        validationStates[provider] = state
    }
    #endif
}

// MARK: - Supporting Types

/// Validation result for API key operations
enum ValidationResult {
    case success
    case failure(APIKeyValidationError)
    
    var isSuccess: Bool {
        if case .success = self {
            return true
        }
        return false
    }
    
    var timestamp: Date {
        return Date()
    }
}

/// Specific validation errors
enum APIKeyValidationError: Error, LocalizedError {
    case invalidKey(String)
    case networkError(Error)
    case rateLimited
    case serverError(Int, String)
    case storageError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidKey(let message):
            return message
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .rateLimited:
            return "Rate limited. Please try again later."
        case .serverError(let code, let message):
            return "Server error (\(code)): \(message)"
        case .storageError(let error):
            return "Storage error: \(error.localizedDescription)"
        }
    }
}

/// Service-level errors
enum APIKeyServiceError: Error, LocalizedError {
    case storageError(Error)
    case migrationError(Error)
    case validationError(APIKeyValidationError)
    
    var errorDescription: String? {
        switch self {
        case .storageError(let error):
            return "Storage error: \(error.localizedDescription)"
        case .migrationError(let error):
            return "Migration error: \(error.localizedDescription)"
        case .validationError(let error):
            return error.localizedDescription
        }
    }
}

/// Validation state for UI binding
enum ValidationState: Equatable {
    case notValidated
    case validating
    case valid
    case invalid(String)
    
    var isValid: Bool {
        if case .valid = self {
            return true
        }
        return false
    }
    
    var isValidating: Bool {
        if case .validating = self {
            return true
        }
        return false
    }
    
    var errorMessage: String? {
        if case .invalid(let message) = self {
            return message
        }
        return nil
    }
    
    static func from(_ result: ValidationResult) -> ValidationState {
        switch result {
        case .success:
            return .valid
        case .failure(let error):
            return .invalid(error.localizedDescription)
        }
    }
}
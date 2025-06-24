import Foundation
import SwiftUI

// MARK: - LLM Manager
@MainActor
class LLMManager: ObservableObject {
    @Published var selectedProvider: LLMProvider = .openAI
    @Published var selectedModel: LLMModel?
    @Published var apiKeys: [LLMProvider: String] = [:]
    @Published var validationStates: [LLMProvider: ValidationState] = [:]
    @Published var isValidating = false
    
    private var clients: [LLMProvider: LLMClient] = [:]
    
    enum ValidationState {
        case none
        case validating
        case valid
        case invalid(String)
        
        var isValid: Bool {
            if case .valid = self { return true }
            return false
        }
        
        var errorMessage: String? {
            if case .invalid(let message) = self { return message }
            return nil
        }
    }
    
    init() {
        // Initialize validation states
        for provider in LLMProvider.allCases {
            validationStates[provider] = ValidationState.none
        }
        
        // Load saved settings
        loadSettings()
        
        // Set default model for selected provider
        selectedModel = selectedProvider.models.first
    }
    
    // MARK: - Settings Management
    func loadSettings() {
        // Load selected provider
        if let providerString = UserDefaults.standard.string(forKey: "llm_provider"),
           let provider = LLMProvider(rawValue: providerString) {
            selectedProvider = provider
        }
        
        // Don't preload all API keys during startup to avoid keychain prompts
        // Keys will be loaded on-demand when providers are selected
        
        // Load selected model
        if let modelId = UserDefaults.standard.string(forKey: "selected_model") {
            selectedModel = selectedProvider.models.first { $0.id == modelId }
        }
        
        // Always ensure a model is selected for the current provider
        if selectedModel == nil || selectedModel?.provider != selectedProvider {
            selectedModel = selectedProvider.models.first
        }
    }
    
    func saveSettings() {
        UserDefaults.standard.set(selectedProvider.rawValue, forKey: "llm_provider")
        
        // API keys are now managed by StorageAdapter
        // Individual saves happen through setAPIKey method
        
        if let selectedModel = selectedModel {
            UserDefaults.standard.set(selectedModel.id, forKey: "selected_model")
        }
    }
    
    // MARK: - Provider Management
    func selectProvider(_ provider: LLMProvider) {
        selectedProvider = provider
        selectedModel = provider.models.first
        saveSettings()
        
        PotterLogger.shared.info("llm_manager", "🔄 Switched to \(provider.displayName) provider")
    }
    
    func selectModel(_ model: LLMModel) {
        selectedModel = model
        saveSettings()
        
        PotterLogger.shared.info("llm_manager", "🎯 Selected model: \(model.name)")
    }
    
    // MARK: - API Key Management
    func setAPIKey(_ apiKey: String, for provider: LLMProvider) {
        let maskedKey = apiKey.isEmpty ? "empty" : String(apiKey.prefix(12)) + "..." + String(apiKey.suffix(8))
        PotterLogger.shared.info("llm_manager", "🔧 Setting API key for \(provider.displayName): \(maskedKey) (length: \(apiKey.count))")
        
        // Only log full key for shorter keys to avoid performance issues in tests
        if apiKey.count < 1000 {
            PotterLogger.shared.info("llm_manager", "🔍 FULL KEY BEING SET: \(apiKey)")
        }
        
        // Store in memory
        apiKeys[provider] = apiKey
        
        // Save to persistent storage
        if !apiKey.isEmpty {
            let result = StorageAdapter.shared.saveAPIKey(apiKey, for: provider)
            switch result {
            case .success:
                PotterLogger.shared.info("llm_manager", "✅ API key saved to storage")
                break
            case .failure(let error):
                PotterLogger.shared.error("llm_manager", "❌ Failed to save API key: \(error.localizedDescription)")
            }
        }
        
        // Note: Don't reset validation state here - let validation functions manage that
    }
    
    func getAPIKey(for provider: LLMProvider) -> String {
        PotterLogger.shared.info("llm_manager", "🔍 Getting API key for \(provider.displayName)")
        
        // First check memory cache
        if let cachedKey = apiKeys[provider] {
            let maskedKey = String(cachedKey.prefix(12)) + "..." + String(cachedKey.suffix(8))
            PotterLogger.shared.info("llm_manager", "✅ Found cached API key: \(maskedKey) (length: \(cachedKey.count))")
            
            // Only log full key for shorter keys to avoid performance issues in tests
            if cachedKey.count < 1000 {
                PotterLogger.shared.info("llm_manager", "🔍 FULL CACHED KEY: \(cachedKey)")
            }
            return cachedKey
        }
        
        // Load from storage if not in memory
        PotterLogger.shared.info("llm_manager", "💾 Loading API key from storage for \(provider.displayName)")
        let loadResult = StorageAdapter.shared.loadAPIKey(for: provider)
        switch loadResult {
        case .success(let storedKey):
            let maskedKey = String(storedKey.prefix(12)) + "..." + String(storedKey.suffix(8))
            PotterLogger.shared.info("llm_manager", "✅ Loaded API key from storage: \(maskedKey) (length: \(storedKey.count))")
            
            // Only log full key for shorter keys to avoid performance issues in tests
            if storedKey.count < 1000 {
                PotterLogger.shared.info("llm_manager", "🔍 FULL STORED KEY: \(storedKey)")
            }
            apiKeys[provider] = storedKey
            return storedKey
        case .failure:
            PotterLogger.shared.warning("llm_manager", "❌ Failed to load API key from storage for \(provider.displayName)")
            break
        }
        
        return ""
    }
    
    // MARK: - API Key Validation
    func validateAndSaveAPIKey(_ apiKey: String, for provider: LLMProvider) async {
        guard !apiKey.isEmpty else {
            validationStates[provider] = .invalid("API key cannot be empty")
            return
        }
        
        validationStates[provider] = .validating
        isValidating = true
        
        let maskedKey = String(apiKey.prefix(12)) + "..." + String(apiKey.suffix(8))
        PotterLogger.shared.info("llm_manager", "🔑 Validating \(provider.displayName) API key: \(maskedKey) (length: \(apiKey.count))")
        
        // Only log full key for shorter keys to avoid performance issues in tests
        if apiKey.count < 1000 {
            PotterLogger.shared.info("llm_manager", "🔍 FULL API KEY FOR VALIDATION: \(apiKey)")
        }
        
        do {
            let client = createClient(for: provider, apiKey: apiKey)
            _ = try await client.validateAPIKey(apiKey)
            
            // If we get here, validation succeeded
            PotterLogger.shared.info("llm_manager", "✅ \(provider.displayName) API key validated successfully")
            
            // Save the key using the simple setter
            setAPIKey(apiKey, for: provider)
            
            // Update validation state AFTER saving to avoid conflicts
            validationStates[provider] = .valid
            clients[provider] = client
            
            // Save other settings (provider, model selection)
            saveSettings()
        } catch {
            let errorMessage = error.localizedDescription
            validationStates[provider] = .invalid(errorMessage)
            PotterLogger.shared.error("llm_manager", "❌ \(provider.displayName) API key validation error: \(errorMessage)")
        }
        
        isValidating = false
    }
    
    private func createClient(for provider: LLMProvider, apiKey: String) -> LLMClient {
        switch provider {
        case .openAI:
            return OpenAIClient(apiKey: apiKey)
        case .anthropic:
            return AnthropicClient(apiKey: apiKey)
        case .google:
            return GoogleClient(apiKey: apiKey)
        }
    }
    
    // MARK: - Text Processing
    func processText(_ text: String, prompt: String) async throws -> String {
        guard let model = selectedModel else {
            throw PotterError.configuration(.missingConfiguration(key: "selected model"))
        }
        
        // Get API key from storage (will load into memory cache if needed)
        let apiKey = getAPIKey(for: selectedProvider)
        guard !apiKey.isEmpty else {
            throw PotterError.configuration(.missingAPIKey(provider: selectedProvider.displayName))
        }
        
        // Get or create client
        let client: LLMClient
        if let existingClient = clients[selectedProvider] {
            client = existingClient
        } else {
            client = createClient(for: selectedProvider, apiKey: apiKey)
            clients[selectedProvider] = client
        }
        
        PotterLogger.shared.info("llm_manager", "🤖 Processing text with \(selectedProvider.displayName) \(model.name)")
        
        let result = try await client.processText(text, prompt: prompt, model: model.id)
        
        PotterLogger.shared.info("llm_manager", "✅ Text processing completed successfully")
        
        return result
    }
    
    // MARK: - Validation Helpers
    func isProviderConfigured(_ provider: LLMProvider) -> Bool {
        let validationState = validationStates[provider] ?? .none
        
        // If explicitly valid, return true
        if validationState.isValid {
            return true
        }
        
        // If explicitly invalid, return false regardless of stored keys
        if case .invalid(_) = validationState {
            return false
        }
        
        // For .none or .validating states, check if we have a stored key
        // This makes the system robust across app restarts
        let apiKey = getAPIKey(for: provider)
        return !apiKey.isEmpty
    }
    
    func getCurrentValidationState() -> ValidationState {
        return validationStates[selectedProvider] ?? .none
    }
    
    func hasValidProvider() -> Bool {
        // Check if the currently selected provider is configured
        return isProviderConfigured(selectedProvider)
    }
}
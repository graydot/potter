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
        apiKeys[provider] = apiKey
        // Reset validation state when key changes
        validationStates[provider] = ValidationState.none
        
        // Save to storage using StorageAdapter
        if !apiKey.isEmpty {
            let result = StorageAdapter.shared.saveAPIKey(apiKey, for: provider)
            switch result {
            case .success:
                break
            case .failure(let error):
                PotterLogger.shared.error("llm_manager", "Failed to save API key for \(provider.displayName): \(error.localizedDescription)")
            }
        }
        
        saveSettings()
    }
    
    func getAPIKey(for provider: LLMProvider) -> String {
        // First check memory cache
        if let cachedKey = apiKeys[provider] {
            return cachedKey
        }
        
        // Load from storage if not in memory
        let loadResult = StorageAdapter.shared.loadAPIKey(for: provider)
        switch loadResult {
        case .success(let storedKey):
            apiKeys[provider] = storedKey
            return storedKey
        case .failure:
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
        
        PotterLogger.shared.info("llm_manager", "🔑 Validating \(provider.displayName) API key...")
        
        do {
            let client = createClient(for: provider, apiKey: apiKey)
            _ = try await client.validateAPIKey(apiKey)
            
            // If we get here, validation succeeded
            validationStates[provider] = .valid
            apiKeys[provider] = apiKey
            clients[provider] = client
            saveSettings()
            
            PotterLogger.shared.info("llm_manager", "✅ \(provider.displayName) API key validated successfully")
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
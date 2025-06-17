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
        
        // Load API keys
        for provider in LLMProvider.allCases {
            let key = "api_key_\(provider.rawValue)"
            if let apiKey = UserDefaults.standard.string(forKey: key), !apiKey.isEmpty {
                apiKeys[provider] = apiKey
                // Mark as valid if previously saved (will be re-validated on first use)
                validationStates[provider] = .valid
            }
        }
        
        // Load selected model
        if let modelId = UserDefaults.standard.string(forKey: "selected_model") {
            selectedModel = selectedProvider.models.first { $0.id == modelId }
        }
        
        selectedModel = selectedModel ?? selectedProvider.models.first
    }
    
    func saveSettings() {
        UserDefaults.standard.set(selectedProvider.rawValue, forKey: "llm_provider")
        
        for (provider, apiKey) in apiKeys {
            let key = "api_key_\(provider.rawValue)"
            UserDefaults.standard.set(apiKey, forKey: key)
        }
        
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
        saveSettings()
    }
    
    func getAPIKey(for provider: LLMProvider) -> String {
        return apiKeys[provider] ?? ""
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
            let isValid = try await client.validateAPIKey(apiKey)
            
            if isValid {
                // Validation successful
                validationStates[provider] = .valid
                apiKeys[provider] = apiKey
                clients[provider] = client
                saveSettings()
                
                PotterLogger.shared.info("llm_manager", "✅ \(provider.displayName) API key validated successfully")
                
                // Show success feedback briefly
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    // Keep the valid state but don't show temporary success message
                }
            } else {
                validationStates[provider] = .invalid("Invalid API key")
                PotterLogger.shared.warning("llm_manager", "❌ \(provider.displayName) API key validation failed")
            }
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
            throw LLMError.noResponse
        }
        
        guard let apiKey = apiKeys[selectedProvider], !apiKey.isEmpty else {
            throw LLMError.invalidAPIKey
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
        return validationStates[provider]?.isValid == true
    }
    
    func getCurrentValidationState() -> ValidationState {
        return validationStates[selectedProvider] ?? .none
    }
    
    func hasValidProvider() -> Bool {
        return validationStates.values.contains { $0.isValid }
    }
}
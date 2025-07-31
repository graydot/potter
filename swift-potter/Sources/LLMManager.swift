import Foundation
import SwiftUI

// MARK: - LLM Manager
@MainActor
class LLMManager: ObservableObject {
    @Published var selectedProvider: LLMProvider = .openAI
    @Published var selectedModel: LLMModel?
    
    private var clients: [LLMProvider: LLMClient] = [:]
    private let apiKeyService = APIKeyService.shared
    
    @Published var isValidatingLocal: Bool = false
    
    // MARK: - API Key Service Delegation
    
    /// Delegate to APIKeyService for validation states
    var validationStates: [LLMProvider: ValidationState] {
        return apiKeyService.validationStates
    }
    
    /// Delegate to APIKeyService for validation status
    var isValidating: Bool {
        return isValidatingLocal || apiKeyService.isValidating
    }
    
    init() {
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
    
    // MARK: - API Key Management (Delegated to APIKeyService)
    func setAPIKey(_ apiKey: String, for provider: LLMProvider) {
        let result = apiKeyService.saveAPIKey(apiKey, for: provider)
        switch result {
        case .success:
            PotterLogger.shared.info("llm_manager", "✅ API key saved via service")
        case .failure(let error):
            PotterLogger.shared.error("llm_manager", "❌ Failed to save API key via service: \(error)")
        }
    }
    
    func getAPIKey(for provider: LLMProvider) -> String {
        return apiKeyService.getAPIKey(for: provider) ?? ""
    }
    
    // MARK: - API Key Validation (Delegated to APIKeyService)
    func validateAndSaveAPIKey(_ apiKey: String, for provider: LLMProvider) async {
        isValidatingLocal = true
        
        // Only pass the selected model if it belongs to the provider being validated
        let modelToUse = selectedModel?.provider == provider ? selectedModel : nil
        let result = await apiKeyService.validateAndSaveAPIKey(apiKey, for: provider, using: modelToUse)
        
        isValidatingLocal = false
        
        if case .success = result {
            // Update client cache if validation successful
            let client = createClient(for: provider, apiKey: apiKey)
            clients[provider] = client
            
            // Save other settings (provider, model selection)
            saveSettings()
        }
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
    
    // MARK: - Validation Helpers (Delegated to APIKeyService)
    func isProviderConfigured(_ provider: LLMProvider) -> Bool {
        return apiKeyService.isProviderConfigured(provider)
    }
    
    func getCurrentValidationState() -> ValidationState {
        return apiKeyService.getValidationState(for: selectedProvider)
    }
    
    func hasValidProvider() -> Bool {
        return isProviderConfigured(selectedProvider)
    }
}
import Foundation
import SwiftUI

// MARK: - LLM Manager
@MainActor
class LLMManager: ObservableObject, LLMProcessing {
    static let shared = LLMManager()

    @Published var selectedProvider: LLMProvider = .anthropic
    @Published var selectedModel: LLMModel?

    private var clients: [LLMProvider: LLMClient] = [:]
    private var keyValidationService: (any KeyValidationService)?
    private var apiKeyService: any KeyValidationService { keyValidationService ?? APIKeyService.shared }
    
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
    
    private let modelRegistry: ModelRegistry

    init(modelRegistry: ModelRegistry? = nil, keyValidationService: (any KeyValidationService)? = nil) {
        self.modelRegistry = modelRegistry ?? ModelRegistry.shared
        self.keyValidationService = keyValidationService

        // Load saved settings
        loadSettings()

        // Set default model for selected provider
        if selectedModel == nil {
            selectedModel = modelsForCurrentProvider().first
        }

        // Trigger background model refresh if stale
        refreshModelsIfStale(for: selectedProvider)
    }

    /// Models for the current provider, using the registry (dynamic) with static fallback.
    func modelsForCurrentProvider() -> [LLMModel] {
        return modelRegistry.getModels(for: selectedProvider)
    }

    /// Models for a specific provider, using the registry.
    func modelsForProvider(_ provider: LLMProvider) -> [LLMModel] {
        return modelRegistry.getModels(for: provider)
    }
    
    // MARK: - Settings Management
    func loadSettings() {
        // Load selected provider
        if let providerString = UserDefaults.standard.string(forKey: UserDefaultsKeys.llmProvider),
           let provider = LLMProvider(rawValue: providerString) {
            selectedProvider = provider
        }
        
        // Don't preload all API keys during startup to avoid keychain prompts
        // Keys will be loaded on-demand when providers are selected
        
        // Load selected model from registry (dynamic) or static fallback
        let providerModels = modelRegistry.getModels(for: selectedProvider)
        if let modelId = UserDefaults.standard.string(forKey: UserDefaultsKeys.selectedModel) {
            selectedModel = providerModels.first { $0.id == modelId }
        }

        // Always ensure a model is selected for the current provider
        if selectedModel == nil || selectedModel?.provider != selectedProvider {
            selectedModel = providerModels.first
        }
    }
    
    func saveSettings() {
        UserDefaults.standard.set(selectedProvider.rawValue, forKey: UserDefaultsKeys.llmProvider)
        
        // API keys are now managed by StorageAdapter
        // Individual saves happen through setAPIKey method
        
        if let selectedModel = selectedModel {
            UserDefaults.standard.set(selectedModel.id, forKey: UserDefaultsKeys.selectedModel)
        }
    }
    
    // MARK: - Provider Management
    func selectProvider(_ provider: LLMProvider) {
        selectedProvider = provider
        selectedModel = modelRegistry.getModels(for: provider).first
        // Invalidate cached client — key may have changed since last cached
        clients.removeValue(forKey: provider)
        saveSettings()

        // Refresh models for the new provider if stale
        refreshModelsIfStale(for: provider)

        PotterLogger.shared.info("llm_manager", "🔄 Switched to \(provider.displayName) provider")
    }

    /// Trigger a background model refresh if the cache is stale.
    private func refreshModelsIfStale(for provider: LLMProvider) {
        guard modelRegistry.isStale(for: provider) else { return }
        let apiKey = getAPIKey(for: provider)
        guard !apiKey.isEmpty else { return }
        Task {
            do {
                try await modelRegistry.refreshModels(for: provider, apiKey: apiKey)
            } catch {
                PotterLogger.shared.error("llm_manager", "Model refresh failed for \(provider.displayName): \(error.localizedDescription)")
            }
        }
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
            // Invalidate cached client so next processText creates one with the new key
            clients.removeValue(forKey: provider)
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
        case .anthropic:
            return AnthropicClient(apiKey: apiKey)
        case .google:
            return GoogleClient(apiKey: apiKey)
        }
    }
    
    // MARK: - Text Processing

    /// Wraps the user's prompt with a system instruction to return only processed text.
    private func buildSystemPrompt(_ prompt: String) -> String {
        return "\(prompt)\n\nOutput only your rewritten version of the text. No preamble, no explanations, no bullet points, no labels like \"Here's the polished version\" — just the transformed text itself."
    }

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

        let systemPrompt = buildSystemPrompt(prompt)
        let result = try await client.processText(text, prompt: systemPrompt, model: model.id)

        PotterLogger.shared.info("llm_manager", "✅ Text processing completed successfully")

        return result
    }
    
    /// Stream text processing — calls `onToken` for each chunk, returns full assembled text.
    func streamText(_ text: String, prompt: String,
                    onToken: @Sendable @escaping (String) -> Void) async throws -> String {
        guard let model = selectedModel else {
            throw PotterError.configuration(.missingConfiguration(key: "selected model"))
        }

        let apiKey = getAPIKey(for: selectedProvider)
        guard !apiKey.isEmpty else {
            throw PotterError.configuration(.missingAPIKey(provider: selectedProvider.displayName))
        }

        let client: LLMClient
        if let existingClient = clients[selectedProvider] {
            client = existingClient
        } else {
            client = createClient(for: selectedProvider, apiKey: apiKey)
            clients[selectedProvider] = client
        }

        PotterLogger.shared.info("llm_manager", "🌊 Streaming text with \(selectedProvider.displayName) \(model.name)")
        let systemPrompt = buildSystemPrompt(prompt)
        let result = try await client.streamText(text, prompt: systemPrompt, model: model.id, onToken: onToken)
        PotterLogger.shared.info("llm_manager", "✅ Streaming completed (\(result.count) chars)")
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
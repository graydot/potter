import SwiftUI
import Foundation


// MARK: - LLM Provider View Model
@MainActor
class LLMProviderViewModel: ObservableObject {
    
    // MARK: - Published Properties
    @Published var apiKeyText: String = ""
    @Published var showAPIKey: Bool = false
    // Storage is now always UserDefaults
    @Published var showStorageError: Bool = false
    @Published var storageErrorMessage: String = ""
    @Published var showingSuccessCheckmark: Bool = false
    
    // MARK: - Dependencies
    private let llmManager: LLMManager
    private let apiKeyService: APIKeyService
    
    // MARK: - Computed Properties
    var selectedProvider: LLMProvider {
        get { llmManager.selectedProvider }
        set { 
            llmManager.selectedProvider = newValue
            loadProviderState(for: newValue)
        }
    }
    
    var selectedModel: LLMModel? {
        get { llmManager.selectedModel }
        set { llmManager.selectedModel = newValue }
    }
    
    var validationStates: [LLMProvider: ValidationState] {
        llmManager.validationStates
    }
    
    var isValidating: Bool {
        llmManager.isValidating
    }
    
    var currentValidationState: ValidationState? {
        validationStates[selectedProvider]
    }
    
    var textFieldBorderColor: Color {
        switch currentValidationState {
        case .some(.invalid):
            return .red.opacity(0.8)
        case .some(.valid):
            return .green.opacity(0.8)
        case .some(.validating):
            return .blue.opacity(0.6)
        case .some(.notValidated), .none:
            return apiKeyText.isEmpty ? .red.opacity(0.8) : .clear
        }
    }
    
    var isTestAndSaveButtonDisabled: Bool {
        apiKeyText.isEmpty || isValidating
    }
    
    // MARK: - Initialization
    init(llmManager: LLMManager? = nil, apiKeyService: APIKeyService = APIKeyService.shared) {
        self.llmManager = llmManager ?? LLMManager()
        self.apiKeyService = apiKeyService
        
        // Initialize state
        loadProviderState(for: self.llmManager.selectedProvider)
        // Storage is always UserDefaults now
    }
    
    // MARK: - Public Methods
    
    func onProviderChanged(to newProvider: LLMProvider) {
        loadProviderState(for: newProvider)
        // Storage is always UserDefaults now
        // Set default model for the new provider
        selectedModel = newProvider.models.first
    }
    
    func onAPIKeyTextChanged(_ newValue: String) {
        // Note: Validation state updates are handled during save/validation operations
        // This is just for UI responsiveness
    }
    
    func toggleAPIKeyVisibility() {
        showAPIKey.toggle()
    }
    
    func openAPIKeyURL() {
        if let url = URL(string: selectedProvider.apiKeyURL) {
            NSWorkspace.shared.open(url)
        }
    }
    
    func testAndSaveAPIKey() async {
        do {
            // Clear any previous errors
            showStorageError = false
            
            // Validate and save using current storage preference
            await llmManager.validateAndSaveAPIKey(apiKeyText, for: selectedProvider)
            
            let success = validationStates[selectedProvider]?.isValid == true
            
            if success {
                await showSuccessState()
            } else {
                let errorMessage = validationStates[selectedProvider]?.errorMessage ?? "Unknown validation error"
                await showErrorState("Failed to validate API key: \(errorMessage)")
            }
        }
    }
    
    // Storage method toggling removed - always UserDefaults now
    
    // MARK: - Private Methods
    
    private func loadProviderState(for provider: LLMProvider) {
        let storedKey = llmManager.getAPIKey(for: provider)
        apiKeyText = storedKey
        
        // Note: Validation states are now managed by APIKeyService
        // The loadProviderState method handles initial state loading
    }
    
    private func showSuccessState() async {
        withAnimation(.easeInOut(duration: 0.3)) {
            showingSuccessCheckmark = true
        }
        
        try? await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds
        
        withAnimation(.easeInOut(duration: 0.3)) {
            showingSuccessCheckmark = false
        }
    }
    
    private func showErrorState(_ message: String) async {
        showStorageError = true
        storageErrorMessage = message
        
        try? await Task.sleep(nanoseconds: 5_000_000_000) // 5 seconds
        
        showStorageError = false
    }
    
}
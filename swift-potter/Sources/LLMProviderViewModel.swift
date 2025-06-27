import SwiftUI
import Foundation


// MARK: - LLM Provider View Model
@MainActor
class LLMProviderViewModel: ObservableObject {
    
    // MARK: - Published Properties
    @Published var apiKeyText: String = ""
    @Published var showAPIKey: Bool = false
    @Published var storageMethod: APIKeyStorageMethod = .userDefaults
    @Published var showStorageError: Bool = false
    @Published var storageErrorMessage: String = ""
    @Published var isMigrating: Bool = false
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
        apiKeyText.isEmpty || isValidating || isMigrating
    }
    
    // MARK: - Initialization
    init(llmManager: LLMManager? = nil, apiKeyService: APIKeyService = APIKeyService.shared) {
        self.llmManager = llmManager ?? LLMManager()
        self.apiKeyService = apiKeyService
        
        // Initialize state
        loadProviderState(for: self.llmManager.selectedProvider)
        storageMethod = APIKeyStorageMethod(rawValue: StorageAdapter.shared.currentStorageMethod.rawValue) ?? .userDefaults
    }
    
    // MARK: - Public Methods
    
    func onProviderChanged(to newProvider: LLMProvider) {
        loadProviderState(for: newProvider)
        storageMethod = APIKeyStorageMethod(rawValue: StorageAdapter.shared.currentStorageMethod.rawValue) ?? .userDefaults
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
    
    func toggleStorageMethod() async {
        let newMethod: APIKeyStorageMethod = storageMethod == .keychain ? .userDefaults : .keychain
        
        // Disable UI during migration
        isMigrating = true
        showStorageError = false
        
        // Migrate all API keys to new storage method
        let newStorageMethod = StorageMethod(rawValue: newMethod.rawValue) ?? .userDefaults
        let result = StorageAdapter.shared.migrate(to: newStorageMethod)
        
        switch result {
        case .success:
            storageMethod = newMethod
            await showSuccessState()
            PotterLogger.shared.info("api_storage", "✅ Migrated all API keys to \(newMethod.rawValue)")
            
        case .failure(let error):
            await showErrorState("Failed to migrate to \(newMethod.displayName): \(error.localizedDescription)")
        }
        
        // Re-enable UI
        isMigrating = false
    }
    
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
    
    // MARK: - Storage Method Helpers
    
    var storageStatusText: String {
        switch storageMethod {
        case .keychain:
            return "Keys encrypted and saved"
        case .userDefaults:
            return "Keys saved without encryption"
        }
    }
    
    var storageStatusColor: Color {
        switch storageMethod {
        case .keychain:
            return .green
        case .userDefaults:
            return .orange
        }
    }
    
    var storageIcon: String {
        switch storageMethod {
        case .keychain:
            return "lock.fill"
        case .userDefaults:
            return "lock.open.fill"
        }
    }
    
    var storageToggleHelp: String {
        if isMigrating {
            return "Migrating API keys..."
        } else if storageMethod == .keychain {
            return "Selected mode: Keychain access. Click to change to insecure mode to avoid keychain password requests"
        } else {
            return "Selected mode: Insecure. Click to change to keychain access for encrypted storage"
        }
    }
}
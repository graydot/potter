import Foundation

class PotterSettings: ObservableObject {
    private let userDefaults: UserDefaults
    
    // Keys - Updated to match StorageAdapter format
    private enum Keys {
        static let openaiAPIKey = "api_key_openai"
        static let anthropicAPIKey = "api_key_anthropic"
        static let googleAPIKey = "api_key_google"
        static let currentProvider = "current_provider"
        static let currentPrompt = "current_prompt"
    }
    
    // Published properties for SwiftUI bindings
    @Published var openaiAPIKey: String? {
        didSet { 
            userDefaults.set(openaiAPIKey, forKey: Keys.openaiAPIKey)
            userDefaults.synchronize()
        }
    }
    
    @Published var anthropicAPIKey: String? {
        didSet { 
            userDefaults.set(anthropicAPIKey, forKey: Keys.anthropicAPIKey)
            userDefaults.synchronize()
        }
    }
    
    @Published var googleAPIKey: String? {
        didSet { 
            userDefaults.set(googleAPIKey, forKey: Keys.googleAPIKey)
            userDefaults.synchronize()
        }
    }
    
    @Published var currentProvider: String {
        didSet { 
            userDefaults.set(currentProvider, forKey: Keys.currentProvider)
            userDefaults.synchronize()
        }
    }
    
    @Published var currentPrompt: String {
        didSet { 
            userDefaults.set(currentPrompt, forKey: Keys.currentPrompt)
            userDefaults.synchronize()
        }
    }
    
    
    init(userDefaults: UserDefaults = .standard) {
        self.userDefaults = userDefaults
        
        // Load from UserDefaults
        self.openaiAPIKey = userDefaults.string(forKey: Keys.openaiAPIKey)
        self.anthropicAPIKey = userDefaults.string(forKey: Keys.anthropicAPIKey)
        self.googleAPIKey = userDefaults.string(forKey: Keys.googleAPIKey)
        self.currentProvider = userDefaults.string(forKey: Keys.currentProvider) ?? "openai"
        self.currentPrompt = userDefaults.string(forKey: Keys.currentPrompt) ?? "formal"
    }
    
    func save() {
        // UserDefaults automatically saves when properties are set
        userDefaults.synchronize()
    }
    
    func resetToDefaults() {
        // Reset all published properties to their default values
        self.openaiAPIKey = nil
        self.anthropicAPIKey = nil
        self.googleAPIKey = nil
        self.currentProvider = "openai"
        self.currentPrompt = "formal"
        
        // Force synchronization
        userDefaults.synchronize()
    }
}
import Foundation

class PotterSettings: ObservableObject {
    private let userDefaults: UserDefaults
    
    // Published properties for SwiftUI bindings
    @Published var openaiAPIKey: String? {
        didSet {
            userDefaults.set(openaiAPIKey, forKey: UserDefaultsKeys.apiKeyOpenAI)
            userDefaults.synchronize()
        }
    }

    @Published var anthropicAPIKey: String? {
        didSet {
            userDefaults.set(anthropicAPIKey, forKey: UserDefaultsKeys.apiKeyAnthropic)
            userDefaults.synchronize()
        }
    }

    @Published var googleAPIKey: String? {
        didSet {
            userDefaults.set(googleAPIKey, forKey: UserDefaultsKeys.apiKeyGoogle)
            userDefaults.synchronize()
        }
    }

    @Published var currentProvider: String {
        didSet {
            userDefaults.set(currentProvider, forKey: UserDefaultsKeys.llmProvider)
            userDefaults.synchronize()
        }
    }

    @Published var currentPrompt: String {
        didSet {
            userDefaults.set(currentPrompt, forKey: UserDefaultsKeys.currentPrompt)
            userDefaults.synchronize()
        }
    }
    
    
    init(userDefaults: UserDefaults = .standard) {
        self.userDefaults = userDefaults
        
        // Load from UserDefaults
        self.openaiAPIKey = userDefaults.string(forKey: UserDefaultsKeys.apiKeyOpenAI)
        self.anthropicAPIKey = userDefaults.string(forKey: UserDefaultsKeys.apiKeyAnthropic)
        self.googleAPIKey = userDefaults.string(forKey: UserDefaultsKeys.apiKeyGoogle)
        self.currentProvider = userDefaults.string(forKey: UserDefaultsKeys.llmProvider) ?? "anthropic"
        self.currentPrompt = userDefaults.string(forKey: UserDefaultsKeys.currentPrompt) ?? "formal"
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
        self.currentProvider = "anthropic"
        self.currentPrompt = "formal"
        
        // Force synchronization
        userDefaults.synchronize()
    }
}
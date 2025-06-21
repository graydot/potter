import Foundation

class PotterSettings: ObservableObject {
    private let userDefaults = UserDefaults.standard
    
    // Keys - Updated to match StorageAdapter format
    private enum Keys {
        static let openaiAPIKey = "api_key_openai"
        static let anthropicAPIKey = "api_key_anthropic"
        static let googleAPIKey = "api_key_google"
        static let currentProvider = "current_provider"
        static let currentPrompt = "current_prompt"
        static let notifications = "notifications_enabled"
    }
    
    // Published properties for SwiftUI bindings
    @Published var openaiAPIKey: String? {
        didSet { userDefaults.set(openaiAPIKey, forKey: Keys.openaiAPIKey) }
    }
    
    @Published var anthropicAPIKey: String? {
        didSet { userDefaults.set(anthropicAPIKey, forKey: Keys.anthropicAPIKey) }
    }
    
    @Published var googleAPIKey: String? {
        didSet { userDefaults.set(googleAPIKey, forKey: Keys.googleAPIKey) }
    }
    
    @Published var currentProvider: String {
        didSet { userDefaults.set(currentProvider, forKey: Keys.currentProvider) }
    }
    
    @Published var currentPrompt: String {
        didSet { userDefaults.set(currentPrompt, forKey: Keys.currentPrompt) }
    }
    
    @Published var notificationsEnabled: Bool {
        didSet { userDefaults.set(notificationsEnabled, forKey: Keys.notifications) }
    }
    
    init() {
        // Load from UserDefaults
        self.openaiAPIKey = userDefaults.string(forKey: Keys.openaiAPIKey)
        self.anthropicAPIKey = userDefaults.string(forKey: Keys.anthropicAPIKey)
        self.googleAPIKey = userDefaults.string(forKey: Keys.googleAPIKey)
        self.currentProvider = userDefaults.string(forKey: Keys.currentProvider) ?? "openai"
        self.currentPrompt = userDefaults.string(forKey: Keys.currentPrompt) ?? "formal"
        self.notificationsEnabled = userDefaults.object(forKey: Keys.notifications) as? Bool ?? true
    }
    
    func save() {
        // UserDefaults automatically saves when properties are set
        userDefaults.synchronize()
    }
}
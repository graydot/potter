import Foundation

enum APIKeyStorageMethod: String, CaseIterable {
    case keychain = "keychain"
    case userDefaults = "userdefaults"
    
    var displayName: String {
        switch self {
        case .keychain:
            return "Using Keychain (Encrypted)"
        case .userDefaults:
            return "Using UserDefaults (Plain Text)"
        }
    }
    
    var isSecure: Bool {
        return self == .keychain
    }
}

/// Simplified storage manager that delegates keychain operations to KeychainManager
class SecureAPIKeyStorage {
    static let shared = SecureAPIKeyStorage()
    
    private let storageMethodKey = "api_key_storage_method"
    
    /// When true, forces UserDefaults storage for all operations (used in testing)
    public var forceUserDefaultsForTesting = false
    
    private init() {}
    
    // MARK: - Storage Method Management
    
    func getStorageMethod(for provider: LLMProvider) -> APIKeyStorageMethod {
        // Force UserDefaults during testing to avoid keychain prompts
        if forceUserDefaultsForTesting {
            return .userDefaults
        }
        
        let key = "\(storageMethodKey)_\(provider.rawValue)"
        let methodString = UserDefaults.standard.string(forKey: key) ?? APIKeyStorageMethod.userDefaults.rawValue
        return APIKeyStorageMethod(rawValue: methodString) ?? .userDefaults
    }
    
    func setStorageMethod(_ method: APIKeyStorageMethod, for provider: LLMProvider) {
        let key = "\(storageMethodKey)_\(provider.rawValue)"
        UserDefaults.standard.set(method.rawValue, forKey: key)
    }
    
    // MARK: - API Key Storage (Single Access Point)
    
    func saveAPIKey(_ apiKey: String, for provider: LLMProvider, using method: APIKeyStorageMethod) -> Bool {
        // Remove from both locations first to avoid duplicates
        _ = removeAPIKey(for: provider)
        
        let success: Bool
        switch method {
        case .keychain:
            success = KeychainManager.shared.saveAPIKey(apiKey, for: provider)
        case .userDefaults:
            success = saveToUserDefaults(apiKey, for: provider)
        }
        
        if success {
            setStorageMethod(method, for: provider)
        }
        
        return success
    }
    
    func loadAPIKey(for provider: LLMProvider) -> String? {
        let preferredMethod = getStorageMethod(for: provider)
        
        switch preferredMethod {
        case .keychain:
            return KeychainManager.shared.loadAPIKey(for: provider)
        case .userDefaults:
            return loadFromUserDefaults(for: provider)
        }
    }
    
    func removeAPIKey(for provider: LLMProvider) -> Bool {
        var keychainSuccess = true
        var userDefaultsSuccess = true
        
        // Only access keychain if not in testing mode
        if !forceUserDefaultsForTesting {
            keychainSuccess = KeychainManager.shared.removeAPIKey(for: provider)
        }
        userDefaultsSuccess = removeFromUserDefaults(for: provider)
        
        // Remove storage method preference
        let key = "\(storageMethodKey)_\(provider.rawValue)"
        UserDefaults.standard.removeObject(forKey: key)
        
        return keychainSuccess && userDefaultsSuccess
    }
    
    // MARK: - Migration (Single Access Point)
    
    /// Migrate all API keys to keychain storage
    func migrateAllToKeychain() -> [LLMProvider: Bool] {
        PotterLogger.shared.info("api_storage", "🔄 Starting migration to keychain for all providers")
        
        let results = KeychainManager.shared.migrateFromUserDefaults()
        
        // Update storage method preferences for successful migrations
        for (provider, success) in results {
            if success {
                setStorageMethod(.keychain, for: provider)
            }
        }
        
        let successCount = results.values.filter { $0 }.count
        PotterLogger.shared.info("api_storage", "✅ Migration completed: \(successCount)/\(results.count) providers migrated to keychain")
        
        return results
    }
    
    /// Migrate all API keys to UserDefaults storage
    func migrateAllToUserDefaults() -> [LLMProvider: Bool] {
        PotterLogger.shared.info("api_storage", "🔄 Starting migration to UserDefaults for all providers")
        
        let results = KeychainManager.shared.exportToUserDefaults()
        
        // Update storage method preferences for successful migrations
        for (provider, success) in results {
            if success {
                setStorageMethod(.userDefaults, for: provider)
            }
        }
        
        let successCount = results.values.filter { $0 }.count
        PotterLogger.shared.info("api_storage", "✅ Migration completed: \(successCount)/\(results.count) providers migrated to UserDefaults")
        
        return results
    }
    
    // MARK: - UserDefaults Operations
    
    private func saveToUserDefaults(_ apiKey: String, for provider: LLMProvider) -> Bool {
        let key = "api_key_\(provider.rawValue)"
        UserDefaults.standard.set(apiKey, forKey: key)
        return true
    }
    
    private func loadFromUserDefaults(for provider: LLMProvider) -> String? {
        let key = "api_key_\(provider.rawValue)"
        return UserDefaults.standard.string(forKey: key)
    }
    
    private func removeFromUserDefaults(for provider: LLMProvider) -> Bool {
        let key = "api_key_\(provider.rawValue)"
        UserDefaults.standard.removeObject(forKey: key)
        return true
    }
    
    // MARK: - Status and Checks
    
    func getStorageStatus(for provider: LLMProvider) -> (hasKey: Bool, method: APIKeyStorageMethod) {
        let currentMethod = getStorageMethod(for: provider)
        let hasKey = loadAPIKey(for: provider) != nil
        return (hasKey, currentMethod)
    }
    
    func isKeychainAccessible() -> Bool {
        return KeychainManager.shared.isKeychainAccessible()
    }
    
    func getCacheInfo() -> (loaded: Bool, count: Int) {
        return KeychainManager.shared.getCacheInfo()
    }
}
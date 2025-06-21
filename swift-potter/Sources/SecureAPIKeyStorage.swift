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
    
    // MARK: - Atomic Operations (Race-Condition Safe)
    
    /// Atomically save API key with race condition protection
    func atomicSaveAPIKey(_ apiKey: String, for provider: LLMProvider, using method: APIKeyStorageMethod) async -> Bool {
        let currentMethod = getStorageMethod(for: provider)
        let previousMethod = currentMethod != method ? currentMethod : nil
        
        let result = await AtomicStorageManager.shared.atomicSave(
            apiKey: apiKey,
            for: provider,
            using: method,
            previousMethod: previousMethod
        )
        
        switch result {
        case .success:
            PotterLogger.shared.info("api_storage", "✅ Atomic save successful: \(provider.rawValue)")
            return true
        case .failure(let error):
            PotterLogger.shared.error("api_storage", "❌ Atomic save failed: \(error.localizedDescription)")
            return false
        }
    }
    
    /// Atomically migrate API key between storage methods
    func atomicMigrateAPIKey(for provider: LLMProvider, to targetMethod: APIKeyStorageMethod) async -> Bool {
        let currentMethod = getStorageMethod(for: provider)
        
        guard currentMethod != targetMethod else {
            PotterLogger.shared.info("api_storage", "ℹ️ Already using target storage method: \(targetMethod.rawValue)")
            return true
        }
        
        let result = await AtomicStorageManager.shared.atomicMigration(
            for: provider,
            from: currentMethod,
            to: targetMethod
        )
        
        switch result {
        case .success:
            // Update our preference to match the atomic manager
            setStorageMethod(targetMethod, for: provider)
            PotterLogger.shared.info("api_storage", "✅ Atomic migration successful: \(provider.rawValue) -> \(targetMethod.rawValue)")
            return true
        case .failure(let error):
            PotterLogger.shared.error("api_storage", "❌ Atomic migration failed: \(error.localizedDescription)")
            return false
        }
    }
    
    /// Atomically remove API key with confirmation
    func atomicRemoveAPIKey(for provider: LLMProvider) async -> Bool {
        let currentMethod = getStorageMethod(for: provider)
        
        let result = await AtomicStorageManager.shared.atomicRemove(
            for: provider,
            from: currentMethod
        )
        
        switch result {
        case .success:
            // Clear storage method preference
            let key = "\(storageMethodKey)_\(provider.rawValue)"
            UserDefaults.standard.removeObject(forKey: key)
            PotterLogger.shared.info("api_storage", "✅ Atomic removal successful: \(provider.rawValue)")
            return true
        case .failure(let error):
            PotterLogger.shared.error("api_storage", "❌ Atomic removal failed: \(error.localizedDescription)")
            return false
        }
    }
    
    /// Check storage consistency and fix any issues
    func validateAndFixStorage(for provider: LLMProvider) async -> StorageValidationResult {
        let status = AtomicStorageManager.shared.getStorageStatus(for: provider)
        
        switch status {
        case .noStorage:
            return .noIssues("No API key stored")
            
        case .keychainOnly(_), .userDefaultsOnly(_):
            return .noIssues("Single storage location, consistent")
            
        case .duplicateStorage(let keychainKey, let userDefaultsKey):
            if keychainKey == userDefaultsKey {
                // Same key in both places - prefer keychain and clean up UserDefaults
                PotterLogger.shared.warning("api_storage", "🔧 Found duplicate keys, cleaning up...")
                
                let removeResult = await AtomicStorageManager.shared.atomicRemove(
                    for: provider,
                    from: .userDefaults
                )
                
                if case .success = removeResult {
                    setStorageMethod(.keychain, for: provider)
                    return .fixedDuplicates("Removed duplicate from UserDefaults, kept keychain version")
                } else {
                    return .cannotFix("Failed to remove duplicate from UserDefaults")
                }
            } else {
                // Different keys - this requires user intervention
                return .needsUserChoice("Different API keys found in keychain and UserDefaults")
            }
        }
    }
    
    /// Check if atomic operations are safe to perform
    func isAtomicOperationSafe(for provider: LLMProvider) -> Bool {
        return !AtomicStorageManager.shared.isOperationInProgress(for: provider)
    }
    
    enum StorageValidationResult {
        case noIssues(String)
        case fixedDuplicates(String)
        case needsUserChoice(String)
        case cannotFix(String)
        
        var message: String {
            switch self {
            case .noIssues(let msg), .fixedDuplicates(let msg), .needsUserChoice(let msg), .cannotFix(let msg):
                return msg
            }
        }
        
        var requiresUserAction: Bool {
            if case .needsUserChoice = self {
                return true
            }
            return false
        }
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
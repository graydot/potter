import Foundation
import Security

// MARK: - Storage Method

enum StorageMethod: String, CaseIterable {
    case keychain = "keychain"
    case userDefaults = "userdefaults"
    
    var displayName: String {
        switch self {
        case .keychain:
            return "Keychain (Encrypted)"
        case .userDefaults:
            return "UserDefaults (Plain Text)"
        }
    }
    
    var isSecure: Bool {
        return self == .keychain
    }
}

// MARK: - Storage Backend Protocol

protocol StorageBackend {
    func get(key: String) -> Result<String, PotterError>
    func put(key: String, value: String) -> Result<Void, PotterError>
    func remove(key: String) -> Result<Void, PotterError>
    func clear() -> Result<Void, PotterError>
}

// MARK: - Keychain Storage Implementation

class KeychainStorage: StorageBackend {
    private let serviceName: String
    private let accountName = "potter-all-keys"
    
    init() {
        // Use bundle identifier to ensure consistency between dev and production
        if let bundleId = Bundle.main.bundleIdentifier {
            serviceName = "\(bundleId).api-keys"
            PotterLogger.shared.debug("keychain", "🔑 Using keychain service: \(serviceName) (from bundle ID)")
        } else {
            // Fallback for development or when bundle ID is not available
            serviceName = "com.potter.swift.api-keys"
            PotterLogger.shared.debug("keychain", "🔑 Using keychain service: \(serviceName) (fallback)")
        }
    }
    private var cache: [String: String]? = nil // nil = not loaded yet
    private let queue = DispatchQueue(label: "keychain-storage", qos: .userInitiated)
    
    func get(key: String) -> Result<String, PotterError> {
        return queue.sync {
            switch loadCacheIfNeeded() {
            case .success:
                guard let value = cache?[key] else {
                    return .failure(.storage(.keyNotFound(key: key)))
                }
                return .success(value)
            case .failure(let error):
                return .failure(error)
            }
        }
    }
    
    func put(key: String, value: String) -> Result<Void, PotterError> {
        return queue.sync {
            switch loadCacheIfNeeded() {
            case .success:
                cache?[key] = value
                return saveToKeychain()
            case .failure(let error):
                return .failure(error)
            }
        }
    }
    
    func remove(key: String) -> Result<Void, PotterError> {
        return queue.sync {
            switch loadCacheIfNeeded() {
            case .success:
                cache?.removeValue(forKey: key)
                return saveToKeychain()
            case .failure(let error):
                return .failure(error)
            }
        }
    }
    
    func clear() -> Result<Void, PotterError> {
        return queue.sync {
            cache = [:]
            return saveToKeychain()
        }
    }
    
    // MARK: - Private Implementation
    
    private func loadCacheIfNeeded() -> Result<Void, PotterError> {
        guard cache == nil else { 
            return .success(())
        }
        
        PotterLogger.shared.info("keychain", "🔑 Loading keychain cache...")
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: accountName,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        switch status {
        case errSecSuccess:
            if let data = result as? Data,
               let jsonString = String(data: data, encoding: .utf8),
               let jsonData = jsonString.data(using: .utf8),
               let apiKeys = try? JSONSerialization.jsonObject(with: jsonData) as? [String: String] {
                cache = apiKeys
                PotterLogger.shared.info("keychain", "✅ Loaded \(cache?.count ?? 0) keys from keychain")
            } else {
                PotterLogger.shared.error("keychain", "❌ Failed to deserialize keychain data")
                return .failure(.storage(.corruptedData(key: accountName)))
            }
        case errSecItemNotFound:
            // No data in keychain yet, start with empty cache
            cache = [:]
            PotterLogger.shared.info("keychain", "📝 No keychain data found, starting with empty cache")
        case errSecUserCanceled:
            PotterLogger.shared.error("keychain", "❌ User denied keychain access")
            return .failure(.storage(.permissionDenied(operation: "keychain read")))
        case errSecAuthFailed:
            PotterLogger.shared.error("keychain", "❌ Keychain authentication failed")
            return .failure(.storage(.permissionDenied(operation: "keychain authentication")))
        default:
            let errorMessage = keychainErrorMessage(for: status)
            PotterLogger.shared.error("keychain", "❌ Keychain access failed: \(errorMessage) (code: \(status))")
            return .failure(.storage(.loadFailed(key: accountName, reason: errorMessage)))
        }
        
        return .success(())
    }
    
    private func saveToKeychain() -> Result<Void, PotterError> {
        guard let cache = cache else {
            return .failure(.storage(.saveFailed(key: accountName, reason: "Cache not initialized")))
        }
        
        PotterLogger.shared.info("keychain", "🔑 Saving \(cache.count) keys to keychain...")
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: cache)
            guard let jsonString = String(data: jsonData, encoding: .utf8),
                  let data = jsonString.data(using: .utf8) else {
                PotterLogger.shared.error("keychain", "❌ Failed to serialize keychain data")
                return .failure(.storage(.saveFailed(key: accountName, reason: "JSON serialization failed")))
            }
            
            // Try to update existing item first
            let updateQuery: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrService as String: serviceName,
                kSecAttrAccount as String: accountName
            ]
            
            let updateAttributes: [String: Any] = [
                kSecValueData as String: data
            ]
            
            let updateStatus = SecItemUpdate(updateQuery as CFDictionary, updateAttributes as CFDictionary)
            
            if updateStatus == errSecSuccess {
                PotterLogger.shared.info("keychain", "✅ Updated keychain data successfully")
                return .success(())
            } else if updateStatus == errSecItemNotFound {
                // Item doesn't exist, create new one
                let addQuery: [String: Any] = [
                    kSecClass as String: kSecClassGenericPassword,
                    kSecAttrService as String: serviceName,
                    kSecAttrAccount as String: accountName,
                    kSecValueData as String: data,
                    kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
                    kSecAttrSynchronizable as String: false
                ]
                
                let addStatus = SecItemAdd(addQuery as CFDictionary, nil)
                
                if addStatus == errSecSuccess {
                    PotterLogger.shared.info("keychain", "✅ Created keychain data successfully")
                    return .success(())
                } else {
                    let errorMessage = keychainErrorMessage(for: addStatus)
                    PotterLogger.shared.error("keychain", "❌ Failed to create keychain data: \(errorMessage) (code: \(addStatus))")
                    return .failure(.storage(.saveFailed(key: accountName, reason: errorMessage)))
                }
            } else {
                let errorMessage = keychainErrorMessage(for: updateStatus)
                PotterLogger.shared.error("keychain", "❌ Failed to update keychain data: \(errorMessage) (code: \(updateStatus))")
                return .failure(.storage(.saveFailed(key: accountName, reason: errorMessage)))
            }
        } catch {
            PotterLogger.shared.error("keychain", "❌ JSON serialization error: \(error)")
            return .failure(.storage(.saveFailed(key: accountName, reason: "JSON serialization error: \(error.localizedDescription)")))
        }
    }
    
    private func keychainErrorMessage(for status: OSStatus) -> String {
        switch status {
        case errSecUserCanceled:
            return "User denied keychain access"
        case errSecAuthFailed:
            return "Authentication failed"
        case errSecInteractionNotAllowed:
            return "Keychain interaction not allowed"
        case errSecDuplicateItem:
            return "Item already exists"
        case errSecItemNotFound:
            return "Item not found"
        case errSecParam:
            return "Invalid parameters"
        case errSecNotAvailable:
            return "Keychain not available"
        case errSecReadOnly:
            return "Read-only"
        case errSecNoSuchKeychain:
            return "Keychain does not exist"
        case errSecInvalidKeychain:
            return "Invalid keychain"
        default:
            return "Unknown keychain error"
        }
    }
}

// MARK: - UserDefaults Storage Implementation

class UserDefaultsStorage: StorageBackend {
    func get(key: String) -> Result<String, PotterError> {
        PotterLogger.shared.info("userdefaults", "📋 Reading key: \(key)")
        let bundleId = Bundle.main.bundleIdentifier ?? "no-bundle-id"
        PotterLogger.shared.debug("userdefaults", "📋 Bundle ID during read: \(bundleId)")
        
        // Debug: Show which storage method is currently selected
        let currentMethod = UserDefaults.standard.string(forKey: "storage_method") ?? "not-set"
        PotterLogger.shared.debug("userdefaults", "📋 Current storage method: \(currentMethod)")
        
        guard let value = UserDefaults.standard.string(forKey: key), !value.isEmpty else {
            PotterLogger.shared.debug("userdefaults", "📋 Key '\(key)' not found or empty")
            return .failure(.storage(.keyNotFound(key: key)))
        }
        PotterLogger.shared.debug("userdefaults", "📋 Key '\(key)' found, value length: \(value.count)")
        return .success(value)
    }
    
    func put(key: String, value: String) -> Result<Void, PotterError> {
        PotterLogger.shared.info("userdefaults", "📋 Writing key: \(key)")
        let bundleId = Bundle.main.bundleIdentifier ?? "no-bundle-id"
        PotterLogger.shared.debug("userdefaults", "📋 Bundle ID during write: \(bundleId)")
        
        // Debug: Show which storage method is currently selected
        let currentMethod = UserDefaults.standard.string(forKey: "storage_method") ?? "not-set"
        PotterLogger.shared.debug("userdefaults", "📋 Current storage method during write: \(currentMethod)")
        PotterLogger.shared.debug("userdefaults", "📋 Writing value of length: \(value.count)")
        
        UserDefaults.standard.set(value, forKey: key)
        
        // Debug: Verify the write worked
        let verification = UserDefaults.standard.string(forKey: key)
        PotterLogger.shared.debug("userdefaults", "📋 Write verification - value exists: \(verification != nil), length: \(verification?.count ?? 0)")
        
        return .success(())
    }
    
    func remove(key: String) -> Result<Void, PotterError> {
        PotterLogger.shared.info("userdefaults", "📋 Removing key: \(key)")
        UserDefaults.standard.removeObject(forKey: key)
        return .success(())
    }
    
    func clear() -> Result<Void, PotterError> {
        PotterLogger.shared.info("userdefaults", "📋 Clearing all API keys")
        // Remove all API key entries
        for provider in LLMProvider.allCases {
            let key = "api_key_\(provider.rawValue)"
            UserDefaults.standard.removeObject(forKey: key)
        }
        return .success(())
    }
}

// MARK: - Storage Adapter

class StorageAdapter {
    static let shared = StorageAdapter()
    
    private let keychainStorage = KeychainStorage()
    private let userDefaultsStorage = UserDefaultsStorage()
    
    /// When true, forces UserDefaults storage for all operations (used in testing)
    public var forceUserDefaultsForTesting = false
    
    private init() {
        // Debug: Log bundle identifier and UserDefaults suite info
        let bundleId = Bundle.main.bundleIdentifier ?? "no-bundle-id"
        PotterLogger.shared.debug("storage", "🏗️ Storage initialized - Bundle ID: \(bundleId)")
        PotterLogger.shared.debug("storage", "🏗️ UserDefaults domain info available")
    }
    
    var currentStorageMethod: StorageMethod {
        get {
            // In testing mode, always use UserDefaults to avoid keychain access
            if forceUserDefaultsForTesting {
                return .userDefaults
            }
            let raw = UserDefaults.standard.string(forKey: "storage_method") ?? StorageMethod.userDefaults.rawValue
            return StorageMethod(rawValue: raw) ?? .userDefaults
        }
        set {
            // Don't save storage method changes during testing
            if !forceUserDefaultsForTesting {
                UserDefaults.standard.set(newValue.rawValue, forKey: "storage_method")
            }
        }
    }
    
    private var currentBackend: StorageBackend {
        // In testing mode, always use UserDefaults to avoid keychain access
        if forceUserDefaultsForTesting {
            return userDefaultsStorage
        }
        
        switch currentStorageMethod {
        case .keychain: 
            return keychainStorage
        case .userDefaults: 
            return userDefaultsStorage
        }
    }
    
    // MARK: - Security Utilities
    
    /// Sanitizes API keys to remove potentially dangerous characters
    private func sanitizeAPIKey(_ key: String) -> String {
        // Only remove null bytes which can cause storage issues
        // Preserve all other characters as they may be legitimate parts of API keys
        return key.replacingOccurrences(of: "\0", with: "")
    }
    
    // MARK: - Public API
    
    func saveAPIKey(_ key: String, for provider: LLMProvider) -> Result<Void, PotterError> {
        guard !key.isEmpty else {
            return .failure(.validation(.emptyInput(field: "API Key")))
        }
        
        // Sanitize the API key to remove dangerous characters
        let sanitizedKey = sanitizeAPIKey(key)
        
        // Check if sanitization resulted in an empty key
        guard !sanitizedKey.isEmpty else {
            return .failure(.validation(.invalidFormat(field: "API Key", pattern: "Non-empty after sanitization")))
        }
        
        let storageKey = "api_key_\(provider.rawValue)"
        return currentBackend.put(key: storageKey, value: sanitizedKey)
    }
    
    func loadAPIKey(for provider: LLMProvider) -> Result<String, PotterError> {
        let storageKey = "api_key_\(provider.rawValue)"
        return currentBackend.get(key: storageKey)
    }
    
    func removeAPIKey(for provider: LLMProvider) -> Result<Void, PotterError> {
        let storageKey = "api_key_\(provider.rawValue)"
        return currentBackend.remove(key: storageKey)
    }
    
    func hasAPIKey(for provider: LLMProvider) -> Bool {
        let storageKey = "api_key_\(provider.rawValue)"
        return currentBackend.get(key: storageKey).isSuccess
    }
    
    func clearAllAPIKeys() -> Result<Void, PotterError> {
        PotterLogger.shared.warning("storage", "🗑️ Clearing all API keys from \(currentStorageMethod.rawValue)")
        return currentBackend.clear()
    }
    
    func migrate(to newMethod: StorageMethod) -> Result<Void, PotterError> {
        guard newMethod != currentStorageMethod else {
            PotterLogger.shared.info("storage", "ℹ️ Already using \(newMethod.rawValue) storage")
            return .success(())
        }
        
        PotterLogger.shared.info("storage", "🔄 Migrating from \(currentStorageMethod.rawValue) to \(newMethod.rawValue)")
        
        let oldBackend = currentBackend
        let newBackend: StorageBackend = (newMethod == .keychain) ? keychainStorage : userDefaultsStorage
        
        // 1. Read all API keys from current storage
        var allKeys: [String: String] = [:]
        for provider in LLMProvider.allCases {
            let storageKey = "api_key_\(provider.rawValue)"
            switch oldBackend.get(key: storageKey) {
            case .success(let value):
                allKeys[storageKey] = value
            case .failure:
                // Key doesn't exist, skip it
                break
            }
        }
        
        // 2. Write all keys to new storage
        for (key, value) in allKeys {
            switch newBackend.put(key: key, value: value) {
            case .success:
                break
            case .failure(let error):
                PotterLogger.shared.error("storage", "❌ Migration failed writing to new storage: \(error.localizedDescription)")
                return .failure(.storage(.migrationFailed(from: currentStorageMethod.rawValue, to: newMethod.rawValue, reason: "Failed to write to new storage")))
            }
        }
        
        // 3. Update storage method preference
        currentStorageMethod = newMethod
        
        // 4. Clear old storage
        switch oldBackend.clear() {
        case .success:
            break
        case .failure(let error):
            PotterLogger.shared.warning("storage", "⚠️ Failed to clear old storage: \(error.localizedDescription)")
            // Don't fail migration for cleanup issues
        }
        
        PotterLogger.shared.info("storage", "✅ Migration completed: \(allKeys.count) keys migrated to \(newMethod.rawValue)")
        return .success(())
    }
    
    // MARK: - Testing Support
    
    func getStorageInfo() -> (method: StorageMethod, keyCount: Int) {
        var keyCount = 0
        for provider in LLMProvider.allCases {
            if hasAPIKey(for: provider) {
                keyCount += 1
            }
        }
        return (currentStorageMethod, keyCount)
    }
}
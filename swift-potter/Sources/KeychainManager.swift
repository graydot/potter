import Foundation
import Security

/// Single access point for all keychain operations using a unified storage approach
class KeychainManager {
    static let shared = KeychainManager()
    
    private let serviceName = "Potter-API-Keys"
    private let keychainAccount = "potter-all-keys"
    private let operationQueue = DispatchQueue(label: "keychain-operations", qos: .userInitiated)
    
    // In-memory cache of all API keys
    private var cache: [String: String] = [:]
    private var cacheLoaded = false
    private var isKeychainDenied = false
    
    private init() {}
    
    // MARK: - Public Interface
    
    /// Load API key for provider (loads all keys once, then uses cache)
    func loadAPIKey(for provider: LLMProvider) -> String? {
        return operationQueue.sync {
            loadAllKeysIfNeeded()
            return cache[provider.rawValue]
        }
    }
    
    /// Save API key for provider (saves entire dict to keychain)
    func saveAPIKey(_ apiKey: String, for provider: LLMProvider) -> Bool {
        return operationQueue.sync {
            loadAllKeysIfNeeded()
            
            // If keychain access was denied during load, attempt to save anyway and let user decide
            if isKeychainDenied {
                PotterLogger.shared.warning("keychain_manager", "⚠️ Keychain access was previously denied, but attempting to save anyway")
                // Reset the flag to allow retry
                isKeychainDenied = false
                cacheLoaded = false
            }
            
            cache[provider.rawValue] = apiKey
            return saveAllKeysToKeychain()
        }
    }
    
    /// Remove API key for provider (saves updated dict to keychain)
    func removeAPIKey(for provider: LLMProvider) -> Bool {
        return operationQueue.sync {
            loadAllKeysIfNeeded()
            cache.removeValue(forKey: provider.rawValue)
            return saveAllKeysToKeychain()
        }
    }
    
    /// Migrate all API keys from UserDefaults to keychain
    func migrateFromUserDefaults() -> [LLMProvider: Bool] {
        return operationQueue.sync {
            loadAllKeysIfNeeded()
            var results: [LLMProvider: Bool] = [:]
            var hasChanges = false
            
            for provider in LLMProvider.allCases {
                let userDefaultsKey = "api_key_\(provider.rawValue)"
                
                if let apiKey = UserDefaults.standard.string(forKey: userDefaultsKey), !apiKey.isEmpty {
                    cache[provider.rawValue] = apiKey
                    UserDefaults.standard.removeObject(forKey: userDefaultsKey)
                    hasChanges = true
                    results[provider] = true
                    PotterLogger.shared.info("keychain_manager", "🔄 Migrated \(provider.rawValue) from UserDefaults")
                } else {
                    results[provider] = true // No migration needed
                }
            }
            
            if hasChanges {
                let success = saveAllKeysToKeychain()
                if !success {
                    // Rollback on failure
                    for provider in LLMProvider.allCases {
                        if results[provider] == true, let key = cache[provider.rawValue] {
                            let userDefaultsKey = "api_key_\(provider.rawValue)"
                            UserDefaults.standard.set(key, forKey: userDefaultsKey)
                        }
                    }
                    return results.mapValues { _ in false }
                }
            }
            
            return results
        }
    }
    
    /// Export all API keys from keychain to UserDefaults
    func exportToUserDefaults() -> [LLMProvider: Bool] {
        return operationQueue.sync {
            loadAllKeysIfNeeded()
            var results: [LLMProvider: Bool] = [:]
            
            for provider in LLMProvider.allCases {
                if let apiKey = cache[provider.rawValue] {
                    let userDefaultsKey = "api_key_\(provider.rawValue)"
                    UserDefaults.standard.set(apiKey, forKey: userDefaultsKey)
                    results[provider] = true
                    PotterLogger.shared.info("keychain_manager", "💾 Exported \(provider.rawValue) to UserDefaults")
                } else {
                    results[provider] = true // No export needed
                }
            }
            
            // Clear keychain after successful export
            cache.removeAll()
            _ = saveAllKeysToKeychain()
            
            return results
        }
    }
    
    /// Remove all API keys
    func removeAllAPIKeys() -> Bool {
        return operationQueue.sync {
            cache.removeAll()
            return saveAllKeysToKeychain()
        }
    }
    
    /// Check if keychain is accessible
    func isKeychainAccessible() -> Bool {
        return operationQueue.sync {
            // First check if we already know keychain was denied
            if isKeychainDenied {
                return false
            }
            
            // Load keys if not loaded yet (this may set isKeychainDenied)
            loadAllKeysIfNeeded()
            
            // Return false if keychain was denied during load
            if isKeychainDenied {
                return false
            }
            
            // Otherwise, keychain is accessible
            return true
        }
    }
    
    /// Get cache info for debugging
    func getCacheInfo() -> (loaded: Bool, count: Int) {
        return operationQueue.sync {
            return (cacheLoaded, cache.count)
        }
    }
    
    // MARK: - Private Implementation
    
    /// Load all keys from keychain once (single keychain prompt)
    private func loadAllKeysIfNeeded() {
        guard !cacheLoaded else { 
            return 
        }
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: keychainAccount,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        if status == errSecSuccess,
           let data = result as? Data,
           let jsonString = String(data: data, encoding: .utf8),
           let jsonData = jsonString.data(using: .utf8),
           let apiKeys = try? JSONSerialization.jsonObject(with: jsonData) as? [String: String] {
            
            cache = apiKeys
            PotterLogger.shared.info("keychain_manager", "✅ Loaded \(cache.count) API keys from keychain")
        } else if status == errSecItemNotFound {
            // No unified storage found, try to migrate from old individual keychain items
            cache = migrateFromOldKeychainFormat()
            PotterLogger.shared.info("keychain_manager", "🔄 No unified storage found, migrated \(cache.count) keys from old format")
        } else {
            // Handle keychain access errors (user denial, etc.)
            let errorMessage = keychainErrorMessage(for: status)
            PotterLogger.shared.error("keychain_manager", "❌ Failed to load keychain data: \(errorMessage) (code: \(status))")
            
            // Set cache to empty but mark as inaccessible
            cache = [:]
            isKeychainDenied = true
        }
        
        cacheLoaded = true
    }
    
    /// Migrate from old individual keychain items to unified storage
    private func migrateFromOldKeychainFormat() -> [String: String] {
        var migratedKeys: [String: String] = [:]
        
        for provider in LLMProvider.allCases {
            if let apiKey = loadOldIndividualKey(for: provider) {
                migratedKeys[provider.rawValue] = apiKey
                PotterLogger.shared.info("keychain_manager", "🔄 Migrated old keychain item for \(provider.rawValue)")
                
                // Remove old individual item
                _ = removeOldIndividualKey(for: provider)
            }
        }
        
        if !migratedKeys.isEmpty {
            // Save to new unified format
            let tempCache = cache
            cache = migratedKeys
            if saveAllKeysToKeychain() {
                PotterLogger.shared.info("keychain_manager", "✅ Successfully migrated \(migratedKeys.count) keys to unified storage")
            } else {
                PotterLogger.shared.error("keychain_manager", "❌ Failed to save migrated keys")
                cache = tempCache
                return [:]
            }
        }
        
        return migratedKeys
    }
    
    /// Load API key from old individual keychain format
    private func loadOldIndividualKey(for provider: LLMProvider) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: provider.rawValue,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        if status == errSecSuccess,
           let data = result as? Data,
           let apiKey = String(data: data, encoding: .utf8) {
            return apiKey
        }
        
        return nil
    }
    
    /// Remove old individual keychain item
    private func removeOldIndividualKey(for provider: LLMProvider) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: provider.rawValue
        ]
        
        let status = SecItemDelete(query as CFDictionary)
        return status == errSecSuccess || status == errSecItemNotFound
    }
    
    /// Save all keys to keychain as a single JSON dict (single keychain prompt)
    private func saveAllKeysToKeychain() -> Bool {
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: cache)
            guard let jsonString = String(data: jsonData, encoding: .utf8),
                  let data = jsonString.data(using: .utf8) else {
                PotterLogger.shared.error("keychain_manager", "❌ Failed to serialize API keys")
                return false
            }
            
            // Try to update existing item first
            let updateQuery: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrService as String: serviceName,
                kSecAttrAccount as String: keychainAccount
            ]
            
            let updateAttributes: [String: Any] = [
                kSecValueData as String: data
            ]
            
            let updateStatus = SecItemUpdate(updateQuery as CFDictionary, updateAttributes as CFDictionary)
            
            if updateStatus == errSecSuccess {
                PotterLogger.shared.info("keychain_manager", "✅ Updated \(cache.count) API keys in keychain")
                return true
            } else if updateStatus == errSecItemNotFound {
                // Item doesn't exist, create new one
                let addQuery: [String: Any] = [
                    kSecClass as String: kSecClassGenericPassword,
                    kSecAttrService as String: serviceName,
                    kSecAttrAccount as String: keychainAccount,
                    kSecValueData as String: data,
                    kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
                    kSecAttrSynchronizable as String: false
                ]
                
                let addStatus = SecItemAdd(addQuery as CFDictionary, nil)
                
                if addStatus == errSecSuccess {
                    PotterLogger.shared.info("keychain_manager", "✅ Saved \(cache.count) API keys to keychain")
                    return true
                } else {
                    let errorMessage = keychainErrorMessage(for: addStatus)
                    PotterLogger.shared.error("keychain_manager", "❌ Failed to save API keys to keychain: \(errorMessage) (code: \(addStatus))")
                    return false
                }
            } else {
                let errorMessage = keychainErrorMessage(for: updateStatus)
                PotterLogger.shared.error("keychain_manager", "❌ Failed to update API keys in keychain: \(errorMessage) (code: \(updateStatus))")
                return false
            }
        } catch {
            PotterLogger.shared.error("keychain_manager", "❌ JSON serialization error: \(error)")
            return false
        }
    }
    
    // MARK: - Error Handling Helpers
    
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
        case errSecAllocate:
            return "Memory allocation failed"
        case errSecNotAvailable:
            return "Keychain not available"
        case errSecUnimplemented:
            return "Function not implemented"
        case errSecDiskFull:
            return "Disk full"
        case errSecIO:
            return "I/O error"
        case errSecOpWr:
            return "File already open for writing"
        case errSecReadOnly:
            return "Read-only"
        case errSecNoSuchKeychain:
            return "Keychain does not exist"
        case errSecInvalidKeychain:
            return "Invalid keychain"
        case errSecDuplicateKeychain:
            return "Keychain already exists"
        case errSecDuplicateCallback:
            return "Duplicate callback"
        case errSecInvalidCallback:
            return "Invalid callback"
        case errSecBufferTooSmall:
            return "Buffer too small"
        case errSecDataTooLarge:
            return "Data too large"
        case errSecNoSuchAttr:
            return "Attribute does not exist"
        case errSecInvalidItemRef:
            return "Invalid item reference"
        case errSecInvalidSearchRef:
            return "Invalid search reference"
        case errSecNoSuchClass:
            return "Class does not exist"
        case errSecNoDefaultKeychain:
            return "No default keychain"
        case errSecInteractionRequired:
            return "User interaction required"
        case errSecReadOnlyAttr:
            return "Attribute is read-only"
        case errSecWrongSecVersion:
            return "Wrong security version"
        case errSecKeySizeNotAllowed:
            return "Key size not allowed"
        case errSecNoStorageModule:
            return "No storage module available"
        case errSecNoCertificateModule:
            return "No certificate module available"
        case errSecNoPolicyModule:
            return "No policy module available"
        case errSecNoAccessForItem:
            return "No access for item"
        case errSecInvalidOwnerEdit:
            return "Invalid owner edit"
        case errSecTrustNotAvailable:
            return "Trust not available"
        case errSecUnsupportedFormat:
            return "Unsupported format"
        case errSecUnknownFormat:
            return "Unknown format"
        case errSecKeyIsSensitive:
            return "Key is sensitive and cannot be extracted"
        case errSecMultiplePrivKeys:
            return "Multiple private keys"
        case errSecPassphraseRequired:
            return "Passphrase required"
        case errSecInvalidPasswordRef:
            return "Invalid password reference"
        case errSecNoTrustSettings:
            return "No trust settings"
        case errSecPkcs12VerifyFailure:
            return "PKCS12 verification failure"
        case errSecDecode:
            return "Unable to decode"
        default:
            return "Unknown keychain error"
        }
    }
}
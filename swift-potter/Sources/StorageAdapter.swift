import Foundation

// MARK: - Storage Method

enum StorageMethod: String, CaseIterable {
    case userDefaults = "userdefaults"
    
    var displayName: String {
        return "UserDefaults (Plain Text)"
    }
    
    var isSecure: Bool {
        return false
    }
}

// MARK: - Storage Backend Protocol

protocol StorageBackend {
    func get(key: String) -> Result<String, PotterError>
    func put(key: String, value: String) -> Result<Void, PotterError>
    func remove(key: String) -> Result<Void, PotterError>
    func clear() -> Result<Void, PotterError>
}

// MARK: - UserDefaults Storage Implementation

class UserDefaultsStorage: StorageBackend {
    private let userDefaults: UserDefaults
    
    init(userDefaults: UserDefaults = UserDefaults.standard) {
        self.userDefaults = userDefaults
    }
    
    func get(key: String) -> Result<String, PotterError> {
        PotterLogger.shared.debug("userdefaults", "📋 Reading key: \(key)")
        
        guard let value = userDefaults.string(forKey: key) else {
            PotterLogger.shared.warning("userdefaults", "❌ NOT FOUND in UserDefaults for key: \(key)")
            return .failure(.storage(.keyNotFound(key: key)))
        }
        
        let maskedValue = String(value.prefix(8)) + "..." + String(value.suffix(4))
        PotterLogger.shared.debug("userdefaults", "✅ SUCCESS - Found value: \(maskedValue)")
        
        return .success(value)
    }
    
    func put(key: String, value: String) -> Result<Void, PotterError> {
        let maskedValue = String(value.prefix(8)) + "..." + String(value.suffix(4))
        PotterLogger.shared.info("userdefaults", "📋 Writing key: \(key), value: \(maskedValue)")
        
        userDefaults.set(value, forKey: key)
        userDefaults.synchronize()
        
        return .success(())
    }
    
    func remove(key: String) -> Result<Void, PotterError> {
        PotterLogger.shared.info("userdefaults", "📋 Removing key: \(key)")
        userDefaults.removeObject(forKey: key)
        return .success(())
    }
    
    func clear() -> Result<Void, PotterError> {
        PotterLogger.shared.info("userdefaults", "📋 Clearing all API keys")
        // Remove all API key entries
        for provider in LLMProvider.allCases {
            let key = "api_key_\(provider.rawValue)"
            userDefaults.removeObject(forKey: key)
        }
        return .success(())
    }
}

// MARK: - Storage Adapter

class StorageAdapter {
    static let shared = StorageAdapter()
    
    /// Cache for loaded API keys
    private var cache: [String: String] = [:]
    private var cacheLoaded = false
    private let cacheQueue = DispatchQueue(label: "storage-cache", qos: .userInitiated)
    
    /// When true, forces UserDefaults storage for all operations (used in testing)
    public var forceUserDefaultsForTesting = false
    
    /// Test-specific UserDefaults suite to isolate test storage from production
    public var testUserDefaults: UserDefaults?
    
    private init() {
        // Debug: Log bundle identifier and UserDefaults suite info
        let bundleId = Bundle.main.bundleIdentifier ?? "no-bundle-id"
        PotterLogger.shared.debug("storage", "🏗️ Storage initialized - Bundle ID: \(bundleId)")
        PotterLogger.shared.debug("storage", "🏗️ UserDefaults domain info available")
    }
    
    var currentStorageMethod: StorageMethod {
        get {
            return .userDefaults
        }
        set {
            // Always userDefaults now, so this is a no-op
            PotterLogger.shared.debug("storage", "Storage method is always UserDefaults now")
        }
    }
    
    var currentBackend: StorageBackend {
        // Use test UserDefaults if available, otherwise use standard
        let userDefaults = testUserDefaults ?? UserDefaults.standard
        return UserDefaultsStorage(userDefaults: userDefaults)
    }
    
    // MARK: - Public API
    
    func setAPIKey(_ apiKey: String, for provider: LLMProvider) -> Result<Void, PotterError> {
        let storageKey = "api_key_\(provider.rawValue)"
        let result = currentBackend.put(key: storageKey, value: apiKey)
        
        // Update cache if successful
        if case .success = result {
            cacheQueue.sync {
                cache[storageKey] = apiKey
                cacheLoaded = true
            }
        }
        
        return result
    }
    
    func getAPIKey(for provider: LLMProvider) -> Result<String, PotterError> {
        let storageKey = "api_key_\(provider.rawValue)"
        return currentBackend.get(key: storageKey)
    }
    
    func removeAPIKey(for provider: LLMProvider) -> Result<Void, PotterError> {
        let storageKey = "api_key_\(provider.rawValue)"
        let result = currentBackend.remove(key: storageKey)
        
        // Update cache if successful
        if case .success = result {
            cacheQueue.sync {
                cache.removeValue(forKey: storageKey)
                cacheLoaded = true
            }
        }
        
        return result
    }
    
    func hasAPIKey(for provider: LLMProvider) -> Bool {
        let storageKey = "api_key_\(provider.rawValue)"
        
        return cacheQueue.sync {
            loadCacheIfNeeded()
            return cache[storageKey] != nil && !cache[storageKey]!.isEmpty
        }
    }
    
    func clearAllAPIKeys() -> Result<Void, PotterError> {
        PotterLogger.shared.warning("storage", "🗑️ Clearing all API keys from \(currentStorageMethod.rawValue)")
        let result = currentBackend.clear()
        
        // Clear cache after clearing storage
        cacheQueue.sync {
            cache.removeAll()
            cacheLoaded = true // Mark as loaded but empty
        }
        
        return result
    }
    
    // MARK: - Cache Management
    
    private func loadCacheIfNeeded() {
        guard !cacheLoaded else { return }
        
        PotterLogger.shared.debug("storage", "📦 Loading cache from \(currentStorageMethod.rawValue)")
        
        // Load all API keys for all providers
        for provider in LLMProvider.allCases {
            let storageKey = "api_key_\(provider.rawValue)"
            let result = currentBackend.get(key: storageKey)
            
            switch result {
            case .success(let value):
                cache[storageKey] = value
            case .failure:
                // Key doesn't exist, don't add to cache
                break
            }
        }
        
        cacheLoaded = true
        PotterLogger.shared.debug("storage", "📦 Cache loaded with \(cache.count) keys")
    }
    
    /// Force cache to be reloaded on next access (useful for testing)
    func invalidateCache() {
        cacheQueue.sync {
            cache.removeAll()
            cacheLoaded = false
        }
    }
}
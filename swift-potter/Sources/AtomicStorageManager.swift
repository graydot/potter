import Foundation

/// Atomic storage manager that provides race-condition-free operations
/// for API key storage and migration between storage methods
class AtomicStorageManager {
    static let shared = AtomicStorageManager()
    
    private let operationQueue = DispatchQueue(label: "atomic-storage", qos: .userInitiated)
    private var activeOperations: Set<String> = []
    private let operationLock = NSLock()
    
    
    private init() {}
    
    // MARK: - Operation Result Types
    
    enum StorageResult {
        case success
        case failure(StorageError)
    }
    
    enum StorageError: LocalizedError {
        case operationInProgress
        case keychainFailure(String)
        case userDefaultsFailure(String)
        case migrationFailed(String)
        case validationFailed(String)
        case rollbackFailed(String)
        
        var errorDescription: String? {
            switch self {
            case .operationInProgress:
                return "Storage operation already in progress"
            case .keychainFailure(let message):
                return "Keychain operation failed: \(message)"
            case .userDefaultsFailure(let message):
                return "UserDefaults operation failed: \(message)"
            case .migrationFailed(let message):
                return "Migration failed: \(message)"
            case .validationFailed(let message):
                return "Validation failed: \(message)"
            case .rollbackFailed(let message):
                return "Rollback failed: \(message)"
            }
        }
    }
    
    // MARK: - Atomic Operations
    
    /// Atomically save an API key with validation and rollback capability
    func atomicSave(
        apiKey: String,
        for provider: LLMProvider,
        using method: APIKeyStorageMethod,
        previousMethod: APIKeyStorageMethod? = nil
    ) async -> StorageResult {
        let operationId = "save_\(provider.rawValue)_\(UUID().uuidString.prefix(8))"
        
        return await performAtomicOperation(operationId: operationId) { [self] in
            // 1. Backup current state if migrating
            var backup: (method: APIKeyStorageMethod, key: String)?
            if let prevMethod = previousMethod {
                if let existingKey = self.loadAPIKey(for: provider, from: prevMethod) {
                    backup = (prevMethod, existingKey)
                    PotterLogger.shared.info("storage", "📦 Created backup for migration: \(provider.rawValue)")
                }
            }
            
            // 2. Save to new location
            let saveResult = self.saveAPIKey(apiKey, for: provider, to: method)
            guard case .success = saveResult else {
                PotterLogger.shared.error("storage", "❌ Save operation failed: \(saveResult)")
                return saveResult
            }
            
            // 3. Validate the save operation
            guard let savedKey = self.loadAPIKey(for: provider, from: method),
                  savedKey == apiKey else {
                PotterLogger.shared.error("storage", "❌ Validation failed after save")
                
                // Rollback if validation fails
                if let backup = backup {
                    _ = self.saveAPIKey(backup.key, for: provider, to: backup.method)
                    PotterLogger.shared.info("storage", "🔄 Rolled back to previous storage method")
                }
                
                return .failure(.validationFailed("Saved key doesn't match expected value"))
            }
            
            // 4. Clean up old location if migrating
            if let prevMethod = previousMethod, prevMethod != method {
                let cleanupResult = self.removeAPIKey(for: provider, from: prevMethod)
                if case .failure(let error) = cleanupResult {
                    PotterLogger.shared.warning("storage", "⚠️ Cleanup warning (non-critical): \(error)")
                    // Don't fail the operation for cleanup issues
                }
            }
            
            PotterLogger.shared.info("storage", "✅ Atomic save completed: \(provider.rawValue) -> \(method.rawValue)")
            return .success
        }
    }
    
    /// Atomically migrate API key between storage methods
    func atomicMigration(
        for provider: LLMProvider,
        from sourceMethod: APIKeyStorageMethod,
        to targetMethod: APIKeyStorageMethod
    ) async -> StorageResult {
        let operationId = "migrate_\(provider.rawValue)_\(UUID().uuidString.prefix(8))"
        
        return await performAtomicOperation(operationId: operationId) { [self] in
            // 1. Load current key from source
            guard let apiKey = self.loadAPIKey(for: provider, from: sourceMethod) else {
                return .failure(.migrationFailed("No API key found in source storage"))
            }
            
            // 2. Validate source key is not empty
            guard !apiKey.isEmpty else {
                return .failure(.migrationFailed("Source API key is empty"))
            }
            
            // 3. Save to target location
            let saveResult = self.saveAPIKey(apiKey, for: provider, to: targetMethod)
            guard case .success = saveResult else {
                return .failure(.migrationFailed("Failed to save to target storage: \(saveResult)"))
            }
            
            // 4. Validate target has the correct key
            guard let targetKey = self.loadAPIKey(for: provider, from: targetMethod),
                  targetKey == apiKey else {
                return .failure(.migrationFailed("Target validation failed"))
            }
            
            // 5. Remove from source only after target is confirmed
            let removeResult = self.removeAPIKey(for: provider, from: sourceMethod)
            if case .failure(let error) = removeResult {
                // If removal fails, we have duplicates but target is valid
                PotterLogger.shared.warning("storage", "⚠️ Source cleanup failed: \(error)")
                // Continue - having duplicates is better than losing the key
            }
            
            // 6. Update storage method preference
            self.updateStorageMethodPreference(targetMethod, for: provider)
            
            PotterLogger.shared.info("storage", "✅ Migration completed: \(provider.rawValue) \(sourceMethod.rawValue) -> \(targetMethod.rawValue)")
            return .success
        }
    }
    
    /// Atomically remove API key with confirmation
    func atomicRemove(
        for provider: LLMProvider,
        from method: APIKeyStorageMethod
    ) async -> StorageResult {
        let operationId = "remove_\(provider.rawValue)_\(UUID().uuidString.prefix(8))"
        
        return await performAtomicOperation(operationId: operationId) { [self] in
            // 1. Create backup before removal
            let backup = self.loadAPIKey(for: provider, from: method)
            
            // 2. Remove from storage
            let removeResult = self.removeAPIKey(for: provider, from: method)
            guard case .success = removeResult else {
                return removeResult
            }
            
            // 3. Validate removal
            if let stillExists = self.loadAPIKey(for: provider, from: method), !stillExists.isEmpty {
                // Removal failed, restore backup
                if let backup = backup {
                    _ = self.saveAPIKey(backup, for: provider, to: method)
                    PotterLogger.shared.warning("storage", "🔄 Restored backup after failed removal")
                }
                return .failure(.validationFailed("API key still exists after removal"))
            }
            
            PotterLogger.shared.info("storage", "✅ Atomic removal completed: \(provider.rawValue)")
            return .success
        }
    }
    
    // MARK: - Private Operation Management
    
    private func performAtomicOperation(
        operationId: String,
        operation: @escaping () -> StorageResult
    ) async -> StorageResult {
        return await withCheckedContinuation { continuation in
            operationQueue.async {
                // Check for concurrent operations
                self.operationLock.lock()
                let providerPrefix = operationId.components(separatedBy: "_").dropLast().joined(separator: "_")
                if self.activeOperations.contains(where: { $0.hasPrefix(providerPrefix) }) {
                    self.operationLock.unlock()
                    continuation.resume(returning: .failure(.operationInProgress))
                    return
                }
                self.activeOperations.insert(operationId)
                self.operationLock.unlock()
                
                // Perform operation
                let result = operation()
                
                // Cleanup
                self.operationLock.lock()
                self.activeOperations.remove(operationId)
                self.operationLock.unlock()
                
                continuation.resume(returning: result)
            }
        }
    }
    
    // MARK: - Storage Implementation Methods
    
    private func saveAPIKey(_ key: String, for provider: LLMProvider, to method: APIKeyStorageMethod) -> StorageResult {
        switch method {
        case .keychain:
            let success = KeychainManager.shared.saveAPIKey(key, for: provider)
            return success ? .success : .failure(.keychainFailure("Failed to save to keychain"))
            
        case .userDefaults:
            UserDefaults.standard.set(key, forKey: "api_key_\(provider.rawValue)")
            // Verify save
            let saved = UserDefaults.standard.string(forKey: "api_key_\(provider.rawValue)")
            return saved == key ? .success : .failure(.userDefaultsFailure("Failed to save to UserDefaults"))
        }
    }
    
    private func loadAPIKey(for provider: LLMProvider, from method: APIKeyStorageMethod) -> String? {
        switch method {
        case .keychain:
            return KeychainManager.shared.loadAPIKey(for: provider)
            
        case .userDefaults:
            return UserDefaults.standard.string(forKey: "api_key_\(provider.rawValue)")
        }
    }
    
    private func removeAPIKey(for provider: LLMProvider, from method: APIKeyStorageMethod) -> StorageResult {
        switch method {
        case .keychain:
            let success = KeychainManager.shared.removeAPIKey(for: provider)
            return success ? .success : .failure(.keychainFailure("Failed to remove from keychain"))
            
        case .userDefaults:
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
            // Verify removal
            let removed = UserDefaults.standard.string(forKey: "api_key_\(provider.rawValue)")
            return removed == nil ? .success : .failure(.userDefaultsFailure("Failed to remove from UserDefaults"))
        }
    }
    
    private func updateStorageMethodPreference(_ method: APIKeyStorageMethod, for provider: LLMProvider) {
        UserDefaults.standard.set(method.rawValue, forKey: "api_key_storage_method_\(provider.rawValue)")
    }
    
    // MARK: - Public Query Methods
    
    /// Check if an operation is currently in progress for a provider
    func isOperationInProgress(for provider: LLMProvider) -> Bool {
        operationLock.lock()
        defer { operationLock.unlock() }
        
        let providerOperationPrefix = "save_\(provider.rawValue)"
        return activeOperations.contains { $0.hasPrefix(providerOperationPrefix) }
    }
    
    /// Get current storage status for a provider
    func getStorageStatus(for provider: LLMProvider) -> StorageStatus {
        let keychainKey = KeychainManager.shared.loadAPIKey(for: provider)
        let userDefaultsKey = UserDefaults.standard.string(forKey: "api_key_\(provider.rawValue)")
        
        if let keychainKey = keychainKey, !keychainKey.isEmpty,
           let userDefaultsKey = userDefaultsKey, !userDefaultsKey.isEmpty {
            return .duplicateStorage(keychain: keychainKey, userDefaults: userDefaultsKey)
        } else if let keychainKey = keychainKey, !keychainKey.isEmpty {
            return .keychainOnly(keychainKey)
        } else if let userDefaultsKey = userDefaultsKey, !userDefaultsKey.isEmpty {
            return .userDefaultsOnly(userDefaultsKey)
        } else {
            return .noStorage
        }
    }
    
    enum StorageStatus {
        case noStorage
        case keychainOnly(String)
        case userDefaultsOnly(String)
        case duplicateStorage(keychain: String, userDefaults: String)
        
        var hasAPIKey: Bool {
            switch self {
            case .noStorage:
                return false
            case .keychainOnly, .userDefaultsOnly, .duplicateStorage:
                return true
            }
        }
        
        var preferredKey: String? {
            switch self {
            case .noStorage:
                return nil
            case .keychainOnly(let key), .userDefaultsOnly(let key):
                return key
            case .duplicateStorage(let keychainKey, _):
                // Prefer keychain in case of duplicates
                return keychainKey
            }
        }
    }
}
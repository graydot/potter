import Foundation

// MARK: - Core Error Types

/// Top-level error type for all Potter-related errors
/// Provides consistent error handling and user-friendly messages
enum PotterError: LocalizedError, Equatable {
    case configuration(ConfigurationError)
    case network(NetworkError)
    case storage(StorageError)
    case permission(PermissionError)
    case validation(ValidationError)
    case system(SystemError)
    
    var errorDescription: String? {
        switch self {
        case .configuration(let error): return error.userMessage
        case .network(let error): return error.userMessage
        case .storage(let error): return error.userMessage
        case .permission(let error): return error.userMessage
        case .validation(let error): return error.userMessage
        case .system(let error): return error.userMessage
        }
    }
    
    /// Technical description for logging purposes
    var technicalDescription: String {
        switch self {
        case .configuration(let error): return error.technicalDescription
        case .network(let error): return error.technicalDescription
        case .storage(let error): return error.technicalDescription
        case .permission(let error): return error.technicalDescription
        case .validation(let error): return error.technicalDescription
        case .system(let error): return error.technicalDescription
        }
    }
    
    /// Error severity for prioritizing user notifications
    var severity: ErrorSeverity {
        switch self {
        case .configuration(let error): return error.severity
        case .network(let error): return error.severity
        case .storage(let error): return error.severity
        case .permission(let error): return error.severity
        case .validation(let error): return error.severity
        case .system(let error): return error.severity
        }
    }
}

// MARK: - Error Severity

enum ErrorSeverity: String, CaseIterable {
    case critical = "critical"  // App cannot function
    case high = "high"         // Major feature broken
    case medium = "medium"     // Minor feature issue
    case low = "low"          // Cosmetic or edge case
    
    var shouldShowAlert: Bool {
        switch self {
        case .critical, .high: return true
        case .medium, .low: return false
        }
    }
}

// MARK: - Configuration Errors

enum ConfigurationError: LocalizedError, Equatable {
    case invalidAPIKey(provider: String)
    case missingAPIKey(provider: String)
    case missingConfiguration(key: String)
    case invalidFormat(field: String, expected: String)
    case unsupportedProvider(provider: String)
    case invalidModel(modelId: String, provider: String)
    case corruptedSettings(reason: String)
    
    var userMessage: String {
        switch self {
        case .invalidAPIKey(let provider):
            return "Invalid API key for \(provider). Please check your key and try again."
        case .missingAPIKey(let provider):
            return "Please add your \(provider) API key in Settings to continue."
        case .missingConfiguration(let key):
            return "Missing required configuration: \(key). Please check your settings."
        case .invalidFormat(let field, let expected):
            return "Invalid \(field) format. Expected: \(expected)."
        case .unsupportedProvider(let provider):
            return "Provider '\(provider)' is not supported."
        case .invalidModel(let modelId, let provider):
            return "Model '\(modelId)' is not available for \(provider)."
        case .corruptedSettings(let reason):
            return "Settings file is corrupted: \(reason). Please reset your settings."
        }
    }
    
    var technicalDescription: String {
        switch self {
        case .invalidAPIKey(let provider):
            return "API key validation failed for provider: \(provider)"
        case .missingAPIKey(let provider):
            return "No API key found for provider: \(provider)"
        case .missingConfiguration(let key):
            return "Configuration key not found: \(key)"
        case .invalidFormat(let field, let expected):
            return "Field '\(field)' format validation failed, expected: \(expected)"
        case .unsupportedProvider(let provider):
            return "Unsupported LLM provider: \(provider)"
        case .invalidModel(let modelId, let provider):
            return "Model '\(modelId)' not found for provider '\(provider)'"
        case .corruptedSettings(let reason):
            return "Settings corruption detected: \(reason)"
        }
    }
    
    var severity: ErrorSeverity {
        switch self {
        case .missingAPIKey: return .critical
        case .invalidAPIKey: return .high
        case .corruptedSettings: return .high
        case .unsupportedProvider, .invalidModel: return .medium
        case .missingConfiguration, .invalidFormat: return .medium
        }
    }
}

// MARK: - Network Errors

enum NetworkError: LocalizedError, Equatable {
    case noInternetConnection
    case timeout(duration: TimeInterval)
    case serverError(statusCode: Int, message: String?)
    case invalidResponse(reason: String)
    case rateLimited(retryAfter: TimeInterval?)
    case unauthorized(provider: String)
    case invalidURL(urlString: String)
    case requestFailed(underlying: String)
    
    var userMessage: String {
        switch self {
        case .noInternetConnection:
            return "No internet connection. Please check your network and try again."
        case .timeout(let duration):
            return "Request timed out after \(Int(duration)) seconds. Please try again."
        case .serverError(let statusCode, let message):
            if let message = message {
                return "Server error (\(statusCode)): \(message)"
            } else {
                return "Server error (HTTP \(statusCode)). Please try again later."
            }
        case .invalidResponse(let reason):
            return "Invalid response from server: \(reason). Please try again."
        case .rateLimited(let retryAfter):
            if let retryAfter = retryAfter {
                return "Rate limit exceeded. Please wait \(Int(retryAfter)) seconds before trying again."
            } else {
                return "Rate limit exceeded. Please wait a moment before trying again."
            }
        case .unauthorized(let provider):
            return "Invalid API key for \(provider). Please check your credentials."
        case .invalidURL:
            return "Invalid server URL. Please contact support."
        case .requestFailed(let underlying):
            return "Network request failed: \(underlying)"
        }
    }
    
    var technicalDescription: String {
        switch self {
        case .noInternetConnection:
            return "Network reachability check failed"
        case .timeout(let duration):
            return "URLSession timeout after \(duration) seconds"
        case .serverError(let statusCode, let message):
            return "HTTP \(statusCode): \(message ?? "No message")"
        case .invalidResponse(let reason):
            return "Response parsing failed: \(reason)"
        case .rateLimited(let retryAfter):
            return "Rate limited, retry after: \(retryAfter?.description ?? "unknown")"
        case .unauthorized(let provider):
            return "HTTP 401/403 for provider: \(provider)"
        case .invalidURL(let urlString):
            return "Invalid URL: \(urlString)"
        case .requestFailed(let underlying):
            return "URLSession error: \(underlying)"
        }
    }
    
    var severity: ErrorSeverity {
        switch self {
        case .noInternetConnection: return .critical
        case .unauthorized: return .high
        case .serverError: return .high
        case .timeout, .rateLimited: return .medium
        case .invalidResponse, .invalidURL, .requestFailed: return .medium
        }
    }
}

// MARK: - Storage Errors

enum StorageError: LocalizedError, Equatable {
    case keyNotFound(key: String)
    case saveFailed(key: String, reason: String)
    case loadFailed(key: String, reason: String)
    case deleteFailed(key: String, reason: String)
    case keychainUnavailable
    case migrationFailed(from: String, to: String, reason: String)
    case corruptedData(key: String)
    case insufficientSpace
    case permissionDenied(operation: String)
    
    var userMessage: String {
        switch self {
        case .keyNotFound:
            return "Data not found. Please reconfigure your settings."
        case .saveFailed:
            return "Failed to save settings. Please try again."
        case .loadFailed:
            return "Failed to load settings. Some preferences may be reset."
        case .deleteFailed:
            return "Failed to remove data. Please try again."
        case .keychainUnavailable:
            return "Secure storage is unavailable. Settings will be stored less securely."
        case .migrationFailed:
            return "Failed to update storage format. Some settings may be lost."
        case .corruptedData:
            return "Settings data is corrupted. Please reset your preferences."
        case .insufficientSpace:
            return "Insufficient storage space. Please free up space and try again."
        case .permissionDenied:
            return "Permission denied for storage operation. Please check system settings."
        }
    }
    
    var technicalDescription: String {
        switch self {
        case .keyNotFound(let key):
            return "Storage key not found: \(key)"
        case .saveFailed(let key, let reason):
            return "Save failed for key '\(key)': \(reason)"
        case .loadFailed(let key, let reason):
            return "Load failed for key '\(key)': \(reason)"
        case .deleteFailed(let key, let reason):
            return "Delete failed for key '\(key)': \(reason)"
        case .keychainUnavailable:
            return "Keychain services unavailable or denied"
        case .migrationFailed(let from, let to, let reason):
            return "Migration failed from '\(from)' to '\(to)': \(reason)"
        case .corruptedData(let key):
            return "Data corruption detected for key: \(key)"
        case .insufficientSpace:
            return "Disk space insufficient for storage operation"
        case .permissionDenied(let operation):
            return "Permission denied for operation: \(operation)"
        }
    }
    
    var severity: ErrorSeverity {
        switch self {
        case .migrationFailed, .corruptedData: return .high
        case .keychainUnavailable, .permissionDenied: return .medium
        case .saveFailed, .loadFailed: return .medium
        case .keyNotFound, .deleteFailed: return .low
        case .insufficientSpace: return .medium
        }
    }
}

// MARK: - Permission Errors

enum PermissionError: LocalizedError, Equatable {
    case accessibilityDenied
    case notificationsDenied
    case fileSystemDenied(path: String)
    case networkDenied
    case microphoneDenied
    case cameraDenied
    case unknownPermission(permission: String)
    
    var userMessage: String {
        switch self {
        case .accessibilityDenied:
            return "Accessibility permission is required for global hotkeys. Please enable it in System Settings > Privacy & Security > Accessibility."
        case .notificationsDenied:
            return "Notification permission was denied. You can enable it in System Settings > Notifications."
        case .fileSystemDenied(let path):
            return "File access permission denied for: \(path). Please check system settings."
        case .networkDenied:
            return "Network access permission denied. Please check system settings."
        case .microphoneDenied:
            return "Microphone access permission denied."
        case .cameraDenied:
            return "Camera access permission denied."
        case .unknownPermission(let permission):
            return "Permission denied for: \(permission). Please check system settings."
        }
    }
    
    var technicalDescription: String {
        switch self {
        case .accessibilityDenied:
            return "AXIsProcessTrusted() returned false"
        case .notificationsDenied:
            return "UNAuthorizationStatus.denied for notifications"
        case .fileSystemDenied(let path):
            return "File system access denied for path: \(path)"
        case .networkDenied:
            return "Network access permission denied"
        case .microphoneDenied:
            return "AVAuthorizationStatus.denied for microphone"
        case .cameraDenied:
            return "AVAuthorizationStatus.denied for camera"
        case .unknownPermission(let permission):
            return "Permission denied for: \(permission)"
        }
    }
    
    var severity: ErrorSeverity {
        switch self {
        case .accessibilityDenied: return .critical
        case .notificationsDenied: return .low
        case .fileSystemDenied, .networkDenied: return .medium
        case .microphoneDenied, .cameraDenied: return .low
        case .unknownPermission: return .medium
        }
    }
}

// MARK: - Validation Errors

enum ValidationError: LocalizedError, Equatable {
    case emptyInput(field: String)
    case invalidLength(field: String, min: Int?, max: Int?)
    case invalidFormat(field: String, pattern: String)
    case invalidCharacters(field: String, allowedCharacters: String)
    case valueOutOfRange(field: String, min: Double?, max: Double?)
    case duplicateValue(field: String, value: String)
    case dependencyMissing(field: String, dependency: String)
    
    var userMessage: String {
        switch self {
        case .emptyInput(let field):
            return "\(field) cannot be empty."
        case .invalidLength(let field, let min, let max):
            if let min = min, let max = max {
                return "\(field) must be between \(min) and \(max) characters."
            } else if let min = min {
                return "\(field) must be at least \(min) characters."
            } else if let max = max {
                return "\(field) must be no more than \(max) characters."
            } else {
                return "\(field) has invalid length."
            }
        case .invalidFormat(let field, let pattern):
            return "\(field) format is invalid. Expected pattern: \(pattern)"
        case .invalidCharacters(let field, let allowedCharacters):
            return "\(field) contains invalid characters. Allowed: \(allowedCharacters)"
        case .valueOutOfRange(let field, let min, let max):
            if let min = min, let max = max {
                return "\(field) must be between \(min) and \(max)."
            } else if let min = min {
                return "\(field) must be at least \(min)."
            } else if let max = max {
                return "\(field) must be no more than \(max)."
            } else {
                return "\(field) value is out of range."
            }
        case .duplicateValue(let field, let value):
            return "\(field) '\(value)' already exists."
        case .dependencyMissing(let field, let dependency):
            return "\(field) requires \(dependency) to be set first."
        }
    }
    
    var technicalDescription: String {
        switch self {
        case .emptyInput(let field):
            return "Empty input validation failed for field: \(field)"
        case .invalidLength(let field, let min, let max):
            return "Length validation failed for '\(field)': min=\(min?.description ?? "nil"), max=\(max?.description ?? "nil")"
        case .invalidFormat(let field, let pattern):
            return "Format validation failed for '\(field)' with pattern: \(pattern)"
        case .invalidCharacters(let field, let allowedCharacters):
            return "Character validation failed for '\(field)': allowed=\(allowedCharacters)"
        case .valueOutOfRange(let field, let min, let max):
            return "Range validation failed for '\(field)': min=\(min?.description ?? "nil"), max=\(max?.description ?? "nil")"
        case .duplicateValue(let field, let value):
            return "Duplicate value validation failed for '\(field)': \(value)"
        case .dependencyMissing(let field, let dependency):
            return "Dependency validation failed for '\(field)': missing \(dependency)"
        }
    }
    
    var severity: ErrorSeverity {
        switch self {
        case .emptyInput, .dependencyMissing: return .medium
        case .invalidLength, .invalidFormat, .invalidCharacters: return .low
        case .valueOutOfRange, .duplicateValue: return .low
        }
    }
}

// MARK: - System Errors

enum SystemError: LocalizedError, Equatable {
    case insufficientMemory
    case diskSpaceLow
    case processLimitReached
    case systemCallFailed(call: String, errno: Int32)
    case unsupportedVersion(current: String, required: String)
    case resourceUnavailable(resource: String)
    case threadingError(reason: String)
    
    var userMessage: String {
        switch self {
        case .insufficientMemory:
            return "Insufficient memory available. Please close other applications and try again."
        case .diskSpaceLow:
            return "Low disk space. Please free up space and try again."
        case .processLimitReached:
            return "System process limit reached. Please restart the application."
        case .systemCallFailed:
            return "System operation failed. Please restart the application."
        case .unsupportedVersion(let current, let required):
            return "Unsupported system version. Current: \(current), Required: \(required)"
        case .resourceUnavailable(let resource):
            return "System resource unavailable: \(resource). Please try again later."
        case .threadingError:
            return "Internal threading error. Please restart the application."
        }
    }
    
    var technicalDescription: String {
        switch self {
        case .insufficientMemory:
            return "Memory allocation failed"
        case .diskSpaceLow:
            return "Disk space below threshold"
        case .processLimitReached:
            return "Process creation failed: limit reached"
        case .systemCallFailed(let call, let errno):
            return "System call '\(call)' failed with errno: \(errno)"
        case .unsupportedVersion(let current, let required):
            return "Version check failed: current=\(current), required=\(required)"
        case .resourceUnavailable(let resource):
            return "Resource unavailable: \(resource)"
        case .threadingError(let reason):
            return "Threading error: \(reason)"
        }
    }
    
    var severity: ErrorSeverity {
        switch self {
        case .insufficientMemory, .processLimitReached: return .critical
        case .diskSpaceLow, .unsupportedVersion: return .high
        case .systemCallFailed, .resourceUnavailable: return .medium
        case .threadingError: return .high
        }
    }
}

// MARK: - Result Type Extensions

extension Result where Failure == PotterError {
    /// Creates a configuration error result
    static func configurationError(_ error: ConfigurationError) -> Result<Success, PotterError> {
        return .failure(.configuration(error))
    }
    
    /// Creates a network error result
    static func networkError(_ error: NetworkError) -> Result<Success, PotterError> {
        return .failure(.network(error))
    }
    
    /// Creates a storage error result
    static func storageError(_ error: StorageError) -> Result<Success, PotterError> {
        return .failure(.storage(error))
    }
    
    /// Creates a permission error result
    static func permissionError(_ error: PermissionError) -> Result<Success, PotterError> {
        return .failure(.permission(error))
    }
    
    /// Creates a validation error result
    static func validationError(_ error: ValidationError) -> Result<Success, PotterError> {
        return .failure(.validation(error))
    }
    
    /// Creates a system error result
    static func systemError(_ error: SystemError) -> Result<Success, PotterError> {
        return .failure(.system(error))
    }
    
    /// Convenience property to check if result is successful
    var isSuccess: Bool {
        switch self {
        case .success: return true
        case .failure: return false
        }
    }
    
    /// Convenience property to check if result is a failure
    var isFailure: Bool {
        return !isSuccess
    }
}
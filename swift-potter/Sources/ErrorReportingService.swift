import Foundation
import AppKit

// MARK: - Error Reporting Protocol

/// Protocol for centralized error handling and user feedback
protocol ErrorReporting {
    /// Reports an error for logging and internal tracking
    func report(_ error: PotterError, context: String)
    
    /// Shows a user-friendly error dialog
    func showUserError(_ error: PotterError, in window: NSWindow?)
    
    /// Reports an error and optionally shows user dialog based on severity
    func handle(_ error: PotterError, context: String, showUser: Bool?)
    
    /// Reports a non-Potter error by converting it first
    func report(_ error: Error, context: String, category: ErrorCategory)
}

/// Categories for converting non-Potter errors
enum ErrorCategory {
    case configuration
    case network
    case storage
    case permission
    case validation
    case system
}

// MARK: - Error Reporting Service Implementation

class ErrorReportingService: ErrorReporting {
    
    private let logger: PotterLogger
    
    init(logger: PotterLogger = PotterLogger.shared) {
        self.logger = logger
    }
    
    // MARK: - Error Reporting
    
    func report(_ error: PotterError, context: String) {
        // Log the error with appropriate level based on severity
        let logLevel = mapSeverityToLogLevel(error.severity)
        let sanitizedMessage = "[\(context)] \(error.technicalDescription)"
        
        switch logLevel {
        case .error:
            logger.error("error_service", sanitizedMessage)
        case .warning:
            logger.warning("error_service", sanitizedMessage)
        case .info:
            logger.info("error_service", sanitizedMessage)
        case .debug:
            logger.debug("error_service", sanitizedMessage)
        }
        
        // Post notification for other components to react
        DispatchQueue.main.async {
            NotificationCenter.default.post(
                name: .potterErrorOccurred,
                object: error,
                userInfo: ["context": context]
            )
        }
    }
    
    func showUserError(_ error: PotterError, in window: NSWindow?) {
        DispatchQueue.main.async {
            let alert = self.createAlert(for: error)
            
            if let window = window {
                alert.beginSheetModal(for: window) { _ in
                    // Alert completed
                }
            } else {
                alert.runModal()
            }
        }
    }
    
    func handle(_ error: PotterError, context: String, showUser: Bool? = nil) {
        // Always report the error
        report(error, context: context)
        
        // Determine whether to show user dialog
        let shouldShowUser = showUser ?? error.severity.shouldShowAlert
        
        if shouldShowUser {
            showUserError(error, in: nil)
        }
    }
    
    func report(_ error: Error, context: String, category: ErrorCategory) {
        let potterError = convertToPotterError(error, category: category)
        report(potterError, context: context)
    }
    
    // MARK: - Private Helper Methods
    
    private func mapSeverityToLogLevel(_ severity: ErrorSeverity) -> PotterLogger.LogEntry.LogLevel {
        switch severity {
        case .critical: return .error
        case .high: return .error
        case .medium: return .warning
        case .low: return .info
        }
    }
    
    private func createAlert(for error: PotterError) -> NSAlert {
        let alert = NSAlert()
        
        // Set alert style based on severity
        switch error.severity {
        case .critical:
            alert.alertStyle = .critical
            alert.messageText = "Critical Error"
        case .high:
            alert.alertStyle = .warning
            alert.messageText = "Error"
        case .medium:
            alert.alertStyle = .warning
            alert.messageText = "Warning"
        case .low:
            alert.alertStyle = .informational
            alert.messageText = "Notice"
        }
        
        // Set the informative text to the user-friendly message
        alert.informativeText = error.localizedDescription
        
        // Add appropriate buttons based on error type
        alert.addButton(withTitle: "OK")
        
        // Add additional buttons for specific error types
        switch error {
        case .permission(.accessibilityDenied):
            alert.addButton(withTitle: "Open System Settings")
        case .configuration(.missingAPIKey):
            alert.addButton(withTitle: "Open Settings")
        default:
            break
        }
        
        // Set icon based on severity
        switch error.severity {
        case .critical:
            alert.icon = NSImage(systemSymbolName: "exclamationmark.triangle.fill", accessibilityDescription: "Critical Error")
        case .high:
            alert.icon = NSImage(systemSymbolName: "exclamationmark.circle.fill", accessibilityDescription: "Error")
        case .medium:
            alert.icon = NSImage(systemSymbolName: "exclamationmark.triangle", accessibilityDescription: "Warning")
        case .low:
            alert.icon = NSImage(systemSymbolName: "info.circle", accessibilityDescription: "Information")
        }
        
        return alert
    }
    
    private func convertToPotterError(_ error: Error, category: ErrorCategory) -> PotterError {
        let errorDescription = error.localizedDescription
        
        switch category {
        case .configuration:
            return .configuration(.invalidFormat(field: "unknown", expected: errorDescription))
        case .network:
            if let urlError = error as? URLError {
                switch urlError.code {
                case .notConnectedToInternet:
                    return .network(.noInternetConnection)
                case .timedOut:
                    return .network(.timeout(duration: 30.0))
                default:
                    return .network(.requestFailed(underlying: errorDescription))
                }
            } else {
                return .network(.requestFailed(underlying: errorDescription))
            }
        case .storage:
            return .storage(.loadFailed(key: "unknown", reason: errorDescription))
        case .permission:
            return .permission(.unknownPermission(permission: errorDescription))
        case .validation:
            return .validation(.invalidFormat(field: "unknown", pattern: errorDescription))
        case .system:
            return .system(.systemCallFailed(call: "unknown", errno: 0))
        }
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let potterErrorOccurred = Notification.Name("PotterErrorOccurred")
}

// MARK: - Error Handling Utilities

extension ErrorReportingService {
    
    /// Convenience method for handling Result types
    func handleResult<T>(_ result: Result<T, PotterError>, context: String, showUser: Bool? = nil) -> T? {
        switch result {
        case .success(let value):
            return value
        case .failure(let error):
            handle(error, context: context, showUser: showUser)
            return nil
        }
    }
    
    /// Convenience method for handling async Result types
    func handleResultAsync<T>(_ result: Result<T, PotterError>, context: String, showUser: Bool? = nil) async -> T? {
        switch result {
        case .success(let value):
            return value
        case .failure(let error):
            await MainActor.run {
                handle(error, context: context, showUser: showUser)
            }
            return nil
        }
    }
    
    /// Creates a generic success result
    static func success<T>(_ value: T) -> Result<T, PotterError> {
        return .success(value)
    }
    
    /// Creates a generic failure result
    static func failure<T>(_ error: PotterError) -> Result<T, PotterError> {
        return .failure(error)
    }
}

// MARK: - Global Error Handler

/// Global convenience instance for error reporting
/// Use this for simple error reporting when dependency injection is not available
class GlobalErrorHandler {
    static let shared = ErrorReportingService()
    
    /// Quick error reporting without creating service instances
    static func report(_ error: PotterError, context: String = "global") {
        shared.report(error, context: context)
    }
    
    /// Quick error handling with optional user dialog
    static func handle(_ error: PotterError, context: String = "global", showUser: Bool? = nil) {
        shared.handle(error, context: context, showUser: showUser)
    }
}
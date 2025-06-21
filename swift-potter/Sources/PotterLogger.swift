import Foundation
import OSLog
import AppKit

class PotterLogger: ObservableObject {
    static let shared = PotterLogger()
    
    @Published var logEntries: [LogEntry] = []
    private let maxLogEntries = 500
    private let logger = Logger(subsystem: "com.potter.app", category: "general")
    
    struct LogEntry {
        let timestamp: Date
        let level: LogLevel
        let component: String
        let message: String
        
        enum LogLevel: String, CaseIterable {
            case info = "INFO"
            case warning = "WARNING"
            case error = "ERROR"
            case debug = "DEBUG"
            
            var color: NSColor {
                switch self {
                case .info: return .systemBlue
                case .warning: return .systemOrange
                case .error: return .systemRed
                case .debug: return .systemGray
                }
            }
        }
        
        var formattedString: String {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd HH:mm:ss.SSS"
            return "\(formatter.string(from: timestamp)) - \(component) - \(level.rawValue) - \(message)"
        }
    }
    
    private init() {
        // Add initial startup logs
        log(.info, component: "main", message: "🎭 Potter - AI Text Processing Tool")
        log(.info, component: "main", message: "Starting Swift version...")
    }
    
    func log(_ level: LogEntry.LogLevel, component: String, message: String) {
        let sanitizedMessage = sanitizeMessage(message)
        let entry = LogEntry(
            timestamp: Date(),
            level: level,
            component: component,
            message: sanitizedMessage
        )
        
        DispatchQueue.main.async {
            self.logEntries.append(entry)
            
            // Keep only the most recent entries
            if self.logEntries.count > self.maxLogEntries {
                self.logEntries.removeFirst(self.logEntries.count - self.maxLogEntries)
            }
        }
        
        // Also log to system logger (using sanitized message)
        switch level {
        case .info:
            logger.info("\(component) - \(sanitizedMessage)")
        case .warning:
            logger.warning("\(component) - \(sanitizedMessage)")
        case .error:
            logger.error("\(component) - \(sanitizedMessage)")
        case .debug:
            logger.debug("\(component) - \(sanitizedMessage)")
        }
        
        // Print to console for development (using sanitized message)
        print("\(entry.formattedString)")
    }
    
    func info(_ component: String, _ message: String) {
        log(.info, component: component, message: message)
    }
    
    func warning(_ component: String, _ message: String) {
        log(.warning, component: component, message: message)
    }
    
    func error(_ component: String, _ message: String) {
        log(.error, component: component, message: message)
    }
    
    func debug(_ component: String, _ message: String) {
        log(.debug, component: component, message: message)
    }
    
    func clearLogs() {
        DispatchQueue.main.async {
            self.logEntries.removeAll()
        }
        log(.info, component: "logger", message: "Log entries cleared")
    }
    
    // MARK: - Message Sanitization
    
    /// Sanitizes log messages to prevent exposure of sensitive information
    /// including API keys, user content, URLs with secrets, and other PII
    private func sanitizeMessage(_ message: String) -> String {
        var sanitized = message
        
        // 1. API Key Patterns - Common cloud providers and LLM services
        let apiKeyPatterns = [
            // OpenAI keys (flexible length to catch various formats)
            (#"sk-[A-Za-z0-9]{20,64}"#, "[OPENAI_KEY_REDACTED]"),
            (#"sk-proj-[A-Za-z0-9_-]{20,64}"#, "[OPENAI_PROJECT_KEY_REDACTED]"),
            
            // Anthropic keys
            (#"sk-ant-[A-Za-z0-9_-]{64,128}"#, "[ANTHROPIC_KEY_REDACTED]"),
            
            // Google keys
            (#"AIza[A-Za-z0-9_-]{35,39}"#, "[GOOGLE_KEY_REDACTED]"),
            
            // AWS credentials
            (#"AKIA[A-Z0-9]{16}"#, "[AWS_ACCESS_KEY_REDACTED]"),
            (#"(?i)aws_secret_access_key[\s]*[:=][\s]*[A-Za-z0-9/+=]{40}"#, "[AWS_SECRET_KEY_REDACTED]"),
            
            // Azure keys
            (#"[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}"#, "[AZURE_GUID_REDACTED]"),
            
            // Generic API key patterns
            (#"(?i)(?:api[_-]?key|apikey|access[_-]?token|bearer[_-]?token)[\s]*[:=][\s]*['\"]?([A-Za-z0-9_+/=-]{20,})['\"]?"#, "[API_TOKEN_REDACTED]"),
            
            // JWT tokens (rough pattern)
            (#"ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"#, "[JWT_TOKEN_REDACTED]"),
            
            // Base64 encoded data that might be sensitive (if looks like credentials)
            (#"(?i)(?:password|secret|token|key)[\s]*[:=][\s]*[A-Za-z0-9+/]{32,}={0,2}"#, "[BASE64_CREDENTIAL_REDACTED]")
        ]
        
        for (pattern, replacement) in apiKeyPatterns {
            sanitized = sanitized.replacingOccurrences(
                of: pattern,
                with: replacement,
                options: .regularExpression
            )
        }
        
        // 2. URL Parameter Sanitization - Remove sensitive query parameters
        let urlParameterPatterns = [
            (#"([?&](?:key|token|secret|password|auth|api_key|access_token)=)[^&\s]+"#, "$1[REDACTED]"),
            (#"([?&](?:sk-[^&\s]+))"#, "$1[REDACTED_KEY]")
        ]
        
        for (pattern, replacement) in urlParameterPatterns {
            sanitized = sanitized.replacingOccurrences(
                of: pattern,
                with: replacement,
                options: .regularExpression
            )
        }
        
        // 3. JSON Field Sanitization - Redact sensitive JSON fields
        let jsonFieldPatterns = [
            (#"("(?:api_key|apiKey|access_token|accessToken|password|secret|token|authorization|bearer)"\s*:\s*)"[^"]*""#, "$1\"[REDACTED]\""),
            (#"("(?:api_key|apiKey|access_token|accessToken|password|secret|token|authorization|bearer)"\s*:\s*)[^,}\s]+"#, "$1[REDACTED]")
        ]
        
        for (pattern, replacement) in jsonFieldPatterns {
            sanitized = sanitized.replacingOccurrences(
                of: pattern,
                with: replacement,
                options: .regularExpression
            )
        }
        
        // 4. User Content Protection - Redact text that appears to be user input
        let userContentPatterns = [
            // Text between our typical separators
            (#"\|\|\|\|\|.*?\|\|\|\|\|"#, "[USER_TEXT_REDACTED]"),
            
            // Long text that might be user content (>100 chars in various contexts)
            (#"(?i)(?:text|content|message|prompt|input)[\s]*[:=]?[\s]*['\"]?(.{100,})['\"]?"#, "[LONG_USER_CONTENT_REDACTED]"),
            
            // Any very long single message that might contain user data
            (#"^.{500,}$"#, "[VERY_LONG_CONTENT_REDACTED]"),
            
            // Email addresses (potential PII)
            (#"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"#, "[EMAIL_REDACTED]")
        ]
        
        for (pattern, replacement) in userContentPatterns {
            sanitized = sanitized.replacingOccurrences(
                of: pattern,
                with: replacement,
                options: .regularExpression
            )
        }
        
        // 5. File Path Sanitization - Redact potentially sensitive paths
        let pathPatterns = [
            // Home directory paths that might reveal username
            (#"/Users/[^/\s]+(/.*)?/(?:\.ssh|\.aws|\.config|\.env)"#, "/Users/[USER_REDACTED]$1/[SENSITIVE_DIR]"),
            
            // API key files
            (#"[^\s]*(?:api[_-]?key|secret|credential|token)[^\s]*\.(json|txt|pem|key)"#, "[CREDENTIAL_FILE_REDACTED]")
        ]
        
        for (pattern, replacement) in pathPatterns {
            sanitized = sanitized.replacingOccurrences(
                of: pattern,
                with: replacement,
                options: .regularExpression
            )
        }
        
        // 6. Header Sanitization - Clean authorization headers
        if sanitized.contains("Authorization:") || sanitized.contains("authorization:") {
            sanitized = sanitized.replacingOccurrences(
                of: #"(?i)(authorization:\s*(?:bearer|basic)\s+)[^\s\n,]+"#,
                with: "$1[AUTH_HEADER_REDACTED]",
                options: .regularExpression
            )
        }
        
        // 7. Special Context Sanitization
        if sanitized.lowercased().contains("processing user text") {
            sanitized = "Processing user text [CONTENT_REDACTED_FOR_PRIVACY]"
        }
        
        return sanitized
    }
    
    func filteredEntries(level: LogEntry.LogLevel?) -> [LogEntry] {
        guard let level = level else { return logEntries }
        return logEntries.filter { $0.level == level }
    }
    
    func saveLogsToFile() -> URL? {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd_HH-mm-ss"
        let filename = "potter_logs_\(formatter.string(from: Date())).txt"
        
        let documentsPath = FileManager.default.urls(for: .documentDirectory, 
                                                   in: .userDomainMask).first!
        let logFileURL = documentsPath.appendingPathComponent(filename)
        
        let logContent = logEntries.map { $0.formattedString }.joined(separator: "\n")
        
        do {
            try logContent.write(to: logFileURL, atomically: true, encoding: .utf8)
            return logFileURL
        } catch {
            log(.error, component: "logger", message: "Failed to save logs: \(error)")
            return nil
        }
    }
}
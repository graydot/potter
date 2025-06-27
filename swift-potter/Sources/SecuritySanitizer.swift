import Foundation

// MARK: - Security Sanitizer
/// Handles sanitization of sensitive information in log messages and strings
/// Separates security concerns from logging infrastructure
class SecuritySanitizer {
    
    static let shared = SecuritySanitizer()
    
    private init() {}
    
    // MARK: - Public Interface
    
    /// Main sanitization method that applies all security patterns
    func sanitizeMessage(_ message: String) -> String {
        var sanitized = message
        
        // Apply sanitization in order of specificity
        sanitized = sanitizeAPIKeys(sanitized)
        sanitized = sanitizeURLParameters(sanitized)
        sanitized = sanitizeJSONFields(sanitized)
        sanitized = sanitizeUserContent(sanitized)
        sanitized = sanitizeFilePaths(sanitized)
        sanitized = sanitizeHeaders(sanitized)
        sanitized = sanitizeSpecialContexts(sanitized)
        
        return sanitized
    }
    
    // MARK: - API Key Sanitization
    
    /// Sanitizes various API key formats from cloud providers and LLM services
    private func sanitizeAPIKeys(_ message: String) -> String {
        let patterns = APIKeySanitizer.patterns
        return applyPatterns(patterns, to: message)
    }
    
    // MARK: - URL Parameter Sanitization
    
    /// Removes sensitive query parameters from URLs
    private func sanitizeURLParameters(_ message: String) -> String {
        let patterns = URLParameterSanitizer.patterns
        return applyPatterns(patterns, to: message)
    }
    
    // MARK: - JSON Field Sanitization
    
    /// Redacts sensitive JSON fields
    private func sanitizeJSONFields(_ message: String) -> String {
        let patterns = JSONFieldSanitizer.patterns
        return applyPatterns(patterns, to: message)
    }
    
    // MARK: - User Content Protection
    
    /// Redacts text that appears to be user input or PII
    private func sanitizeUserContent(_ message: String) -> String {
        let patterns = UserContentSanitizer.patterns
        return applyPatterns(patterns, to: message)
    }
    
    // MARK: - File Path Sanitization
    
    /// Redacts potentially sensitive file paths
    private func sanitizeFilePaths(_ message: String) -> String {
        let patterns = FilePathSanitizer.patterns
        return applyPatterns(patterns, to: message)
    }
    
    // MARK: - Header Sanitization
    
    /// Cleans authorization headers
    private func sanitizeHeaders(_ message: String) -> String {
        var sanitized = message
        
        if sanitized.contains("Authorization:") || sanitized.contains("authorization:") {
            sanitized = sanitized.replacingOccurrences(
                of: #"(?i)(authorization:\s*(?:bearer|basic)\s+)[^\s\n,]+"#,
                with: "$1[AUTH_HEADER_REDACTED]",
                options: .regularExpression
            )
        }
        
        return sanitized
    }
    
    // MARK: - Special Context Sanitization
    
    /// Handles specific context patterns
    private func sanitizeSpecialContexts(_ message: String) -> String {
        var sanitized = message
        
        if sanitized.lowercased().contains("processing user text") {
            sanitized = "Processing user text [CONTENT_REDACTED_FOR_PRIVACY]"
        }
        
        return sanitized
    }
    
    // MARK: - Helper Methods
    
    /// Applies an array of regex patterns to a string
    private func applyPatterns(_ patterns: [(String, String)], to message: String) -> String {
        var result = message
        
        for (pattern, replacement) in patterns {
            result = result.replacingOccurrences(
                of: pattern,
                with: replacement,
                options: .regularExpression
            )
        }
        
        return result
    }
}

// MARK: - API Key Sanitizer
private struct APIKeySanitizer {
    static let patterns: [(String, String)] = [
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
        
        // Base64 encoded data that might be sensitive
        (#"(?i)(?:password|secret|token|key)[\s]*[:=][\s]*[A-Za-z0-9+/]{32,}={0,2}"#, "[BASE64_CREDENTIAL_REDACTED]")
    ]
}

// MARK: - URL Parameter Sanitizer
private struct URLParameterSanitizer {
    static let patterns: [(String, String)] = [
        (#"([?&](?:key|token|secret|password|auth|api_key|access_token)=)[^&\s]+"#, "$1[REDACTED]"),
        (#"([?&](?:sk-[^&\s]+))"#, "$1[REDACTED_KEY]")
    ]
}

// MARK: - JSON Field Sanitizer
private struct JSONFieldSanitizer {
    static let patterns: [(String, String)] = [
        (#"("(?:api_key|apiKey|access_token|accessToken|password|secret|token|authorization|bearer)"\s*:\s*)"[^"]*""#, "$1\"[REDACTED]\""),
        (#"("(?:api_key|apiKey|access_token|accessToken|password|secret|token|authorization|bearer)"\s*:\s*)[^,}\s]+"#, "$1[REDACTED]")
    ]
}

// MARK: - User Content Sanitizer
private struct UserContentSanitizer {
    static let patterns: [(String, String)] = [
        // Text between our typical separators
        (#"\|\|\|\|\|.*?\|\|\|\|\|"#, "[USER_TEXT_REDACTED]"),
        
        // Long text that might be user content (>100 chars in various contexts)
        (#"(?i)(?:text|content|message|prompt|input)[\s]*[:=]?[\s]*['\"]?(.{100,})['\"]?"#, "[LONG_USER_CONTENT_REDACTED]"),
        
        // Any very long single message that might contain user data
        (#"^.{500,}$"#, "[VERY_LONG_CONTENT_REDACTED]"),
        
        // Email addresses (potential PII)
        (#"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"#, "[EMAIL_REDACTED]")
    ]
}

// MARK: - File Path Sanitizer
private struct FilePathSanitizer {
    static let patterns: [(String, String)] = [
        // Home directory paths that might reveal username
        (#"/Users/[^/\s]+(/.*)?/(?:\.ssh|\.aws|\.config|\.env)"#, "/Users/[USER_REDACTED]$1/[SENSITIVE_DIR]"),
        
        // API key files
        (#"[^\s]*(?:api[_-]?key|secret|credential|token)[^\s]*\.(json|txt|pem|key)"#, "[CREDENTIAL_FILE_REDACTED]")
    ]
}
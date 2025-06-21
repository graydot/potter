#!/usr/bin/env swift
import Foundation

// Quick test to verify our log sanitization is working
print("🔒 Testing Log Sanitization")
print(String(repeating: "=", count: 40))

// Test data with various sensitive patterns
let testMessages = [
    "API validation with key: sk-1234567890abcdefghijklmnopqrstuvwxyz123456",
    "Anthropic key: sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890_abcdefghijklmnopqrstuvwxyz1234567890",
    "Google API key: AIzaSyDxKL-abcdefghijklmnopqrstuvwxyz123",
    "Request URL: https://api.openai.com/v1/chat?key=sk-secretkey123",
    "User text processing: |||||Hello this is my secret document with passwords|||||",
    "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4ifQ.abc123",
    "Config: {\"api_key\": \"sk-verysecret123\", \"password\": \"mypassword\"}",
    "Email found: user@company.com in logs",
    "Processing user text content with 200+ characters that might contain sensitive information like social security numbers, credit card details, or other private data that should not appear in logs",
    "File path: /Users/john/.ssh/id_rsa with secret key"
]

// Reproduce the sanitization logic from PotterLogger
func sanitizeMessage(_ message: String) -> String {
    var sanitized = message
    
    // API Key Patterns
    let apiKeyPatterns = [
        (#"sk-[A-Za-z0-9]{48,64}"#, "[OPENAI_KEY_REDACTED]"),
        (#"sk-proj-[A-Za-z0-9_-]{20,64}"#, "[OPENAI_PROJECT_KEY_REDACTED]"),
        (#"sk-ant-[A-Za-z0-9_-]{64,128}"#, "[ANTHROPIC_KEY_REDACTED]"),
        (#"AIza[A-Za-z0-9_-]{35,39}"#, "[GOOGLE_KEY_REDACTED]"),
        (#"(?i)(?:api[_-]?key|apikey|access[_-]?token|bearer[_-]?token)[\s]*[:=][\s]*['\"]?([A-Za-z0-9_+/=-]{20,})['\"]?"#, "[API_TOKEN_REDACTED]"),
        (#"ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"#, "[JWT_TOKEN_REDACTED]"),
    ]
    
    for (pattern, replacement) in apiKeyPatterns {
        sanitized = sanitized.replacingOccurrences(
            of: pattern,
            with: replacement,
            options: .regularExpression
        )
    }
    
    // URL Parameter Sanitization
    let urlParameterPatterns = [
        (#"([?&](?:key|token|secret|password|auth|api_key|access_token)=)[^&\s]+"#, "$1[REDACTED]"),
    ]
    
    for (pattern, replacement) in urlParameterPatterns {
        sanitized = sanitized.replacingOccurrences(
            of: pattern,
            with: replacement,
            options: .regularExpression
        )
    }
    
    // JSON Field Sanitization
    let jsonFieldPatterns = [
        (#"("(?:api_key|apiKey|access_token|accessToken|password|secret|token|authorization|bearer)"\s*:\s*)"[^"]*""#, "$1\"[REDACTED]\""),
    ]
    
    for (pattern, replacement) in jsonFieldPatterns {
        sanitized = sanitized.replacingOccurrences(
            of: pattern,
            with: replacement,
            options: .regularExpression
        )
    }
    
    // User Content Protection
    let userContentPatterns = [
        (#"\|\|\|\|\|.*?\|\|\|\|\|"#, "[USER_TEXT_REDACTED]"),
        (#"(?i)(?:text|content|message|prompt|input)[\s]*[:=][\s]*['\"](.{200,})['\"]"#, "[LONG_USER_CONTENT_REDACTED]"),
        (#"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"#, "[EMAIL_REDACTED]"),
    ]
    
    for (pattern, replacement) in userContentPatterns {
        sanitized = sanitized.replacingOccurrences(
            of: pattern,
            with: replacement,
            options: .regularExpression
        )
    }
    
    // File Path Sanitization
    let pathPatterns = [
        (#"/Users/[^/\s]+(/.*)?/(?:\.ssh|\.aws|\.config|\.env)"#, "/Users/[USER_REDACTED]$1/[SENSITIVE_DIR]"),
    ]
    
    for (pattern, replacement) in pathPatterns {
        sanitized = sanitized.replacingOccurrences(
            of: pattern,
            with: replacement,
            options: .regularExpression
        )
    }
    
    // Header Sanitization
    if sanitized.contains("Authorization:") || sanitized.contains("authorization:") {
        sanitized = sanitized.replacingOccurrences(
            of: #"(?i)(authorization:\s*(?:bearer|basic)\s+)[^\s\n,]+"#,
            with: "$1[AUTH_HEADER_REDACTED]",
            options: .regularExpression
        )
    }
    
    return sanitized
}

// Test each message
for (index, message) in testMessages.enumerated() {
    print("\nTest \(index + 1):")
    print("BEFORE: \(message)")
    print("AFTER:  \(sanitizeMessage(message))")
    print(String(repeating: "-", count: 40))
}

print("\n✅ Sanitization test complete!")
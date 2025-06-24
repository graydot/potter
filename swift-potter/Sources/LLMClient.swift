import Foundation

// MARK: - LLM Model Definitions
struct LLMModel: Identifiable, Hashable {
    let id: String
    let name: String
    let description: String
    let provider: LLMProvider
    
    static let openAIModels = [
        LLMModel(id: "o4-mini", name: "o4-mini", description: "Latest reasoning model, excellent for math, coding, and logical tasks", provider: .openAI),
        LLMModel(id: "o3", name: "o3", description: "Most powerful reasoning model for complex scientific and technical problems", provider: .openAI),
        LLMModel(id: "gpt-4.1", name: "GPT-4.1", description: "Latest GPT model with major improvements in coding and instruction following", provider: .openAI),
        LLMModel(id: "gpt-4.1-mini", name: "GPT-4.1 Mini", description: "Fast and efficient with excellent performance, 83% cheaper than GPT-4o", provider: .openAI),
        LLMModel(id: "gpt-4o", name: "GPT-4o", description: "Flagship multimodal model, excellent for complex reasoning and analysis", provider: .openAI),
        LLMModel(id: "gpt-4o-mini", name: "GPT-4o Mini", description: "Cost-effective with good performance for most tasks", provider: .openAI),
        LLMModel(id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", description: "Legacy model, quick responses and cost-effective for simple tasks", provider: .openAI)
    ]
    
    static let anthropicModels = [
        LLMModel(id: "claude-sonnet-4-20250514", name: "Claude Sonnet 4", description: "Latest flagship model with enhanced reasoning and coding capabilities", provider: .anthropic),
        LLMModel(id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet", description: "Excellent for creative writing and complex analysis", provider: .anthropic),
        LLMModel(id: "claude-3-5-haiku-20241022", name: "Claude 3.5 Haiku", description: "Fast and efficient, perfect for quick tasks", provider: .anthropic),
        LLMModel(id: "claude-3-opus-20240229", name: "Claude 3 Opus", description: "Legacy model for complex reasoning and research", provider: .anthropic)
    ]
    
    static let googleModels = [
        LLMModel(id: "gemini-2.5-pro-exp", name: "Gemini 2.5 Pro Experimental", description: "Latest experimental model with enhanced reasoning and multimodal capabilities", provider: .google),
        LLMModel(id: "gemini-2.0-flash-exp", name: "Gemini 2.0 Flash Experimental", description: "Next-generation flash model with improved performance and efficiency", provider: .google),
        LLMModel(id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", description: "Advanced reasoning with large context, great for research", provider: .google),
        LLMModel(id: "gemini-1.5-flash", name: "Gemini 1.5 Flash", description: "Fast and efficient, optimized for speed", provider: .google)
    ]
}

enum LLMProvider: String, CaseIterable, Identifiable, Hashable {
    case openAI = "openai"
    case anthropic = "anthropic"
    case google = "google"
    
    var id: String { return self.rawValue }
    
    var displayName: String {
        switch self {
        case .openAI: return "OpenAI"
        case .anthropic: return "Anthropic"
        case .google: return "Google"
        }
    }
    
    var models: [LLMModel] {
        switch self {
        case .openAI: return LLMModel.openAIModels
        case .anthropic: return LLMModel.anthropicModels
        case .google: return LLMModel.googleModels
        }
    }
    
    var apiKeyPlaceholder: String {
        switch self {
        case .openAI: return "sk-..."
        case .anthropic: return "sk-ant-..."
        case .google: return "AIza..."
        }
    }
    
    var apiKeyURL: String {
        switch self {
        case .openAI: return "https://platform.openai.com/api-keys"
        case .anthropic: return "https://console.anthropic.com/settings/keys"
        case .google: return "https://aistudio.google.com/app/apikey"
        }
    }
}

// MARK: - LLM Client Protocol
protocol LLMClient {
    var provider: LLMProvider { get }
    func processText(_ text: String, prompt: String, model: String) async throws -> String
    func validateAPIKey(_ apiKey: String) async throws -> Bool
}

// MARK: - OpenAI Client
class OpenAIClient: LLMClient {
    let provider: LLMProvider = .openAI
    private let apiKey: String
    
    init(apiKey: String) {
        self.apiKey = apiKey
    }
    
    func validateAPIKey(_ apiKey: String) async throws -> Bool {
        let url = URL(string: "https://api.openai.com/v1/models")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        
        PotterLogger.shared.info("validation", "🔍 OpenAI validation URL: \(url.absoluteString)")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        let httpResponse = response as? HTTPURLResponse
        let statusCode = httpResponse?.statusCode ?? 0
        
        PotterLogger.shared.info("validation", "📡 OpenAI response status: \(statusCode)")
        
        if statusCode != 200 {
            let errorBody = String(data: data, encoding: .utf8) ?? "No response body"
            PotterLogger.shared.error("validation", "❌ OpenAI validation failed - Response: \(errorBody)")
            throw createLLMError(for: statusCode, message: errorBody, provider: "OpenAI")
        }
        
        return true
    }
    
    func processText(_ text: String, prompt: String, model: String) async throws -> String {
        let url = URL(string: "https://api.openai.com/v1/chat/completions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = OpenAIRequest(
            model: model,
            messages: [
                OpenAIMessage(role: "system", content: prompt),
                OpenAIMessage(role: "user", content: text)
            ]
        )
        
        let jsonData = try JSONEncoder().encode(requestBody)
        request.httpBody = jsonData
        
        PotterLogger.shared.debug("llm_client", "🌐 Making OpenAI API request...")
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            PotterLogger.shared.error("llm_client", "🚫 OpenAI Network Error: \(error)")
            throw createResponseError(reason: "Network error: \(error.localizedDescription)")
        }
        
        // Debug logging for response investigation
        PotterLogger.shared.debug("llm_client", "🔍 OpenAI Raw Response Type: \(type(of: response))")
        
        guard let httpResponse = response as? HTTPURLResponse else {
            PotterLogger.shared.error("llm_client", "❌ OpenAI Invalid Response Type: \(type(of: response))")
            throw createResponseError(reason: "OpenAI API returned invalid HTTP response")
        }
        
        // Always log the status code for debugging
        PotterLogger.shared.debug("llm_client", "📡 OpenAI Response Status: \(httpResponse.statusCode)")
        
        guard httpResponse.statusCode == 200 else {
            throw handleLLMError(httpResponse: httpResponse, data: data, provider: "OpenAI")
        }
        
        let openAIResponse = try JSONDecoder().decode(OpenAIResponse.self, from: data)
        
        guard let firstChoice = openAIResponse.choices.first else {
            throw createResponseError(reason: "OpenAI API returned no response choices")
        }
        
        return firstChoice.message.content.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

// MARK: - Anthropic Client
class AnthropicClient: LLMClient {
    let provider: LLMProvider = .anthropic
    private let apiKey: String
    
    init(apiKey: String) {
        self.apiKey = apiKey
    }
    
    func validateAPIKey(_ apiKey: String) async throws -> Bool {
        let url = URL(string: "https://api.anthropic.com/v1/messages")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")
        
        PotterLogger.shared.info("validation", "🔍 Anthropic validation URL: \(url.absoluteString)")
        
        let testBody = AnthropicRequest(
            model: "claude-3-5-haiku-20241022",
            max_tokens: 1,
            messages: [AnthropicMessage(role: "user", content: "test")]
        )
        
        request.httpBody = try JSONEncoder().encode(testBody)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        let httpResponse = response as? HTTPURLResponse
        let statusCode = httpResponse?.statusCode ?? 0
        
        PotterLogger.shared.info("validation", "📡 Anthropic response status: \(statusCode)")
        
        if statusCode != 200 {
            let errorBody = String(data: data, encoding: .utf8) ?? "No response body"
            PotterLogger.shared.error("validation", "❌ Anthropic validation failed - Response: \(errorBody)")
            throw createLLMError(for: statusCode, message: errorBody, provider: "Anthropic")
        }
        
        return true
    }
    
    func processText(_ text: String, prompt: String, model: String) async throws -> String {
        let url = URL(string: "https://api.anthropic.com/v1/messages")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")
        
        let requestBody = AnthropicRequest(
            model: model,
            max_tokens: 2048,
            messages: [AnthropicMessage(role: "user", content: "\(prompt)\n\n\(text)")]
        )
        
        let jsonData = try JSONEncoder().encode(requestBody)
        request.httpBody = jsonData
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw createResponseError(reason: "Anthropic API returned invalid HTTP response")
        }
        
        guard httpResponse.statusCode == 200 else {
            throw handleLLMError(httpResponse: httpResponse, data: data, provider: "Anthropic")
        }
        
        let anthropicResponse = try JSONDecoder().decode(AnthropicResponse.self, from: data)
        
        guard let firstContent = anthropicResponse.content.first else {
            throw createResponseError(reason: "Anthropic API returned no response content")
        }
        
        return firstContent.text.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

// MARK: - Google Client
class GoogleClient: LLMClient {
    let provider: LLMProvider = .google
    private let apiKey: String
    
    init(apiKey: String) {
        self.apiKey = apiKey
    }
    
    func validateAPIKey(_ apiKey: String) async throws -> Bool {
        let baseURL = URL(string: "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent")!
        var request = URLRequest(url: baseURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "x-goog-api-key")
        
        PotterLogger.shared.info("validation", "🔍 Google validation URL: \(baseURL.absoluteString)")
        
        let testBody = GoogleRequest(
            contents: [GoogleContent(parts: [GooglePart(text: "test")])]
        )
        
        request.httpBody = try JSONEncoder().encode(testBody)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        let httpResponse = response as? HTTPURLResponse
        let statusCode = httpResponse?.statusCode ?? 0
        
        PotterLogger.shared.info("validation", "📡 Google response status: \(statusCode)")
        
        if statusCode != 200 {
            let errorBody = String(data: data, encoding: .utf8) ?? "No response body"
            PotterLogger.shared.error("validation", "❌ Google validation failed - Response: \(errorBody)")
            throw createLLMError(for: statusCode, message: errorBody, provider: "Google")
        }
        
        return true
    }
    
    func processText(_ text: String, prompt: String, model: String) async throws -> String {
        let modelName = model
        let baseURL = URL(string: "https://generativelanguage.googleapis.com/v1/models/\(modelName):generateContent")!
        var request = URLRequest(url: baseURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "x-goog-api-key")
        
        let requestBody = GoogleRequest(
            contents: [GoogleContent(parts: [GooglePart(text: "\(prompt)\n\n\(text)")])]
        )
        
        let jsonData = try JSONEncoder().encode(requestBody)
        request.httpBody = jsonData
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw createResponseError(reason: "Google API returned invalid HTTP response")
        }
        
        guard httpResponse.statusCode == 200 else {
            throw handleLLMError(httpResponse: httpResponse, data: data, provider: "Google")
        }
        
        let googleResponse = try JSONDecoder().decode(GoogleResponse.self, from: data)
        
        guard let firstCandidate = googleResponse.candidates.first,
              let content = firstCandidate.content,
              let firstPart = content.parts.first else {
            throw createResponseError(reason: "Google API returned no response candidates")
        }
        
        return firstPart.text.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

// MARK: - API Models

// OpenAI Models
struct OpenAIRequest: Codable {
    let model: String
    let messages: [OpenAIMessage]
}

struct OpenAIMessage: Codable {
    let role: String
    let content: String
}

struct OpenAIResponse: Codable {
    let choices: [OpenAIChoice]
}

struct OpenAIChoice: Codable {
    let message: OpenAIMessage
}

// Anthropic Models  
struct AnthropicRequest: Codable {
    let model: String
    let max_tokens: Int  // Required for Anthropic
    let messages: [AnthropicMessage]
}

struct AnthropicMessage: Codable {
    let role: String
    let content: String
}

struct AnthropicResponse: Codable {
    let content: [AnthropicContent]
}

struct AnthropicContent: Codable {
    let text: String
}

// Google Models
struct GoogleRequest: Codable {
    let contents: [GoogleContent]
}

struct GoogleContent: Codable {
    let parts: [GooglePart]
}

struct GooglePart: Codable {
    let text: String
}

struct GoogleResponse: Codable {
    let candidates: [GoogleCandidate]
}

struct GoogleCandidate: Codable {
    let content: GoogleContent?
}

// MARK: - Error Conversion Helpers

/// Unified error handling for all LLM providers
private func handleLLMError(httpResponse: HTTPURLResponse, data: Data, provider: String) -> PotterError {
    let statusCode = httpResponse.statusCode
    let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
    
    // Log the full API response for debugging
    PotterLogger.shared.error("llm_client", "❌ \(provider) API Error - Status: \(statusCode)")
    PotterLogger.shared.error("llm_client", "📄 Full API Response: \(errorMessage)")
    
    // Log headers that might contain rate limiting info
    if let rateLimitHeaders = httpResponse.allHeaderFields as? [String: String] {
        let relevantHeaders = rateLimitHeaders.filter { key, _ in
            key.lowercased().contains("rate") || 
            key.lowercased().contains("limit") || 
            key.lowercased().contains("retry") ||
            key.lowercased().contains("quota")
        }
        if !relevantHeaders.isEmpty {
            PotterLogger.shared.error("llm_client", "🔢 Rate Limit Headers: \(relevantHeaders)")
        }
    }
    
    return createLLMError(for: statusCode, message: errorMessage, provider: provider)
}

/// Helper function to convert common LLM API errors to PotterError
private func createLLMError(for statusCode: Int, message: String, provider: String) -> PotterError {
    switch statusCode {
    case 400:
        return .network(.invalidResponse(reason: "\(provider) API: \(message)"))
    case 401, 403:
        return .network(.unauthorized(provider: provider))
    case 429:
        // Extract retry-after time from error message if available
        let retryAfter = extractRetryAfterFromMessage(message)
        
        // Log additional rate limiting details for debugging
        PotterLogger.shared.error("llm_client", "🚫 Rate Limiting Details - Provider: \(provider)")
        PotterLogger.shared.error("llm_client", "⏳ Retry After: \(retryAfter?.description ?? "not specified")")
        PotterLogger.shared.error("llm_client", "💬 Rate Limit Message: \(message)")
        
        return .network(.rateLimited(retryAfter: retryAfter))
    case 500...599:
        return .network(.serverError(statusCode: statusCode, message: message))
    default:
        return .network(.requestFailed(underlying: "\(provider) API Error (\(statusCode)): \(message)"))
    }
}

/// Extract retry-after time from various API error message formats
private func extractRetryAfterFromMessage(_ message: String) -> TimeInterval? {
    // Common patterns in API rate limit messages
    let patterns = [
        #"retry.*?(\d+).*?second"#,
        #"wait.*?(\d+).*?second"#,
        #"Try again in (\d+) second"#,
        #"Rate limit.*?(\d+).*?second"#,
        #"Please try again in (\d+)"#
    ]
    
    for pattern in patterns {
        if let regex = try? NSRegularExpression(pattern: pattern, options: .caseInsensitive),
           let match = regex.firstMatch(in: message, options: [], range: NSRange(location: 0, length: message.count)),
           match.numberOfRanges > 1 {
            let range = match.range(at: 1)
            let numberString = (message as NSString).substring(with: range)
            if let seconds = Double(numberString) {
                return seconds
            }
        }
    }
    
    return nil
}

/// Helper function for invalid API key errors
private func createInvalidAPIKeyError(provider: String) -> PotterError {
    return .configuration(.invalidAPIKey(provider: provider))
}

/// Helper function for network response errors
private func createResponseError(reason: String) -> PotterError {
    return .network(.invalidResponse(reason: reason))
}
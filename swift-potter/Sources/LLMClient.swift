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
            throw LLMError.apiError(statusCode, errorBody)
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
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw LLMError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw LLMError.apiError(httpResponse.statusCode, errorMessage)
        }
        
        let openAIResponse = try JSONDecoder().decode(OpenAIResponse.self, from: data)
        
        guard let firstChoice = openAIResponse.choices.first else {
            throw LLMError.noResponse
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
            throw LLMError.apiError(statusCode, errorBody)
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
            throw LLMError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw LLMError.apiError(httpResponse.statusCode, errorMessage)
        }
        
        let anthropicResponse = try JSONDecoder().decode(AnthropicResponse.self, from: data)
        
        guard let firstContent = anthropicResponse.content.first else {
            throw LLMError.noResponse
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
        let url = URL(string: "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=\(apiKey)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        PotterLogger.shared.info("validation", "🔍 Google validation URL: \(url.absoluteString)")
        
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
            throw LLMError.apiError(statusCode, errorBody)
        }
        
        return true
    }
    
    func processText(_ text: String, prompt: String, model: String) async throws -> String {
        let modelName = model
        let url = URL(string: "https://generativelanguage.googleapis.com/v1/models/\(modelName):generateContent?key=\(apiKey)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = GoogleRequest(
            contents: [GoogleContent(parts: [GooglePart(text: "\(prompt)\n\n\(text)")])]
        )
        
        let jsonData = try JSONEncoder().encode(requestBody)
        request.httpBody = jsonData
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw LLMError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            let errorMessage = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw LLMError.apiError(httpResponse.statusCode, errorMessage)
        }
        
        let googleResponse = try JSONDecoder().decode(GoogleResponse.self, from: data)
        
        guard let firstCandidate = googleResponse.candidates.first,
              let content = firstCandidate.content,
              let firstPart = content.parts.first else {
            throw LLMError.noResponse
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

// MARK: - Errors
enum LLMError: Error, LocalizedError {
    case invalidResponse
    case apiError(Int, String)
    case noResponse
    case invalidAPIKey
    
    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Invalid response from API"
        case .apiError(let code, let message):
            return "API Error (\(code)): \(message)"
        case .noResponse:
            return "No response content received"
        case .invalidAPIKey:
            return "Invalid API key"
        }
    }
}
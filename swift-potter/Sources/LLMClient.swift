import Foundation

// MARK: - LLM Model Definitions
struct LLMModel: Identifiable, Hashable {
    let id: String
    let name: String
    let description: String
    let provider: LLMProvider
    
    static let openAIModels = [
        LLMModel(id: "gpt-4o-mini", name: "GPT-4o Mini", description: "Fast, intelligent, and cost-effective for most tasks", provider: .openAI),
        LLMModel(id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", description: "Reliable and cost-effective for most tasks", provider: .openAI),
    ]
    
    static let anthropicModels = [
        LLMModel(id: "claude-3-5-haiku-20241022", name: "Claude 3.5 Haiku", description: "Fast and efficient, perfect for quick tasks", provider: .anthropic),
        LLMModel(id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet", description: "Excellent for creative writing and complex analysis", provider: .anthropic)
    ]
    
    static let googleModels = [
        LLMModel(id: "gemini-1.5-flash", name: "Gemini 1.5 Flash", description: "Fast and efficient, optimized for speed", provider: .google),
        LLMModel(id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", description: "Advanced reasoning with large context", provider: .google)
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
            throw LLMHTTPClient.createLLMError(for: statusCode, message: errorBody, provider: "OpenAI")
        }

        return true
    }

    func processText(_ text: String, prompt: String, model: String) async throws -> String {
        let url = URL(string: "https://api.openai.com/v1/chat/completions")!
        let body = OpenAIRequest(
            model: model,
            messages: [
                OpenAIMessage(role: "system", content: prompt),
                OpenAIMessage(role: "user", content: text)
            ]
        )
        let headers = ["Authorization": "Bearer \(apiKey)"]

        PotterLogger.shared.debug("llm_client", "🌐 Making OpenAI API request...")
        let request: URLRequest
        do {
            request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: body)
        } catch {
            throw LLMHTTPClient.createResponseError(reason: "Failed to encode request: \(error.localizedDescription)")
        }

        let response: OpenAIResponse
        do {
            response = try await LLMHTTPClient.performRequest(request, responseType: OpenAIResponse.self, provider: "OpenAI")
        } catch {
            if let potterError = error as? PotterError {
                throw potterError
            }
            PotterLogger.shared.error("llm_client", "🚫 OpenAI Network Error: \(error)")
            throw LLMHTTPClient.createResponseError(reason: "Network error: \(error.localizedDescription)")
        }

        guard let firstChoice = response.choices.first else {
            throw LLMHTTPClient.createResponseError(reason: "OpenAI API returned no response choices")
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
        let headers = [
            "x-api-key": apiKey,
            "anthropic-version": "2023-06-01"
        ]
        let testBody = AnthropicRequest(
            model: LLMModel.anthropicModels.first!.id,
            max_tokens: 1,
            messages: [AnthropicMessage(role: "user", content: "test")]
        )

        PotterLogger.shared.info("validation", "🔍 Anthropic validation URL: \(url.absoluteString)")

        let request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: testBody)

        let (data, response) = try await URLSession.shared.data(for: request)
        let httpResponse = response as? HTTPURLResponse
        let statusCode = httpResponse?.statusCode ?? 0

        PotterLogger.shared.info("validation", "📡 Anthropic response status: \(statusCode)")

        if statusCode != 200 {
            let errorBody = String(data: data, encoding: .utf8) ?? "No response body"
            PotterLogger.shared.error("validation", "❌ Anthropic validation failed - Response: \(errorBody)")
            throw LLMHTTPClient.createLLMError(for: statusCode, message: errorBody, provider: "Anthropic")
        }

        return true
    }

    func processText(_ text: String, prompt: String, model: String) async throws -> String {
        let url = URL(string: "https://api.anthropic.com/v1/messages")!
        let body = AnthropicRequest(
            model: model,
            max_tokens: 2048,
            messages: [AnthropicMessage(role: "user", content: "\(prompt)\n\n\(text)")]
        )
        let headers = [
            "x-api-key": apiKey,
            "anthropic-version": "2023-06-01"
        ]

        let request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: body)
        let response: AnthropicResponse
        do {
            response = try await LLMHTTPClient.performRequest(request, responseType: AnthropicResponse.self, provider: "Anthropic")
        } catch {
            if let potterError = error as? PotterError {
                throw potterError
            }
            throw LLMHTTPClient.createResponseError(reason: "Network error: \(error.localizedDescription)")
        }

        guard let firstContent = response.content.first else {
            throw LLMHTTPClient.createResponseError(reason: "Anthropic API returned no response content")
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
        let modelId = LLMModel.googleModels.first!.id
        let url = URL(string: "https://generativelanguage.googleapis.com/v1/models/\(modelId):generateContent")!
        let headers = ["x-goog-api-key": apiKey]
        let testBody = GoogleRequest(
            contents: [GoogleContent(parts: [GooglePart(text: "test")])]
        )

        PotterLogger.shared.info("validation", "🔍 Google validation URL: \(url.absoluteString)")

        let request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: testBody)

        let (data, response) = try await URLSession.shared.data(for: request)
        let httpResponse = response as? HTTPURLResponse
        let statusCode = httpResponse?.statusCode ?? 0

        PotterLogger.shared.info("validation", "📡 Google response status: \(statusCode)")

        if statusCode != 200 {
            let errorBody = String(data: data, encoding: .utf8) ?? "No response body"
            PotterLogger.shared.error("validation", "❌ Google validation failed - Response: \(errorBody)")
            throw LLMHTTPClient.createLLMError(for: statusCode, message: errorBody, provider: "Google")
        }

        return true
    }

    func processText(_ text: String, prompt: String, model: String) async throws -> String {
        let url = URL(string: "https://generativelanguage.googleapis.com/v1/models/\(model):generateContent")!
        let body = GoogleRequest(
            contents: [GoogleContent(parts: [GooglePart(text: "\(prompt)\n\n\(text)")])]
        )
        let headers = ["x-goog-api-key": apiKey]

        let request = try LLMHTTPClient.makeJSONRequest(url: url, headers: headers, body: body)
        let googleResponse: GoogleResponse
        do {
            googleResponse = try await LLMHTTPClient.performRequest(request, responseType: GoogleResponse.self, provider: "Google")
        } catch {
            if let potterError = error as? PotterError {
                throw potterError
            }
            throw LLMHTTPClient.createResponseError(reason: "Network error: \(error.localizedDescription)")
        }

        guard let firstCandidate = googleResponse.candidates.first,
              let content = firstCandidate.content,
              let firstPart = content.parts.first else {
            throw LLMHTTPClient.createResponseError(reason: "Google API returned no response candidates")
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


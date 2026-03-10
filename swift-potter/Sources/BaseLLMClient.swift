import Foundation

/// Shared HTTP utilities for LLM API clients.
/// Reduces duplication across OpenAI, Anthropic, and Google clients.
enum LLMHTTPClient {
    /// Creates a JSON POST request with the given URL, headers, and encodable body.
    static func makeJSONRequest<T: Encodable>(
        url: URL,
        headers: [String: String],
        body: T
    ) throws -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (key, value) in headers {
            request.setValue(value, forHTTPHeaderField: key)
        }
        request.httpBody = try JSONEncoder().encode(body)
        return request
    }

    /// Performs an HTTP request and validates the response.
    static func performRequest<T: Decodable>(
        _ request: URLRequest,
        responseType: T.Type,
        provider: String
    ) async throws -> T {
        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw PotterError.network(.invalidResponse(reason: "\(provider) API returned invalid HTTP response"))
        }

        guard httpResponse.statusCode == 200 else {
            throw handleLLMError(httpResponse: httpResponse, data: data, provider: provider)
        }

        return try JSONDecoder().decode(T.self, from: data)
    }

    /// Unified error handling for all LLM providers
    static func handleLLMError(httpResponse: HTTPURLResponse, data: Data, provider: String) -> PotterError {
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
    static func createLLMError(for statusCode: Int, message: String, provider: String) -> PotterError {
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

            // Return the full error message for UI display
            return .network(.serverError(statusCode: statusCode, message: message))
        case 500...599:
            return .network(.serverError(statusCode: statusCode, message: message))
        default:
            return .network(.requestFailed(underlying: "\(provider) API Error (\(statusCode)): \(message)"))
        }
    }

    /// Extract retry-after time from various API error message formats
    static func extractRetryAfterFromMessage(_ message: String) -> TimeInterval? {
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
    static func createInvalidAPIKeyError(provider: String) -> PotterError {
        return .configuration(.invalidAPIKey(provider: provider))
    }

    /// Helper function for network response errors
    static func createResponseError(reason: String) -> PotterError {
        return .network(.invalidResponse(reason: reason))
    }
}

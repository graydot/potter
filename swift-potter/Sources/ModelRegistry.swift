import Foundation

/// Fetches, caches, and serves LLM models from provider APIs.
/// Falls back to static model lists when APIs are unreachable.
@MainActor
class ModelRegistry: ObservableObject {

    static let shared = ModelRegistry()

    @Published var models: [LLMProvider: [LLMModel]] = [:]
    @Published var lastFetched: [LLMProvider: Date] = [:]
    @Published var isFetching: Bool = false

    private let cacheTTL: TimeInterval
    private let cacheFileURL: URL
    private let session: URLSession

    /// Injectable for testing. Production uses shared singleton.
    init(cacheTTL: TimeInterval = 86400, cacheDirectory: URL? = nil, session: URLSession = .shared) {
        self.cacheTTL = cacheTTL
        self.session = session

        let dir = cacheDirectory ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!.appendingPathComponent("Potter")
        self.cacheFileURL = dir.appendingPathComponent("model_cache.json")

        loadCacheFromDisk()
    }

    // MARK: - Public API

    /// Get models for a provider. Returns cached/fetched models or static fallback.
    func getModels(for provider: LLMProvider) -> [LLMModel] {
        if let cached = models[provider], !cached.isEmpty {
            return cached
        }
        return Self.staticModels(for: provider)
    }

    /// Get models filtered by tier.
    func modelsForTier(_ tier: ModelTier, provider: LLMProvider) -> [LLMModel] {
        return getModels(for: provider).filter { $0.tier == tier }
    }

    /// Get the best (first) model for a tier.
    func bestModel(for tier: ModelTier, provider: LLMProvider) -> LLMModel? {
        return modelsForTier(tier, provider: provider).first
    }

    // MARK: - Per-Provider Tier Config

    /// Returns the user's preferred model for a tier on a given provider.
    /// Falls back to the best available model in that tier if no preference is saved.
    func preferredModel(for tier: ModelTier, provider: LLMProvider) -> LLMModel? {
        let config = getTierConfig(for: provider)
        if let modelID = config.modelID(for: tier),
           let model = getModels(for: provider).first(where: { $0.id == modelID }) {
            return model
        }
        return bestModel(for: tier, provider: provider)
    }

    /// Returns the saved tier config for a provider, or an empty config if none.
    func getTierConfig(for provider: LLMProvider) -> ProviderTierConfig {
        let key = UserDefaultsKeys.tierConfig(for: provider)
        guard let data = UserDefaults.standard.data(forKey: key),
              let config = try? JSONDecoder().decode(ProviderTierConfig.self, from: data) else {
            return ProviderTierConfig()
        }
        return config
    }

    /// Saves a tier config for a provider.
    func setTierConfig(_ config: ProviderTierConfig, for provider: LLMProvider) {
        let key = UserDefaultsKeys.tierConfig(for: provider)
        if let data = try? JSONEncoder().encode(config) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }

    /// Updates a single tier's model selection for a provider.
    func setPreferredModel(_ modelID: String?, tier: ModelTier, provider: LLMProvider) {
        let updated = getTierConfig(for: provider).setting(modelID, for: tier)
        setTierConfig(updated, for: provider)
    }

    /// Models grouped by tier for UI display.
    func modelsByTier(for provider: LLMProvider) -> [(tier: ModelTier, models: [LLMModel])] {
        let allModels = getModels(for: provider)
        return ModelTier.allCases.compactMap { tier in
            let tierModels = allModels.filter { $0.tier == tier }
            return tierModels.isEmpty ? nil : (tier: tier, models: tierModels)
        }
    }

    /// Whether cached models for this provider are stale.
    func isStale(for provider: LLMProvider) -> Bool {
        guard let fetched = lastFetched[provider] else { return true }
        return Date().timeIntervalSince(fetched) > cacheTTL
    }

    /// Refresh models for a single provider. Throws on failure.
    func refreshModels(for provider: LLMProvider, apiKey: String) async throws {
        isFetching = true
        defer { isFetching = false }

        let fetched = try await fetchModels(for: provider, apiKey: apiKey)
        models[provider] = fetched
        lastFetched[provider] = Date()
        saveCacheToDisk()
        PotterLogger.shared.info("model_registry", "Fetched \(fetched.count) models for \(provider.displayName)")
    }

    /// Refresh all providers that have API keys. Collects errors per provider.
    func refreshAllModels(apiKeys: [LLMProvider: String]) async throws {
        isFetching = true
        defer { isFetching = false }

        var errors: [LLMProvider: Error] = [:]

        await withTaskGroup(of: (LLMProvider, Result<[LLMModel], Error>).self) { group in
            for (provider, key) in apiKeys where !key.isEmpty {
                group.addTask { [weak self] in
                    guard let self else { return (provider, .failure(ModelRegistryError.fetchFailed(provider: provider))) }
                    do {
                        let fetched = try await self.fetchModels(for: provider, apiKey: key)
                        return (provider, .success(fetched))
                    } catch {
                        return (provider, .failure(error))
                    }
                }
            }

            for await (provider, result) in group {
                switch result {
                case .success(let fetched):
                    models[provider] = fetched
                    lastFetched[provider] = Date()
                case .failure(let error):
                    errors[provider] = error
                }
            }
        }
        saveCacheToDisk()

        if !errors.isEmpty {
            let descriptions = errors.map { "\($0.key.displayName): \($0.value.localizedDescription)" }
            throw ModelRegistryError.multipleFetchesFailed(descriptions: descriptions)
        }
    }

    // MARK: - Static Fallbacks

    static func staticModels(for provider: LLMProvider) -> [LLMModel] {
        switch provider {
        case .openAI: return LLMModel.openAIModels
        case .anthropic: return LLMModel.anthropicModels
        case .google: return LLMModel.googleModels
        }
    }

    // MARK: - API Fetching

    private func fetchModels(for provider: LLMProvider, apiKey: String) async throws -> [LLMModel] {
        switch provider {
        case .openAI:
            return try await fetchOpenAIModels(apiKey: apiKey)
        case .anthropic:
            return try await fetchAnthropicModels(apiKey: apiKey)
        case .google:
            return try await fetchGoogleModels(apiKey: apiKey)
        }
    }

    private func fetchOpenAIModels(apiKey: String) async throws -> [LLMModel] {
        let url = URL(string: "https://api.openai.com/v1/models")!
        var request = URLRequest(url: url)
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw ModelRegistryError.fetchFailed(provider: .openAI)
        }

        let decoded = try JSONDecoder().decode(OpenAIModelsResponse.self, from: data)

        // Filter to chat-capable models only
        let chatModels = decoded.data.filter { isChatModel($0.id) }

        return chatModels.map { raw in
            let tier = ModelTierClassifier.classify(raw.id, provider: .openAI)
            return LLMModel(
                id: raw.id,
                name: formatModelName(raw.id, provider: .openAI),
                description: descriptionForTier(tier),
                provider: .openAI,
                tier: tier
            )
        }.sorted { $0.tier.sortOrder < $1.tier.sortOrder }
    }

    private func fetchAnthropicModels(apiKey: String) async throws -> [LLMModel] {
        let url = URL(string: "https://api.anthropic.com/v1/models?limit=100")!
        var request = URLRequest(url: url)
        request.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        request.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw ModelRegistryError.fetchFailed(provider: .anthropic)
        }

        let decoded = try JSONDecoder().decode(AnthropicModelsResponse.self, from: data)

        return decoded.data.map { raw in
            let tier = ModelTierClassifier.classify(raw.id, provider: .anthropic)
            return LLMModel(
                id: raw.id,
                name: raw.display_name,
                description: descriptionForTier(tier),
                provider: .anthropic,
                tier: tier
            )
        }.sorted { $0.tier.sortOrder < $1.tier.sortOrder }
    }

    private func fetchGoogleModels(apiKey: String) async throws -> [LLMModel] {
        let url = URL(string: "https://generativelanguage.googleapis.com/v1/models?key=\(apiKey)")!
        let request = URLRequest(url: url)

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw ModelRegistryError.fetchFailed(provider: .google)
        }

        let decoded = try JSONDecoder().decode(GoogleModelsResponse.self, from: data)

        // Filter to models that support generateContent
        let chatModels = decoded.models.filter { model in
            model.supportedGenerationMethods?.contains("generateContent") ?? false
        }

        return chatModels.map { raw in
            // Google returns "models/gemini-1.5-flash" — strip prefix
            let id = raw.name.hasPrefix("models/") ? String(raw.name.dropFirst(7)) : raw.name
            let tier = ModelTierClassifier.classify(id, provider: .google)
            return LLMModel(
                id: id,
                name: raw.displayName ?? formatModelName(id, provider: .google),
                description: raw.description ?? descriptionForTier(tier),
                provider: .google,
                tier: tier
            )
        }.sorted { $0.tier.sortOrder < $1.tier.sortOrder }
    }

    // MARK: - Model Filtering

    /// Heuristic: is this OpenAI model a chat/completion model?
    private func isChatModel(_ id: String) -> Bool {
        let chatPrefixes = ["gpt-", "o1", "o3", "o4", "chatgpt"]
        let excluded = ["instruct", "realtime", "audio", "search", "tts", "whisper",
                        "dall-e", "embedding", "moderation", "babbage", "davinci",
                        "text-", "code-", "ft:"]

        let lower = id.lowercased()
        let matchesChat = chatPrefixes.contains { lower.hasPrefix($0) }
        let isExcluded = excluded.contains { lower.contains($0) }

        return matchesChat && !isExcluded
    }

    // MARK: - Name Formatting

    private func formatModelName(_ id: String, provider: LLMProvider) -> String {
        // Convert "gpt-4o-mini-2024-07-18" → "GPT-4o Mini"
        // Convert "gemini-2.0-flash" → "Gemini 2.0 Flash"
        let parts = id.split(separator: "-").map(String.init)

        // Strip date suffixes (YYYY-MM-DD or YYYYMMDD)
        let filtered = parts.filter { part in
            if part.count == 8, Int(part) != nil { return false }  // YYYYMMDD
            if part.count == 4, Int(part) != nil, parts.count > 3 { return false }  // Year in date
            if part.count == 2, Int(part) != nil, parts.count > 4 { return false }  // Month/Day
            return true
        }

        return filtered.map { $0.capitalized }.joined(separator: " ")
    }

    private func descriptionForTier(_ tier: ModelTier) -> String {
        return tier.description
    }

    // MARK: - Disk Cache

    private func loadCacheFromDisk() {
        guard FileManager.default.fileExists(atPath: cacheFileURL.path) else { return }
        do {
            let data = try Data(contentsOf: cacheFileURL)
            let cache = try JSONDecoder().decode(ModelCache.self, from: data)
            self.models = cache.models
            self.lastFetched = cache.lastFetched
            PotterLogger.shared.info("model_registry", "Loaded model cache from disk")
        } catch {
            PotterLogger.shared.error("model_registry", "Failed to load model cache: \(error.localizedDescription)")
        }
    }

    private func saveCacheToDisk() {
        do {
            let dir = cacheFileURL.deletingLastPathComponent()
            try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            let cache = ModelCache(models: models, lastFetched: lastFetched)
            let data = try JSONEncoder().encode(cache)
            try data.write(to: cacheFileURL, options: .atomic)
        } catch {
            PotterLogger.shared.error("model_registry", "Failed to save model cache: \(error.localizedDescription)")
        }
    }

    /// Clear all cached models (for testing or reset).
    func clearCache() {
        models = [:]
        lastFetched = [:]
        try? FileManager.default.removeItem(at: cacheFileURL)
    }
}

// MARK: - ModelTier Sort Order

extension ModelTier {
    var sortOrder: Int {
        switch self {
        case .fast: return 0
        case .standard: return 1
        case .thinking: return 2
        }
    }
}

// MARK: - Cache Model

private struct ModelCache: Codable {
    let models: [LLMProvider: [LLMModel]]
    let lastFetched: [LLMProvider: Date]
}

// MARK: - API Response Types

struct OpenAIModelsResponse: Codable {
    let data: [OpenAIModelEntry]
}

struct OpenAIModelEntry: Codable {
    let id: String
}

struct AnthropicModelsResponse: Codable {
    let data: [AnthropicModelEntry]
}

struct AnthropicModelEntry: Codable {
    let id: String
    let display_name: String
}

struct GoogleModelsResponse: Codable {
    let models: [GoogleModelEntry]
}

struct GoogleModelEntry: Codable {
    let name: String
    let displayName: String?
    let description: String?
    let supportedGenerationMethods: [String]?
}

// MARK: - Errors

enum ModelRegistryError: Error, LocalizedError {
    case fetchFailed(provider: LLMProvider)
    case multipleFetchesFailed(descriptions: [String])

    var errorDescription: String? {
        switch self {
        case .fetchFailed(let provider):
            return "Failed to fetch models from \(provider.displayName)"
        case .multipleFetchesFailed(let descriptions):
            return "Failed to fetch models: \(descriptions.joined(separator: "; "))"
        }
    }
}

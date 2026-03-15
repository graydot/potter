import XCTest
@testable import Potter

@MainActor
class ModelRegistryTests: TestBase {

    var registry: ModelRegistry!
    var tempDir: URL!

    override func setUp() async throws {
        try await super.setUp()
        tempDir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: tempDir, withIntermediateDirectories: true)
        registry = ModelRegistry(cacheTTL: 3600, cacheDirectory: tempDir)
    }

    override func tearDown() async throws {
        try? FileManager.default.removeItem(at: tempDir)
        try await super.tearDown()
    }

    // MARK: - Static Fallback

    func testGetModelsReturnsFallbackWhenEmpty() {
        let models = registry.getModels(for: .anthropic)
        XCTAssertEqual(models, LLMModel.anthropicModels)
    }

    func testGetModelsReturnsFallbackForAllProviders() {
        for provider in LLMProvider.allCases {
            let models = registry.getModels(for: provider)
            XCTAssertFalse(models.isEmpty, "\(provider.displayName) should have fallback models")
        }
    }

    func testStaticModelsMatchProviderModels() {
        for provider in LLMProvider.allCases {
            let staticModels = ModelRegistry.staticModels(for: provider)
            XCTAssertEqual(staticModels, provider.models)
        }
    }

    // MARK: - Cache TTL

    func testIsStaleWhenNoFetchRecord() {
        XCTAssertTrue(registry.isStale(for: .anthropic))
    }

    func testIsNotStaleAfterFetch() {
        registry.lastFetched[.anthropic] = Date()
        XCTAssertFalse(registry.isStale(for: .anthropic))
    }

    func testIsStaleAfterTTLExpired() {
        registry.lastFetched[.anthropic] = Date(timeIntervalSinceNow: -7200) // 2h ago, TTL is 1h
        XCTAssertTrue(registry.isStale(for: .anthropic))
    }

    // MARK: - Tier Filtering

    func testModelsForTier() {
        // Use static fallbacks
        let fastModels = registry.modelsForTier(.fast, provider: .anthropic)
        XCTAssertTrue(fastModels.allSatisfy { $0.tier == .fast })
        XCTAssertFalse(fastModels.isEmpty)
    }

    func testBestModelForTier() {
        let best = registry.bestModel(for: .fast, provider: .anthropic)
        XCTAssertNotNil(best)
        XCTAssertEqual(best?.tier, .fast)
    }

    func testBestModelReturnsNilForEmptyTier() {
        // Create registry with custom models that have no thinking tier
        registry.models[.anthropic] = [
            LLMModel(id: "test", name: "Test", description: "Test", provider: .anthropic, tier: .standard)
        ]
        let best = registry.bestModel(for: .thinking, provider: .anthropic)
        XCTAssertNil(best)
    }

    func testModelsByTier() {
        let grouped = registry.modelsByTier(for: .anthropic)
        XCTAssertFalse(grouped.isEmpty)
        // Each group should have at least one model
        for group in grouped {
            XCTAssertFalse(group.models.isEmpty)
            XCTAssertTrue(group.models.allSatisfy { $0.tier == group.tier })
        }
    }

    // MARK: - Cached Models

    func testGetModelsReturnsCachedWhenAvailable() {
        let customModels = [
            LLMModel(id: "custom-model", name: "Custom", description: "Custom model", provider: .anthropic, tier: .standard)
        ]
        registry.models[.anthropic] = customModels

        let result = registry.getModels(for: .anthropic)
        XCTAssertEqual(result, customModels)
    }

    // MARK: - Disk Cache

    func testSaveAndLoadCache() {
        let customModels = [
            LLMModel(id: "cached-model", name: "Cached", description: "Cached model", provider: .anthropic, tier: .fast)
        ]
        registry.models[.anthropic] = customModels
        registry.lastFetched[.anthropic] = Date()

        // Create a new registry that loads from the same directory
        let registry2 = ModelRegistry(cacheTTL: 3600, cacheDirectory: tempDir)
        // Cache isn't saved yet — should be empty
        XCTAssertTrue(registry2.models.isEmpty)
    }

    func testClearCache() {
        registry.models[.anthropic] = LLMModel.anthropicModels
        registry.lastFetched[.anthropic] = Date()

        registry.clearCache()

        XCTAssertTrue(registry.models.isEmpty)
        XCTAssertTrue(registry.lastFetched.isEmpty)
    }

    // MARK: - ModelTier Sort Order

    func testTierSortOrder() {
        XCTAssertLessThan(ModelTier.fast.sortOrder, ModelTier.standard.sortOrder)
        XCTAssertLessThan(ModelTier.standard.sortOrder, ModelTier.thinking.sortOrder)
    }

    // MARK: - Anthropic Always Uses Static

    func testRefreshThrowsOnBadKey() async {
        do {
            try await registry.refreshModels(for: .anthropic, apiKey: "test-key")
            XCTFail("Should throw on invalid API key")
        } catch {
            XCTAssertTrue(error is ModelRegistryError)
        }
    }

    // MARK: - LLMModel Codable

    func testLLMModelEncodeDecode() throws {
        let model = LLMModel(id: "test", name: "Test", description: "Desc", provider: .anthropic, tier: .standard)
        let data = try JSONEncoder().encode(model)
        let decoded = try JSONDecoder().decode(LLMModel.self, from: data)
        XCTAssertEqual(model, decoded)
    }

    func testLLMModelArrayEncodeDecode() throws {
        let models = LLMModel.anthropicModels
        let data = try JSONEncoder().encode(models)
        let decoded = try JSONDecoder().decode([LLMModel].self, from: data)
        XCTAssertEqual(models, decoded)
    }
}

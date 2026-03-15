import XCTest
@testable import Potter

class ModelTierClassifierTests: TestBase {

    // MARK: - Fast Tier

    func testFlashModelsClassifyAsFast() {
        XCTAssertEqual(ModelTierClassifier.classify("gemini-2.0-flash", provider: .google), .fast)
        XCTAssertEqual(ModelTierClassifier.classify("gemini-1.5-flash", provider: .google), .fast)
    }

    func testHaikuModelsClassifyAsFast() {
        XCTAssertEqual(ModelTierClassifier.classify("claude-3-5-haiku-20241022", provider: .anthropic), .fast)
        XCTAssertEqual(ModelTierClassifier.classify("claude-haiku-4-20250514", provider: .anthropic), .fast)
    }

    // MARK: - Thinking Tier

    func testThinkingModelsClassifyAsThinking() {
        XCTAssertEqual(ModelTierClassifier.classify("gemini-2.5-flash-thinking", provider: .google), .thinking)
    }

    func testReasonModelClassifiesAsThinking() {
        XCTAssertEqual(ModelTierClassifier.classify("some-reason-model", provider: .anthropic), .thinking)
    }

    // MARK: - Standard Tier (default)

    func testClaudeSonnetClassifiesAsStandard() {
        let result = ModelTierClassifier.classify("claude-sonnet-4-20250514", provider: .anthropic)
        XCTAssertEqual(result, .standard, "claude-sonnet-4 classified as \(result) instead of standard")
    }

    func testGeminiProClassifiesAsStandard() {
        let result = ModelTierClassifier.classify("gemini-2.5-pro", provider: .google)
        XCTAssertEqual(result, .standard, "gemini-2.5-pro classified as \(result) instead of standard")
    }

    func testUnknownModelDefaultsToStandard() {
        XCTAssertEqual(ModelTierClassifier.classify("some-new-unknown-model", provider: .anthropic), .standard)
    }

    // MARK: - Edge Cases

    func testCaseInsensitivity() {
        XCTAssertEqual(ModelTierClassifier.classify("Gemini-Flash", provider: .google), .fast)
    }

    func testOpusClassifiesAsStandard() {
        // Opus doesn't match any fast or thinking patterns — classifier defaults to standard
        // (Static list can override to .thinking for known models)
        XCTAssertEqual(ModelTierClassifier.classify("claude-opus-4-20250514", provider: .anthropic), .standard)
    }

    // MARK: - ModelTier Properties

    func testModelTierDisplayNames() {
        XCTAssertEqual(ModelTier.fast.displayName, "Fast")
        XCTAssertEqual(ModelTier.standard.displayName, "Standard")
        XCTAssertEqual(ModelTier.thinking.displayName, "Thinking")
    }

    func testModelTierDescriptions() {
        XCTAssertFalse(ModelTier.fast.description.isEmpty)
        XCTAssertFalse(ModelTier.standard.description.isEmpty)
        XCTAssertFalse(ModelTier.thinking.description.isEmpty)
    }

    func testModelTierCaseIterable() {
        XCTAssertEqual(ModelTier.allCases.count, 3)
    }

    func testModelTierCodable() throws {
        let encoder = JSONEncoder()
        let decoder = JSONDecoder()

        for tier in ModelTier.allCases {
            let data = try encoder.encode(tier)
            let decoded = try decoder.decode(ModelTier.self, from: data)
            XCTAssertEqual(tier, decoded)
        }
    }

    // MARK: - Static Model Tiers

    func testAllStaticModelsHaveTiers() {
        let allModels = LLMModel.anthropicModels + LLMModel.googleModels
        for model in allModels {
            XCTAssertNotNil(model.tier, "Model \(model.id) should have a tier")
        }
    }

    func testEachProviderHasAllTiers() {
        for provider in LLMProvider.allCases {
            let models = provider.models
            let tiers = Set(models.map(\.tier))
            XCTAssertTrue(tiers.contains(.fast), "\(provider.displayName) should have a fast model")
            XCTAssertTrue(tiers.contains(.standard), "\(provider.displayName) should have a standard model")
        }
    }
}

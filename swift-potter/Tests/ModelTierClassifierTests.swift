import XCTest
@testable import Potter

class ModelTierClassifierTests: TestBase {

    // MARK: - Fast Tier

    func testMiniModelsClassifyAsFast() {
        XCTAssertEqual(ModelTierClassifier.classify("gpt-4o-mini", provider: .openAI), .fast)
        XCTAssertEqual(ModelTierClassifier.classify("o4-mini", provider: .openAI), .fast)
    }

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
        XCTAssertEqual(ModelTierClassifier.classify("o1-preview", provider: .openAI), .thinking)
        XCTAssertEqual(ModelTierClassifier.classify("o3-pro", provider: .openAI), .thinking)
    }

    func testO4ModelClassifiesAsThinking() {
        // Plain o4 (not o4-mini which is fast)
        XCTAssertEqual(ModelTierClassifier.classify("o4-preview", provider: .openAI), .thinking)
    }

    func testReasonModelClassifiesAsThinking() {
        XCTAssertEqual(ModelTierClassifier.classify("some-reason-model", provider: .openAI), .thinking)
    }

    // MARK: - Standard Tier (default)

    func testGpt4oClassifiesAsStandard() {
        let result = ModelTierClassifier.classify("gpt-4o", provider: .openAI)
        XCTAssertEqual(result, .standard, "gpt-4o classified as \(result) instead of standard")
    }

    func testClaudeSonnetClassifiesAsStandard() {
        let result = ModelTierClassifier.classify("claude-sonnet-4-20250514", provider: .anthropic)
        XCTAssertEqual(result, .standard, "claude-sonnet-4 classified as \(result) instead of standard")
    }

    func testGeminiProClassifiesAsStandard() {
        let result = ModelTierClassifier.classify("gemini-2.5-pro", provider: .google)
        XCTAssertEqual(result, .standard, "gemini-2.5-pro classified as \(result) instead of standard")
    }

    func testUnknownModelDefaultsToStandard() {
        XCTAssertEqual(ModelTierClassifier.classify("some-new-unknown-model", provider: .openAI), .standard)
    }

    // MARK: - Edge Cases

    func testMiniTakesPriorityOverThinking() {
        // "o4-mini" has both "o4" (thinking) and "mini" (fast) — fast wins
        XCTAssertEqual(ModelTierClassifier.classify("o4-mini", provider: .openAI), .fast)
    }

    func testCaseInsensitivity() {
        XCTAssertEqual(ModelTierClassifier.classify("GPT-4O-MINI", provider: .openAI), .fast)
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
        let allModels = LLMModel.openAIModels + LLMModel.anthropicModels + LLMModel.googleModels
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

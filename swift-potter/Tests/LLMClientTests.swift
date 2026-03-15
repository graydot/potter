import XCTest
import Foundation
@testable import Potter

class LLMClientTests: TestBase {

    func testLLMModelStructure() {
        let model = LLMModel(
            id: "test-model",
            name: "Test Model",
            description: "A test model",
            provider: .anthropic,
            tier: .standard
        )

        XCTAssertEqual(model.id, "test-model")
        XCTAssertEqual(model.name, "Test Model")
        XCTAssertEqual(model.description, "A test model")
        XCTAssertEqual(model.provider, .anthropic)
        XCTAssertEqual(model.tier, .standard)
    }

    func testLLMProviderProperties() {
        XCTAssertEqual(LLMProvider.anthropic.displayName, "Anthropic")
        XCTAssertEqual(LLMProvider.google.displayName, "Google")

        XCTAssertEqual(LLMProvider.anthropic.rawValue, "anthropic")
        XCTAssertEqual(LLMProvider.google.rawValue, "google")

        XCTAssertEqual(LLMProvider.anthropic.id, "anthropic")
        XCTAssertEqual(LLMProvider.google.id, "google")
    }

    func testLLMProviderModels() {
        let anthropicModels = LLMProvider.anthropic.models
        let googleModels = LLMProvider.google.models

        XCTAssertGreaterThan(anthropicModels.count, 0)
        XCTAssertGreaterThan(googleModels.count, 0)

        // Check that all models have the correct provider
        XCTAssertTrue(anthropicModels.allSatisfy { $0.provider == .anthropic })
        XCTAssertTrue(googleModels.allSatisfy { $0.provider == .google })
    }


    func testAnthropicModels() {
        let models = LLMModel.anthropicModels

        XCTAssertTrue(models.contains { $0.id == "claude-sonnet-4-20250514" })
        XCTAssertTrue(models.contains { $0.id == "claude-3-5-haiku-20241022" })
        XCTAssertTrue(models.contains { $0.id == "claude-opus-4-20250514" })
        XCTAssertEqual(models.count, 3, "Should have 3 Anthropic models (one per tier)")

        let sonnet = models.first { $0.id == "claude-sonnet-4-20250514" }!
        XCTAssertEqual(sonnet.name, "Claude Sonnet 4")
        XCTAssertEqual(sonnet.provider, .anthropic)
        XCTAssertEqual(sonnet.tier, .standard)
        XCTAssertFalse(sonnet.description.isEmpty)
    }


    func testPotterErrorTypes() {
        let errors: [PotterError] = [
            .configuration(.invalidAPIKey(provider: "Test")),
            .network(.invalidResponse(reason: "No response")),
            .network(.invalidResponse(reason: "Invalid response")),
            .network(.serverError(statusCode: 400, message: "Bad Request"))
        ]

        for error in errors {
            XCTAssertTrue(error is PotterError)
        }

        // Test API error details
        if case .network(.serverError(let statusCode, let message)) = PotterError.network(.serverError(statusCode: 404, message: "Not Found")) {
            XCTAssertEqual(statusCode, 404)
            XCTAssertEqual(message, "Not Found")
        } else {
            XCTFail("API error case should match")
        }
    }

    func testAnthropicRequestStructure() {
        let message = AnthropicMessage(role: "user", content: "Hello")
        let request = AnthropicRequest(
            model: "claude-sonnet-4-20250514",
            max_tokens: 1000,
            messages: [message]
        )

        XCTAssertEqual(request.model, "claude-sonnet-4-20250514")
        XCTAssertEqual(request.max_tokens, 1000)
        XCTAssertEqual(request.messages.count, 1)
        XCTAssertEqual(request.messages[0].role, "user")
        XCTAssertEqual(request.messages[0].content, "Hello")
    }

    func testGoogleRequestStructure() {
        let part = GooglePart(text: "Hello")
        let content = GoogleContent(parts: [part])
        let request = GoogleRequest(contents: [content])

        XCTAssertEqual(request.contents.count, 1)
        XCTAssertEqual(request.contents[0].parts.count, 1)
        XCTAssertEqual(request.contents[0].parts[0].text, "Hello")
    }

    func testAnthropicClientInitialization() {
        let client = AnthropicClient(apiKey: "test-key")
        XCTAssertEqual(client.provider, .anthropic)
    }

    func testGoogleClientInitialization() {
        let client = GoogleClient(apiKey: "test-key")
        XCTAssertEqual(client.provider, .google)
    }

    func testLLMModelEquatable() {
        let model1 = LLMModel(id: "test", name: "Test", description: "Test model", provider: .anthropic, tier: .standard)
        let model2 = LLMModel(id: "test", name: "Test", description: "Test model", provider: .anthropic, tier: .standard)
        let model3 = LLMModel(id: "different", name: "Test", description: "Test model", provider: .anthropic, tier: .standard)

        XCTAssertEqual(model1, model2)
        XCTAssertNotEqual(model1, model3)
    }

    func testLLMModelHashable() {
        let model1 = LLMModel(id: "test", name: "Test", description: "Test model", provider: .anthropic, tier: .standard)
        let model2 = LLMModel(id: "test", name: "Test", description: "Test model", provider: .anthropic, tier: .standard)

        let set: Set<LLMModel> = [model1, model2]
        XCTAssertEqual(set.count, 1) // Should be deduplicated
    }

    func testProviderCaseIterable() {
        let allProviders = LLMProvider.allCases
        XCTAssertEqual(allProviders.count, 2)
        XCTAssertTrue(allProviders.contains(.anthropic))
        XCTAssertTrue(allProviders.contains(.google))
    }
}

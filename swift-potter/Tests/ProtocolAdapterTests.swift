import XCTest
@testable import Potter

class ProtocolAdapterTests: TestBase {
    // Test that PromptService can be used as PromptProviding
    func testPromptServiceConformsToPromptProviding() {
        let provider: any PromptProviding = PromptService.shared
        XCTAssertNotNil(provider)
    }

    func testPromptServiceProvidesCurrentPromptText() {
        let provider: any PromptProviding = PromptService.shared
        // getCurrentPromptText should be callable through the protocol
        let _ = provider.getCurrentPromptText()
    }

    func testPromptServiceProvidesCurrentPromptName() {
        let provider: any PromptProviding = PromptService.shared
        let name = provider.currentPromptName
        // Just verify it's accessible, don't assert specific value
        _ = name
    }

    // Test that LLMManager can be used as LLMProcessing
    // LLMManager is @MainActor so we need @MainActor here
    @MainActor
    func testLLMManagerConformsToLLMProcessing() {
        let processor: any LLMProcessing = LLMManager()
        XCTAssertNotNil(processor)
    }

    // Test that TextProcessor can be wired with real implementations
    @MainActor
    func testTextProcessorWithRealImplementations() {
        let tp = TextProcessor(
            promptProvider: PromptService.shared,
            llmProcessor: LLMManager()
        )
        XCTAssertNotNil(tp)
    }

    // Test polymorphism - same TextProcessor works with mocks and real impls
    @MainActor
    func testTextProcessorPolymorphism() {
        // With mocks
        class QuickMockPrompt: PromptProviding {
            func getCurrentPromptText() -> String? { return "test" }
            var currentPromptName: String { return "test" }
        }
        class QuickMockLLM: LLMProcessing {
            func processText(_ text: String, prompt: String) async throws -> String { return "done" }
        }

        let mockTP = TextProcessor(promptProvider: QuickMockPrompt(), llmProcessor: QuickMockLLM())
        XCTAssertNotNil(mockTP)

        // With real implementations
        let realTP = TextProcessor(promptProvider: PromptService.shared, llmProcessor: LLMManager())
        XCTAssertNotNil(realTP)
    }
}

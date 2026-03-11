import XCTest
import Foundation
@testable import Potter

// MARK: - Mocks

class MockPromptProvider: PromptProviding {
    var promptText: String? = "Make this formal"
    var promptName: String = "Formal"

    func getCurrentPromptText() -> String? {
        return promptText
    }

    func getCurrentPrompt() -> PromptItem? {
        return nil
    }

    var currentPromptName: String {
        return promptName
    }
}

class MockLLMProcessor: LLMProcessing {
    var shouldFail = false
    var failureError: Error?
    var lastReceivedText: String?
    var lastReceivedPrompt: String?
    var responseText = "processed result"

    func processText(_ text: String, prompt: String) async throws -> String {
        lastReceivedText = text
        lastReceivedPrompt = prompt
        if shouldFail {
            throw failureError ?? NSError(domain: "MockLLM", code: 1, userInfo: [NSLocalizedDescriptionKey: "Mock LLM failure"])
        }
        return responseText
    }

    func streamText(_ text: String, prompt: String,
                    onToken: @Sendable @escaping (String) -> Void) async throws -> String {
        lastReceivedText = text
        lastReceivedPrompt = prompt
        if shouldFail {
            throw failureError ?? NSError(domain: "MockLLM", code: 1, userInfo: [NSLocalizedDescriptionKey: "Mock LLM failure"])
        }
        // Simulate streaming: emit response word by word
        for word in responseText.split(separator: " ") {
            onToken(String(word) + " ")
        }
        return responseText
    }
}

// MARK: - Tests

class TextProcessorTests: TestBase {
    var mockPromptProvider: MockPromptProvider!
    var mockLLMProcessor: MockLLMProcessor!
    var textProcessor: TextProcessor!

    override func setUp() {
        super.setUp()
        mockPromptProvider = MockPromptProvider()
        mockLLMProcessor = MockLLMProcessor()
        textProcessor = TextProcessor(
            promptProvider: mockPromptProvider,
            llmProcessor: mockLLMProcessor
        )
    }

    override func tearDown() {
        textProcessor = nil
        mockPromptProvider = nil
        mockLLMProcessor = nil
        super.tearDown()
    }

    // MARK: - Tests

    func testProcessTextWithPrompt() async throws {
        // Given
        mockLLMProcessor.responseText = "This is a formal version."

        // When
        let result = try await textProcessor.processText("hey whats up", withPrompt: "Make this formal")

        // Then
        XCTAssertEqual(result, "This is a formal version.")
    }

    func testProcessTextUsesCurrentPrompt() async throws {
        // Given
        mockPromptProvider.promptText = "Summarize this text"
        mockLLMProcessor.responseText = "A summary."

        // When
        let result = try await textProcessor.processText("Long text that needs summarizing...")

        // Then
        XCTAssertEqual(result, "A summary.")
        XCTAssertEqual(mockLLMProcessor.lastReceivedPrompt, "Summarize this text")
    }

    func testProcessTextThrowsWhenLLMFails() async {
        // Given
        mockLLMProcessor.shouldFail = true
        let expectedError = NSError(domain: "LLMError", code: 42, userInfo: [NSLocalizedDescriptionKey: "Rate limited"])
        mockLLMProcessor.failureError = expectedError

        // When / Then
        do {
            _ = try await textProcessor.processText("some text", withPrompt: "Fix grammar")
            XCTFail("Expected error to be thrown")
        } catch {
            let nsError = error as NSError
            XCTAssertEqual(nsError.domain, "LLMError")
            XCTAssertEqual(nsError.code, 42)
        }
    }

    func testProcessTextThrowsWhenNoPromptAvailable() async {
        // Given
        mockPromptProvider.promptText = nil

        // When / Then
        do {
            _ = try await textProcessor.processText("some text")
            XCTFail("Expected error to be thrown when no prompt is available")
        } catch {
            // Error should indicate no prompt is available
            XCTAssertTrue(error.localizedDescription.lowercased().contains("prompt"),
                          "Error should mention prompt, got: \(error.localizedDescription)")
        }
    }

    func testProcessTextPassesCorrectInputToLLM() async throws {
        // Given
        let inputText = "Please check this text for errors"
        let prompt = "Fix all grammar mistakes"
        mockLLMProcessor.responseText = "Corrected text"

        // When
        _ = try await textProcessor.processText(inputText, withPrompt: prompt)

        // Then
        XCTAssertEqual(mockLLMProcessor.lastReceivedText, inputText)
        XCTAssertEqual(mockLLMProcessor.lastReceivedPrompt, prompt)
    }

    func testProcessTextTrimsResult() async throws {
        // Given
        mockLLMProcessor.responseText = "  result with whitespace  \n\n"

        // When
        let result = try await textProcessor.processText("input", withPrompt: "Clean up")

        // Then
        XCTAssertEqual(result, "result with whitespace")
    }
}

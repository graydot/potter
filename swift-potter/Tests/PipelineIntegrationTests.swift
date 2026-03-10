import XCTest
@testable import Potter

// MARK: - Test Doubles

class StubPromptProvider: PromptProviding {
    var promptText: String?
    var currentPromptName: String = "Test Prompt"
    func getCurrentPromptText() -> String? { return promptText }
}

class StubLLMProcessor: LLMProcessing {
    var responses: [String] = []
    private var callIndex = 0
    var receivedInputs: [(text: String, prompt: String)] = []
    var errorToThrow: Error?

    func processText(_ text: String, prompt: String) async throws -> String {
        receivedInputs.append((text: text, prompt: prompt))
        if let error = errorToThrow { throw error }
        let response = callIndex < responses.count ? responses[callIndex] : "default response"
        callIndex += 1
        return response
    }
}

class SpyIconDelegate: IconStateDelegate {
    var states: [String] = []
    func setProcessingState() { states.append("processing") }
    func setSuccessState() { states.append("success") }
    func setNormalState() { states.append("normal") }
    func setErrorState(message: String) { states.append("error:\(message)") }
}

// MARK: - Pipeline Integration Tests

class PipelineIntegrationTests: TestBase {
    var stubPrompt: StubPromptProvider!
    var stubLLM: StubLLMProcessor!
    var processor: TextProcessor!

    override func setUp() {
        super.setUp()
        stubPrompt = StubPromptProvider()
        stubLLM = StubLLMProcessor()
        processor = TextProcessor(promptProvider: stubPrompt, llmProcessor: stubLLM)
    }

    override func tearDown() {
        processor = nil
        stubLLM = nil
        stubPrompt = nil
        super.tearDown()
    }

    // MARK: - 1. Happy Path

    func testFullPipelineHappyPath() async throws {
        // Given
        stubPrompt.promptText = "Make this formal"
        stubLLM.responses = ["Dear Sir, I hope this message finds you well."]

        // When
        let result = try await processor.processText("hey whats up")

        // Then
        XCTAssertEqual(stubLLM.receivedInputs.count, 1)
        XCTAssertEqual(stubLLM.receivedInputs[0].text, "hey whats up")
        XCTAssertEqual(stubLLM.receivedInputs[0].prompt, "Make this formal")
        XCTAssertEqual(result, "Dear Sir, I hope this message finds you well.")
    }

    // MARK: - 2. Multiple Sequential Calls

    func testPipelineWithMultipleSequentialCalls() async throws {
        // Given
        stubPrompt.promptText = "Summarize this"
        stubLLM.responses = ["Summary A", "Summary B", "Summary C"]

        // When
        let resultA = try await processor.processText("First long text about cats")
        let resultB = try await processor.processText("Second long text about dogs")
        let resultC = try await processor.processText("Third long text about birds")

        // Then
        XCTAssertEqual(stubLLM.receivedInputs.count, 3)

        XCTAssertEqual(stubLLM.receivedInputs[0].text, "First long text about cats")
        XCTAssertEqual(stubLLM.receivedInputs[0].prompt, "Summarize this")
        XCTAssertEqual(resultA, "Summary A")

        XCTAssertEqual(stubLLM.receivedInputs[1].text, "Second long text about dogs")
        XCTAssertEqual(stubLLM.receivedInputs[1].prompt, "Summarize this")
        XCTAssertEqual(resultB, "Summary B")

        XCTAssertEqual(stubLLM.receivedInputs[2].text, "Third long text about birds")
        XCTAssertEqual(stubLLM.receivedInputs[2].prompt, "Summarize this")
        XCTAssertEqual(resultC, "Summary C")
    }

    // MARK: - 3. Different Explicit Prompts

    func testPipelineWithDifferentPrompts() async throws {
        // Given
        stubLLM.responses = ["Formal version", "Casual version", "Summary version"]

        // When
        let formal = try await processor.processText("hello", withPrompt: "Make formal")
        let casual = try await processor.processText("hello", withPrompt: "Make casual")
        let summary = try await processor.processText("hello", withPrompt: "Summarize")

        // Then
        XCTAssertEqual(stubLLM.receivedInputs.count, 3)
        XCTAssertEqual(stubLLM.receivedInputs[0].prompt, "Make formal")
        XCTAssertEqual(stubLLM.receivedInputs[1].prompt, "Make casual")
        XCTAssertEqual(stubLLM.receivedInputs[2].prompt, "Summarize")
        XCTAssertEqual(formal, "Formal version")
        XCTAssertEqual(casual, "Casual version")
        XCTAssertEqual(summary, "Summary version")
    }

    // MARK: - 4. Network Error Propagation (Unauthorized)

    func testPipelineErrorPropagation_NetworkError() async {
        // Given
        stubPrompt.promptText = "Fix grammar"
        stubLLM.errorToThrow = PotterError.network(.unauthorized(provider: "OpenAI"))

        // When / Then
        do {
            _ = try await processor.processText("some text")
            XCTFail("Expected unauthorized error to propagate")
        } catch let error as PotterError {
            XCTAssertEqual(error, PotterError.network(.unauthorized(provider: "OpenAI")))
        } catch {
            XCTFail("Expected PotterError, got \(type(of: error)): \(error)")
        }
    }

    // MARK: - 5. Server Error Propagation

    func testPipelineErrorPropagation_ServerError() async {
        // Given
        stubPrompt.promptText = "Fix grammar"
        stubLLM.errorToThrow = PotterError.network(.serverError(statusCode: 500, message: "Internal error"))

        // When / Then
        do {
            _ = try await processor.processText("some text")
            XCTFail("Expected server error to propagate")
        } catch let error as PotterError {
            XCTAssertEqual(error, PotterError.network(.serverError(statusCode: 500, message: "Internal error")))
        } catch {
            XCTFail("Expected PotterError, got \(type(of: error)): \(error)")
        }
    }

    // MARK: - 6. No Prompt Configured

    func testPipelineWithNoPromptConfigured() async {
        // Given
        stubPrompt.promptText = nil

        // When / Then
        do {
            _ = try await processor.processText("some text")
            XCTFail("Expected missing prompt error")
        } catch let error as PotterError {
            XCTAssertEqual(error, PotterError.configuration(.missingConfiguration(key: "prompt")))
        } catch {
            XCTFail("Expected PotterError, got \(type(of: error)): \(error)")
        }
    }

    // MARK: - 7. Preserves Whitespace in Input

    func testPipelinePreservesWhitespaceInInput() async throws {
        // Given
        let inputWithWhitespace = "  hello world  \n\t"
        stubLLM.responses = ["processed"]

        // When
        _ = try await processor.processText(inputWithWhitespace, withPrompt: "Echo")

        // Then — TextProcessor should pass input as-is to the LLM
        XCTAssertEqual(stubLLM.receivedInputs.count, 1)
        XCTAssertEqual(stubLLM.receivedInputs[0].text, "  hello world  \n\t")
    }

    // MARK: - 8. Trims LLM Output

    func testPipelineTrimsLLMOutput() async throws {
        // Given
        stubLLM.responses = ["  result  \n"]

        // When
        let result = try await processor.processText("input", withPrompt: "Process")

        // Then
        XCTAssertEqual(result, "result")
    }

    // MARK: - 9. Empty LLM Response (whitespace only)

    func testPipelineWithEmptyLLMResponse() async throws {
        // Given
        stubLLM.responses = ["   "]

        // When
        let result = try await processor.processText("input", withPrompt: "Process")

        // Then — after trimming whitespace, result should be empty
        XCTAssertEqual(result, "")
    }

    // MARK: - 10. Long Text

    func testPipelineWithLongText() async throws {
        // Given
        let longText = String(repeating: "a", count: 10_000)
        stubLLM.responses = ["Long text processed successfully."]

        // When
        let result = try await processor.processText(longText, withPrompt: "Summarize")

        // Then
        XCTAssertEqual(stubLLM.receivedInputs.count, 1)
        XCTAssertEqual(stubLLM.receivedInputs[0].text.count, 10_000)
        XCTAssertEqual(result, "Long text processed successfully.")
    }
}

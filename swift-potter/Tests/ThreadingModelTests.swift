import XCTest
import Foundation
@testable import Potter

// MARK: - Mocks

/// Mock prompt provider for threading tests
private class ThreadingMockPromptProvider: PromptProviding {
    var promptText: String? = "Test prompt"
    var promptName: String = "Test"

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

/// Mock LLM processor for threading tests — supports configurable delays and errors
private class ThreadingMockLLMProcessor: LLMProcessing {
    var shouldFail = false
    var failureError: Error?
    var responseText = "processed result"
    var processingDelay: UInt64 = 0 // nanoseconds
    /// Track how many times processText was called (thread-safe via actor)
    private let counter = CallCounter()

    actor CallCounter {
        var count = 0
        func increment() { count += 1 }
        func getCount() -> Int { return count }
    }

    func processText(_ text: String, prompt: String) async throws -> String {
        await counter.increment()
        if processingDelay > 0 {
            try await Task.sleep(nanoseconds: processingDelay)
        }
        if shouldFail {
            throw failureError ?? NSError(domain: "MockLLM", code: 1, userInfo: [NSLocalizedDescriptionKey: "Mock LLM failure"])
        }
        return responseText
    }

    func callCount() async -> Int {
        return await counter.getCount()
    }

    func streamText(_ text: String, prompt: String,
                    onToken: @Sendable @escaping (String) -> Void) async throws -> String {
        await counter.increment()
        if processingDelay > 0 {
            try await Task.sleep(nanoseconds: processingDelay)
        }
        if shouldFail {
            throw failureError ?? NSError(domain: "MockLLM", code: 1, userInfo: [NSLocalizedDescriptionKey: "Mock LLM failure"])
        }
        onToken(responseText)
        return responseText
    }
}

/// Mock icon state delegate to verify protocol can be called from any context
private class ThreadingMockIconStateDelegate: IconStateDelegate {
    var lastState: String?

    func setProcessingState() { lastState = "processing" }
    func setSuccessState() { lastState = "success" }
    func setNormalState() { lastState = "normal" }
    func setErrorState(message: String) { lastState = "error: \(message)" }
}

// MARK: - Threading Model Tests

/// Documents and verifies the threading model of the Potter app.
///
/// Key observations about the current threading model:
/// - `LLMManager` is `@MainActor` — all access must happen on main actor
/// - `PermissionManager` is `@MainActor` — all access must happen on main actor
/// - `PotterCore` is NOT `@MainActor` but has many `@MainActor` methods
/// - `APIKeyService` uses `MainActor.run` blocks for published property updates
/// - `TextProcessor` is NOT actor-isolated — a pure processing unit
/// - `IconStateDelegate` protocol has no actor isolation requirement
class ThreadingModelTests: TestBase {

    // MARK: - 1. TextProcessor is not MainActor-isolated

    /// TextProcessor can be created on any thread because it has no @MainActor annotation.
    /// This test creates a TextProcessor on a background thread to prove it works.
    func testTextProcessorIsNotMainActorIsolated() {
        let expectation = expectation(description: "TextProcessor created off main thread")

        DispatchQueue.global(qos: .userInitiated).async {
            let prompt = ThreadingMockPromptProvider()
            let llm = ThreadingMockLLMProcessor()
            let processor = TextProcessor(promptProvider: prompt, llmProcessor: llm)

            // Verify we are NOT on the main thread
            XCTAssertFalse(Thread.isMainThread, "Should be running on a background thread")
            // Verify the processor was created successfully
            XCTAssertNotNil(processor)

            expectation.fulfill()
        }

        waitForExpectations(timeout: 5)
    }

    // MARK: - 2. TextProcessor.processText is async

    /// processText is an async function — calling it requires await.
    /// This is a compile-time guarantee; if it compiled, the test passes.
    func testTextProcessorProcessTextIsAsync() async throws {
        let prompt = ThreadingMockPromptProvider()
        let llm = ThreadingMockLLMProcessor()
        llm.responseText = "async result"
        let processor = TextProcessor(promptProvider: prompt, llmProcessor: llm)

        // The `await` keyword here proves processText is async.
        // If processText were synchronous, the compiler would warn about unnecessary `await`.
        let result = try await processor.processText("hello", withPrompt: "test")
        XCTAssertEqual(result, "async result")
    }

    // MARK: - 3. LLMManager requires MainActor

    /// LLMManager is annotated with @MainActor, so it must be created on the main actor.
    /// This test is itself @MainActor to allow direct LLMManager creation.
    @MainActor
    func testLLMManagerRequiresMainActor() {
        // This compiles because the test method is @MainActor.
        // Without @MainActor, accessing LLMManager's init or properties
        // would require `await MainActor.run { ... }`.
        let manager = LLMManager()
        XCTAssertNotNil(manager)
        XCTAssertEqual(manager.selectedProvider, .anthropic)
        XCTAssertNotNil(manager.selectedModel)
    }

    // MARK: - 4. APIKeyService validation updates on MainActor

    /// APIKeyService uses `MainActor.run` to update @Published properties.
    /// After validation, `validationStates` and `isValidating` are updated on the main actor.
    @MainActor
    func testAPIKeyServiceValidationUpdatesOnMainActor() async {
        let service = APIKeyService.shared

        // Reset state to a known starting point (singleton may carry state from other tests)
        service.setValidationStateForTesting(.notValidated, for: .anthropic)
        let initialState = service.getValidationState(for: .anthropic)
        XCTAssertEqual(initialState, .notValidated)

        // Validate with an empty key — should fail synchronously before network call
        let result = await service.validateAndSaveAPIKey("", for: .anthropic, using: nil)
        XCTAssertFalse(result.isSuccess)

        // After validation completes, state should be updated on main actor
        // The empty-key path sets the state to invalid via MainActor.run
        let stateAfter = service.getValidationState(for: .anthropic)
        XCTAssertFalse(stateAfter.isValid, "Empty key should result in invalid state")

        // isValidating should be false after completion
        XCTAssertFalse(service.isValidating, "Should not be validating after completion")

        // Reset for other tests
        service.setValidationStateForTesting(.notValidated, for: .anthropic)
    }

    // MARK: - 5. PotterCore can be created off MainActor

    /// PotterCore is NOT @MainActor, so it can be instantiated from any context.
    func testPotterCoreCanBeCreatedOffMainActor() {
        let expectation = expectation(description: "PotterCore created off main thread")

        DispatchQueue.global(qos: .background).async {
            XCTAssertFalse(Thread.isMainThread, "Should be on background thread")

            let core = PotterCore()
            XCTAssertNotNil(core)

            expectation.fulfill()
        }

        waitForExpectations(timeout: 5)
    }

    // MARK: - 6. IconStateDelegate can be called from any thread

    /// The IconStateDelegate protocol has no @MainActor requirement,
    /// so conforming objects can receive calls from any thread.
    func testIconStateDelegateCanBeCalledFromAnyThread() {
        let delegate = ThreadingMockIconStateDelegate()
        let expectation = expectation(description: "Delegate called from background thread")

        DispatchQueue.global(qos: .utility).async {
            XCTAssertFalse(Thread.isMainThread, "Should be on background thread")

            delegate.setProcessingState()
            XCTAssertEqual(delegate.lastState, "processing")

            delegate.setSuccessState()
            XCTAssertEqual(delegate.lastState, "success")

            delegate.setNormalState()
            XCTAssertEqual(delegate.lastState, "normal")

            delegate.setErrorState(message: "test error")
            XCTAssertEqual(delegate.lastState, "error: test error")

            expectation.fulfill()
        }

        waitForExpectations(timeout: 5)
    }

    // MARK: - 7. TextProcessor async completion

    /// Verify that TextProcessor's async processText completes with the expected result.
    func testTextProcessorAsyncCompletion() async throws {
        let prompt = ThreadingMockPromptProvider()
        prompt.promptText = "Make it formal"
        let llm = ThreadingMockLLMProcessor()
        llm.responseText = "Dear Sir or Madam"
        let processor = TextProcessor(promptProvider: prompt, llmProcessor: llm)

        // Using explicit prompt
        let result1 = try await processor.processText("hey", withPrompt: "formalize")
        XCTAssertEqual(result1, "Dear Sir or Madam")

        // Using prompt from provider
        llm.responseText = "Good morning"
        let result2 = try await processor.processText("yo")
        XCTAssertEqual(result2, "Good morning")
    }

    // MARK: - 8. Multiple concurrent text processing

    /// Launch 5 concurrent processText calls and verify all complete successfully.
    func testMultipleConcurrentTextProcessing() async throws {
        let prompt = ThreadingMockPromptProvider()
        let llm = ThreadingMockLLMProcessor()
        llm.responseText = "result"
        // Add a small delay to ensure concurrency is exercised
        llm.processingDelay = 10_000_000 // 10ms
        let processor = TextProcessor(promptProvider: prompt, llmProcessor: llm)

        // Launch 5 concurrent tasks
        try await withThrowingTaskGroup(of: String.self) { group in
            for i in 0..<5 {
                group.addTask {
                    return try await processor.processText("input \(i)", withPrompt: "prompt \(i)")
                }
            }

            var results: [String] = []
            for try await result in group {
                results.append(result)
            }

            XCTAssertEqual(results.count, 5, "All 5 concurrent tasks should complete")
            // All should return the same mocked result
            for result in results {
                XCTAssertEqual(result, "result")
            }
        }

        // Verify the mock was called 5 times
        let count = await llm.callCount()
        XCTAssertEqual(count, 5, "LLM processor should have been called exactly 5 times")
    }

    // MARK: - 9. Async error propagation

    /// Verify that errors thrown in async context propagate correctly through TextProcessor.
    func testAsyncErrorPropagation() async {
        let prompt = ThreadingMockPromptProvider()
        let llm = ThreadingMockLLMProcessor()
        llm.shouldFail = true

        let processor = TextProcessor(promptProvider: prompt, llmProcessor: llm)

        // Test with a custom error
        let customError = PotterError.network(.rateLimited(retryAfter: 30))
        llm.failureError = customError

        do {
            _ = try await processor.processText("test", withPrompt: "prompt")
            XCTFail("Expected error to be thrown")
        } catch let error as PotterError {
            // Verify the exact PotterError propagated through
            XCTAssertEqual(error, customError, "PotterError should propagate unchanged")
        } catch {
            XCTFail("Expected PotterError but got: \(type(of: error)) - \(error)")
        }

        // Test with a generic NSError
        let nsError = NSError(domain: "TestDomain", code: 99, userInfo: [NSLocalizedDescriptionKey: "Generic failure"])
        llm.failureError = nsError

        do {
            _ = try await processor.processText("test", withPrompt: "prompt")
            XCTFail("Expected error to be thrown")
        } catch let error as NSError {
            XCTAssertEqual(error.domain, "TestDomain")
            XCTAssertEqual(error.code, 99)
        }

        // Test error when no prompt is available (prompt provider returns nil)
        prompt.promptText = nil
        llm.shouldFail = false // Reset so we test the prompt-missing path

        do {
            _ = try await processor.processText("test")
            XCTFail("Expected error when prompt is nil")
        } catch {
            // Should be a PotterError.configuration(.missingConfiguration)
            XCTAssertTrue(error.localizedDescription.lowercased().contains("prompt") ||
                          error.localizedDescription.lowercased().contains("configuration"),
                          "Error should relate to missing prompt, got: \(error.localizedDescription)")
        }
    }
}

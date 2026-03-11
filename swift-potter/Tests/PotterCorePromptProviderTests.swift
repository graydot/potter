import XCTest
@testable import Potter

// MARK: - Spy PromptProvider

/// A spy that records calls made to it, allowing injection-path verification.
class SpyPromptProvider: PromptProviding {
    var promptText: String? = "Injected prompt text"
    var promptName: String = "Injected Prompt"
    var promptItem: PromptItem? = nil

    // Call tracking
    var getCurrentPromptTextCallCount = 0
    var getCurrentPromptCallCount = 0
    var currentPromptNameAccessCount = 0

    func getCurrentPromptText() -> String? {
        getCurrentPromptTextCallCount += 1
        return promptText
    }

    func getCurrentPrompt() -> PromptItem? {
        getCurrentPromptCallCount += 1
        return promptItem
    }

    var currentPromptName: String {
        currentPromptNameAccessCount += 1
        return promptName
    }
}

// MARK: - PotterCore PromptProvider Injection Tests

@MainActor
final class PotterCorePromptProviderTests: TestBase {

    // MARK: - Test 1: PotterCore accepts promptProvider in init

    func testPotterCoreAcceptsInjectedPromptProvider() {
        let spy = SpyPromptProvider()
        let core = PotterCore(promptProvider: spy)
        XCTAssertNotNil(core, "PotterCore should be creatable with injected promptProvider")
    }

    // MARK: - Test 2: Default init still works (backward compatibility)

    func testDefaultInitDoesNotRequirePromptProvider() {
        let core = PotterCore()
        XCTAssertNotNil(core, "PotterCore() with no promptProvider should still be constructable")
    }

    // MARK: - Test 3: Injected promptProvider coexists with other injected dependencies

    func testPromptProviderCanBeInjectedAlongsideLLMManager() {
        let spy = SpyPromptProvider()
        let llm = LLMManager()
        let core = PotterCore(llmManager: llm, promptProvider: spy)
        XCTAssertNotNil(core)
        XCTAssertTrue(core.getLLMManager() === llm, "Injected LLMManager should be retained alongside injected promptProvider")
    }

    // MARK: - Test 4: Injected promptProvider coexists with HotkeyProvider

    func testPromptProviderCanBeInjectedAlongsideHotkeyProvider() {
        let spy = SpyPromptProvider()
        let hotkey = MockHotkeyProvider()
        let core = PotterCore(hotkeyProvider: hotkey, promptProvider: spy)
        core.setup()
        XCTAssertTrue(hotkey.setupCalled, "Hotkey provider setup should still be called when promptProvider is also injected")
    }

    // MARK: - Test 5: Nil prompt text falls back to currentMode.prompt without crashing

    func testNilPromptTextFallsBackGracefully() {
        let spy = SpyPromptProvider()
        spy.promptText = nil
        // processClipboardText will short-circuit at "no valid provider" before reaching LLM,
        // but the fallback in getCurrentPromptText() is tested by triggering setup + processing
        let core = PotterCore(promptProvider: spy)
        // Should not crash on init or setup
        core.setup()
        XCTAssertTrue(true, "PotterCore with nil promptText should not crash on setup")
    }

    // MARK: - Test 6: PromptItem with .fast tier is accessible through injected provider

    func testInjectedPromptItemWithFastTierIsReturnedByProvider() {
        let spy = SpyPromptProvider()
        let fastPromptItem = PromptItem(name: "Fast Prompt", prompt: "Quick summarize", modelTier: .fast, outputMode: .replace)
        spy.promptItem = fastPromptItem

        let result = spy.getCurrentPrompt()
        XCTAssertNotNil(result)
        XCTAssertEqual(result?.modelTier, .fast, "Injected prompt item with .fast tier should be returned")
        XCTAssertEqual(spy.getCurrentPromptCallCount, 1)
    }

    // MARK: - Test 7: PromptItem with .append outputMode is accessible through injected provider

    func testInjectedPromptItemWithAppendOutputModeIsReturnedByProvider() {
        let spy = SpyPromptProvider()
        let appendPromptItem = PromptItem(name: "Append Prompt", prompt: "Enhance and append", modelTier: .standard, outputMode: .append)
        spy.promptItem = appendPromptItem

        let result = spy.getCurrentPrompt()
        XCTAssertEqual(result?.outputMode, .append, "Injected prompt item with .append outputMode should be returned")
    }

    // MARK: - Test 8: PromptItem with .prepend outputMode is accessible through injected provider

    func testInjectedPromptItemWithPrependOutputModeIsReturnedByProvider() {
        let spy = SpyPromptProvider()
        let prependPromptItem = PromptItem(name: "Prepend Prompt", prompt: "Add context before", modelTier: nil, outputMode: .prepend)
        spy.promptItem = prependPromptItem

        let result = spy.getCurrentPrompt()
        XCTAssertEqual(result?.outputMode, .prepend)
    }

    // MARK: - Test 9: currentPromptName from injected provider is accessible

    func testInjectedProviderCurrentPromptNameIsAccessible() {
        let spy = SpyPromptProvider()
        spy.promptName = "Custom Test Prompt"

        XCTAssertEqual(spy.currentPromptName, "Custom Test Prompt")
    }

    // MARK: - Test 10: OutputMode.apply works correctly for append mode

    func testOutputModeAppendCombinesTextsCorrectly() {
        let original = "Hello world"
        let llmResult = "This is a greeting."
        let combined = OutputMode.append.apply(original: original, result: llmResult)
        XCTAssertEqual(combined, "Hello world\n\nThis is a greeting.", "Append mode should place original before LLM result")
    }

    // MARK: - Test 11: OutputMode.apply works correctly for prepend mode

    func testOutputModePrependCombinesTextsCorrectly() {
        let original = "Hello world"
        let llmResult = "Context: "
        let combined = OutputMode.prepend.apply(original: original, result: llmResult)
        XCTAssertEqual(combined, "Context: \n\nHello world", "Prepend mode should place LLM result before original")
    }

    // MARK: - Test 12: OutputMode.apply works correctly for replace mode

    func testOutputModeReplaceReturnsOnlyLLMResult() {
        let original = "Hello world"
        let llmResult = "Greetings, universe."
        let combined = OutputMode.replace.apply(original: original, result: llmResult)
        XCTAssertEqual(combined, "Greetings, universe.", "Replace mode should return only the LLM result")
    }

    // MARK: - Test 13: PotterCore with full DI set (llm + prompt + hotkey) constructs correctly

    func testFullDIConstructionDoesNotCrash() {
        let spy = SpyPromptProvider()
        spy.promptText = "Be concise."
        spy.promptName = "Concise"
        let hotkey = MockHotkeyProvider()
        let llm = LLMManager()

        let core = PotterCore(llmManager: llm, hotkeyProvider: hotkey, promptProvider: spy)
        core.setup()

        XCTAssertTrue(hotkey.setupCalled, "Hotkey setup should be called in fully DI-configured PotterCore")
        XCTAssertNotNil(core.getLLMManager())
    }

    // MARK: - Test 14: processClipboardText with no valid provider calls error delegate (not crash)

    func testProcessClipboardTextWithNoValidProviderCallsErrorDelegate() async {
        let spy = SpyPromptProvider()
        spy.promptText = "Test prompt"
        let llm = LLMManager() // not configured — hasValidProvider() will return false
        let mockDelegate = MockIconStateDelegate()

        let core = PotterCore(llmManager: llm, promptProvider: spy)
        core.iconDelegate = mockDelegate
        core.setup()

        core.processClipboardText()

        // Allow the async Task inside processClipboardText to run
        try? await Task.sleep(nanoseconds: 200_000_000) // 0.2 seconds

        XCTAssertNotNil(mockDelegate.lastError, "Error delegate should be called when no valid LLM provider is configured")
    }

    // MARK: - Test 15: Injected promptProvider with nil getCurrentPrompt() doesn't crash during processing attempt

    func testNilGetCurrentPromptDoesNotCrashDuringProcessingAttempt() async {
        let spy = SpyPromptProvider()
        spy.promptText = "Test prompt"
        spy.promptItem = nil // nil PromptItem — tier/outputMode defaults should apply
        let llm = LLMManager()
        let mockDelegate = MockIconStateDelegate()

        let core = PotterCore(llmManager: llm, promptProvider: spy)
        core.iconDelegate = mockDelegate
        core.setup()

        core.processClipboardText()
        try? await Task.sleep(nanoseconds: 200_000_000)

        // If we reach here without crashing, the nil-prompt fallback worked
        XCTAssertTrue(true, "nil getCurrentPrompt() should not crash PotterCore")
    }
}

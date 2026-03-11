import Testing
import XCTest
import AppKit
@testable import Potter

// MARK: - MockHistoryStore

/// In-memory mock that conforms to HistoryStoring.
/// Records all appended entries so tests can inspect them.
final class MockHistoryStore: HistoryStoring {
    private(set) var appendedEntries: [ProcessingHistoryEntry] = []

    func append(_ entry: ProcessingHistoryEntry) {
        appendedEntries.append(entry)
    }

    func loadAll() -> [ProcessingHistoryEntry] {
        return appendedEntries.reversed()
    }

    func delete(id: UUID) {
        appendedEntries.removeAll { $0.id == id }
    }

    func clearAll() {
        appendedEntries.removeAll()
    }
}

// MARK: - StubLLMManager

/// An LLMManager subclass that always reports a valid provider and
/// returns a fixed response from streamText. Optionally throws on demand.
final class StubLLMManager: LLMManager {
    var streamResult: String = "processed output"
    var shouldThrow: Bool = false

    override func hasValidProvider() -> Bool { return true }

    override func streamText(
        _ text: String,
        prompt: String,
        onToken: @Sendable @escaping (String) -> Void
    ) async throws -> String {
        if shouldThrow {
            throw PotterError.network(.requestFailed(underlying: "stub network error"))
        }
        onToken(streamResult)
        return streamResult
    }
}

// MARK: - ProcessingHistoryStoreDITests

@Suite("ProcessingHistoryStore Dependency Injection", .serialized)
struct ProcessingHistoryStoreDITests {

    // Helper: put text on the clipboard so PotterCore's clipboard fallback picks it up.
    private func setClipboard(_ text: String) {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(text, forType: .string)
    }

    private func clearClipboard() {
        NSPasteboard.general.clearContents()
    }

    // MARK: - Test 1: Injected store is used instead of ProcessingHistoryStore.shared

    @Test("Injected MockHistoryStore receives entries, not ProcessingHistoryStore.shared")
    @MainActor
    func injectedStoreReceivesEntries() async throws {
        let mock = MockHistoryStore()
        let stub = StubLLMManager()
        let promptProvider = SpyPromptProvider()

        setClipboard("hello world")
        defer { clearClipboard() }

        let core = PotterCore(
            llmManager: stub,
            promptProvider: promptProvider,
            historyStore: mock
        )

        core.processClipboardText()
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5 s

        #expect(mock.appendedEntries.count == 1,
                "Injected MockHistoryStore should have received exactly 1 entry")
    }

    // MARK: - Test 2: History entry contains correct prompt name, input, output

    @Test("History entry contains correct promptName, inputText, and outputText")
    @MainActor
    func historyEntryContentsAreCorrect() async throws {
        let mock = MockHistoryStore()
        let stub = StubLLMManager()
        stub.streamResult = "the processed result"
        let promptProvider = SpyPromptProvider()
        promptProvider.promptName = "My Prompt"

        setClipboard("the input text")
        defer { clearClipboard() }

        let core = PotterCore(
            llmManager: stub,
            promptProvider: promptProvider,
            historyStore: mock
        )

        core.processClipboardText()
        try await Task.sleep(nanoseconds: 500_000_000)

        guard let entry = mock.appendedEntries.first else {
            Issue.record("Expected at least one history entry but got none")
            return
        }

        #expect(entry.inputText == "the input text",
                "Entry inputText should match the text on the clipboard")
        #expect(entry.outputText == "the processed result",
                "Entry outputText should match the result returned by streamText")
        #expect(entry.promptName == "My Prompt",
                "Entry promptName should match the injected prompt provider's currentPromptName")
    }

    // MARK: - Test 3: History store is NOT written to when no valid LLM provider is configured

    @Test("History store receives no entries when LLM provider is not configured")
    @MainActor
    func historyStoreNotWrittenOnProviderFailure() async throws {
        let mock = MockHistoryStore()
        // Real (unconfigured) LLMManager — hasValidProvider() returns false
        let unconfiguredLLM = LLMManager()
        let promptProvider = SpyPromptProvider()
        let mockDelegate = MockIconStateDelegate()

        setClipboard("some text")
        defer { clearClipboard() }

        let core = PotterCore(
            llmManager: unconfiguredLLM,
            promptProvider: promptProvider,
            historyStore: mock
        )
        core.iconDelegate = mockDelegate

        core.processClipboardText()
        try await Task.sleep(nanoseconds: 300_000_000)

        #expect(mock.appendedEntries.isEmpty,
                "History store should not be written to when no valid LLM provider is configured")
        #expect(mockDelegate.lastError != nil,
                "Error delegate should have been notified of the configuration error")
    }

    // MARK: - Test 4: Multiple processing calls each produce their own history entry

    @Test("Multiple successful processing calls produce separate history entries")
    @MainActor
    func multipleCallsProduceMultipleEntries() async throws {
        let mock = MockHistoryStore()
        let stub = StubLLMManager()
        stub.streamResult = "output"
        let promptProvider = SpyPromptProvider()

        setClipboard("input")
        defer { clearClipboard() }

        let core = PotterCore(
            llmManager: stub,
            promptProvider: promptProvider,
            historyStore: mock
        )

        core.processClipboardText()
        try await Task.sleep(nanoseconds: 400_000_000)

        core.processClipboardText()
        try await Task.sleep(nanoseconds: 400_000_000)

        #expect(mock.appendedEntries.count == 2,
                "Each successful processClipboardText call should append one history entry")
    }

    // MARK: - Test 5: History store is NOT written to when streamText throws

    @Test("History store receives no entries when streamText throws an error")
    @MainActor
    func historyStoreNotWrittenOnStreamError() async throws {
        let mock = MockHistoryStore()
        let stub = StubLLMManager()
        stub.shouldThrow = true
        let promptProvider = SpyPromptProvider()
        let mockDelegate = MockIconStateDelegate()

        setClipboard("text that will fail")
        defer { clearClipboard() }

        let core = PotterCore(
            llmManager: stub,
            promptProvider: promptProvider,
            historyStore: mock
        )
        core.iconDelegate = mockDelegate

        core.processClipboardText()
        try await Task.sleep(nanoseconds: 500_000_000)

        #expect(mock.appendedEntries.isEmpty,
                "History store should not receive entries when streamText throws")
        #expect(mockDelegate.lastError != nil,
                "Error delegate should have been notified of the stream error")
    }
}

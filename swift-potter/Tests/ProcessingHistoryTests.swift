import XCTest
@testable import Potter

// MARK: - ProcessingHistoryEntry Tests

final class ProcessingHistoryEntryTests: XCTestCase {

    func testDefaultIDIsUnique() {
        let a = ProcessingHistoryEntry(inputText: "x", outputText: "y",
                                       promptName: "P", modelName: "M",
                                       providerName: "Anthropic", durationMs: 100)
        let b = ProcessingHistoryEntry(inputText: "x", outputText: "y",
                                       promptName: "P", modelName: "M",
                                       providerName: "Anthropic", durationMs: 100)
        XCTAssertNotEqual(a.id, b.id)
    }

    func testEquatableByID() {
        let id = UUID()
        let a = ProcessingHistoryEntry(id: id, inputText: "x", outputText: "y",
                                       promptName: "P", modelName: "M",
                                       providerName: "Anthropic", durationMs: 100)
        let b = ProcessingHistoryEntry(id: id, inputText: "different", outputText: "also different",
                                       promptName: "Q", modelName: "N",
                                       providerName: "Anthropic", durationMs: 999)
        XCTAssertEqual(a, b, "Entries with the same id should be equal")
    }

    func testCodableRoundTrip() throws {
        let original = ProcessingHistoryEntry(
            id: UUID(),
            timestamp: Date(timeIntervalSince1970: 1_000_000),
            inputText: "hello world",
            outputText: "HELLO WORLD",
            promptName: "Shout",
            modelName: "claude-haiku-4-5-20251001",
            providerName: "Anthropic",
            durationMs: 350
        )

        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(ProcessingHistoryEntry.self, from: data)

        XCTAssertEqual(decoded.id, original.id)
        XCTAssertEqual(decoded.inputText, original.inputText)
        XCTAssertEqual(decoded.outputText, original.outputText)
        XCTAssertEqual(decoded.promptName, original.promptName)
        XCTAssertEqual(decoded.modelName, original.modelName)
        XCTAssertEqual(decoded.providerName, original.providerName)
        XCTAssertEqual(decoded.durationMs, original.durationMs)
        XCTAssertEqual(decoded.timestamp.timeIntervalSince1970,
                       original.timestamp.timeIntervalSince1970, accuracy: 0.001)
    }
}

// MARK: - ProcessingHistoryStore Tests

final class ProcessingHistoryStoreTests: XCTestCase {

    // Each test uses a fresh temp file to avoid inter-test state.
    private func makeStore(maxEntries: Int = 500) -> (ProcessingHistoryStore, URL) {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("potter-test-history-\(UUID().uuidString).json")
        let store = ProcessingHistoryStore(maxEntries: maxEntries, storageURL: url)
        return (store, url)
    }

    private func makeEntry(input: String = "in", output: String = "out") -> ProcessingHistoryEntry {
        ProcessingHistoryEntry(inputText: input, outputText: output,
                               promptName: "Test", modelName: "m",
                               providerName: "p", durationMs: 1)
    }

    private func wait(for store: ProcessingHistoryStore) {
        store.flushForTesting()
    }

    // MARK: append + loadAll

    func testAppendAndLoadAll() {
        let (store, _) = makeStore()
        let e1 = makeEntry(input: "a")
        let e2 = makeEntry(input: "b")
        store.append(e1)
        store.append(e2)
        wait(for: store)

        let loaded = store.loadAll()
        // loadAll returns newest first
        XCTAssertEqual(loaded.count, 2)
        XCTAssertEqual(loaded[0].inputText, "b")
        XCTAssertEqual(loaded[1].inputText, "a")
    }

    func testAppendEmptyStoreStartsEmpty() {
        let (store, _) = makeStore()
        XCTAssertTrue(store.loadAll().isEmpty)
    }

    // MARK: cap enforcement

    func testCapEvictsOldestEntries() {
        let (store, _) = makeStore(maxEntries: 3)
        for i in 1...5 {
            store.append(makeEntry(input: "entry\(i)"))
        }
        wait(for: store)

        let loaded = store.loadAll()
        XCTAssertEqual(loaded.count, 3)
        // Newest entries (3, 4, 5) should remain; oldest (1, 2) evicted
        let inputs = loaded.map { $0.inputText }
        XCTAssertFalse(inputs.contains("entry1"))
        XCTAssertFalse(inputs.contains("entry2"))
        XCTAssertTrue(inputs.contains("entry5"))
    }

    func testCapExactlyAtLimit() {
        let (store, _) = makeStore(maxEntries: 3)
        for i in 1...3 {
            store.append(makeEntry(input: "entry\(i)"))
        }
        wait(for: store)
        XCTAssertEqual(store.loadAll().count, 3)
    }

    // MARK: delete

    func testDeleteRemovesEntry() {
        let (store, _) = makeStore()
        let e1 = makeEntry(input: "keep")
        let e2 = makeEntry(input: "remove")
        store.append(e1)
        store.append(e2)
        wait(for: store)

        store.delete(id: e2.id)
        wait(for: store)

        let loaded = store.loadAll()
        XCTAssertEqual(loaded.count, 1)
        XCTAssertEqual(loaded.first?.inputText, "keep")
    }

    func testDeleteNonExistentIDIsNoop() {
        let (store, _) = makeStore()
        store.append(makeEntry())
        wait(for: store)

        store.delete(id: UUID())  // random ID, not in store
        wait(for: store)

        XCTAssertEqual(store.loadAll().count, 1)
    }

    // MARK: clearAll

    func testClearAllRemovesEverything() {
        let (store, _) = makeStore()
        store.append(makeEntry())
        store.append(makeEntry())
        wait(for: store)

        store.clearAll()
        wait(for: store)

        XCTAssertTrue(store.loadAll().isEmpty)
    }

    // MARK: persistence

    func testPersistsAcrossInstances() {
        let (store1, url) = makeStore()
        let entry = makeEntry(input: "persisted")
        store1.append(entry)
        wait(for: store1)

        // Create a second store pointing at the same file
        let store2 = ProcessingHistoryStore(storageURL: url)
        let loaded = store2.loadAll()
        XCTAssertEqual(loaded.count, 1)
        XCTAssertEqual(loaded.first?.inputText, "persisted")
    }

    func testLoadFromNonexistentFileStartsEmpty() {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("doesnotexist-\(UUID().uuidString).json")
        let store = ProcessingHistoryStore(storageURL: url)
        XCTAssertTrue(store.loadAll().isEmpty)
    }
}


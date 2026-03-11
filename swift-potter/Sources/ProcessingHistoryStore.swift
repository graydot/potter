import Foundation

/// Persists and manages the processing history log.
///
/// - Thread safety: all mutations go through a serial `DispatchQueue`; reads
///   are safe to call from any thread via the `@Published`-style `entries` array
///   (reads are copy-on-write value types).
/// - Storage: `~/Library/Application Support/Potter/processing_history.json`
/// - Cap: oldest entries are dropped once the total exceeds `maxEntries` (default 500).
final class ProcessingHistoryStore: HistoryStoring {

    // MARK: - Singleton

    static let shared = ProcessingHistoryStore()

    // MARK: - Configuration

    /// Maximum number of entries to retain. Oldest entries are evicted first.
    let maxEntries: Int

    // MARK: - State

    private(set) var entries: [ProcessingHistoryEntry] = []
    private let queue = DispatchQueue(label: "com.potter.history", qos: .utility)

    // MARK: - Storage URL

    private let storageURL: URL

    // MARK: - Init

    init(maxEntries: Int = 500, storageURL: URL? = nil) {
        self.maxEntries = maxEntries

        if let url = storageURL {
            self.storageURL = url
        } else {
            let appSupport = FileManager.default.urls(
                for: .applicationSupportDirectory,
                in: .userDomainMask
            ).first!.appendingPathComponent("Potter")
            self.storageURL = appSupport.appendingPathComponent("processing_history.json")
        }

        load()
    }

    // MARK: - Public API

    /// Appends a new entry, evicting the oldest if over the cap, then saves.
    func append(_ entry: ProcessingHistoryEntry) {
        queue.async { [weak self] in
            guard let self else { return }
            self.entries.append(entry)
            if self.entries.count > self.maxEntries {
                self.entries.removeFirst(self.entries.count - self.maxEntries)
            }
            self.save()
        }
    }

    /// Removes a single entry by ID, then saves.
    func delete(id: UUID) {
        queue.async { [weak self] in
            guard let self else { return }
            self.entries.removeAll { $0.id == id }
            self.save()
        }
    }

    /// Removes all entries and saves.
    func clearAll() {
        queue.async { [weak self] in
            guard let self else { return }
            self.entries.removeAll()
            self.save()
        }
    }

    /// Returns a snapshot of all entries (newest first).
    func loadAll() -> [ProcessingHistoryEntry] {
        return entries.reversed()
    }

    // MARK: - Testing Support

    /// Synchronously waits for all queued mutations to complete.
    /// Intended for use in tests only.
    func flushForTesting() {
        queue.sync {}
    }

    // MARK: - Persistence

    private func load() {
        guard FileManager.default.fileExists(atPath: storageURL.path) else { return }
        do {
            let data = try Data(contentsOf: storageURL)
            entries = try JSONDecoder().decode([ProcessingHistoryEntry].self, from: data)
        } catch {
            // Corrupted file — start fresh, don't crash
            entries = []
        }
    }

    private func save() {
        do {
            let dir = storageURL.deletingLastPathComponent()
            try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            let data = try JSONEncoder().encode(entries)
            try data.write(to: storageURL, options: .atomic)
        } catch {
            // Best-effort — logging unavailable here to avoid circular dep
        }
    }
}

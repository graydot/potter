import Foundation

/// A single recorded processing run.
struct ProcessingHistoryEntry: Identifiable, Codable, Equatable {
    let id: UUID
    let timestamp: Date
    let inputText: String
    let outputText: String
    let promptName: String
    let modelName: String
    let providerName: String
    let durationMs: Int

    init(
        id: UUID = UUID(),
        timestamp: Date = Date(),
        inputText: String,
        outputText: String,
        promptName: String,
        modelName: String,
        providerName: String,
        durationMs: Int
    ) {
        self.id = id
        self.timestamp = timestamp
        self.inputText = inputText
        self.outputText = outputText
        self.promptName = promptName
        self.modelName = modelName
        self.providerName = providerName
        self.durationMs = durationMs
    }

    static func == (lhs: ProcessingHistoryEntry, rhs: ProcessingHistoryEntry) -> Bool {
        lhs.id == rhs.id
    }
}

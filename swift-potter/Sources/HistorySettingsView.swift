import SwiftUI
import AppKit

@available(macOS 14.0, *)
struct HistorySettingsView: View {

    // MARK: - State

    @State private var entries: [ProcessingHistoryEntry] = []
    @State private var selectedEntryID: UUID? = nil
    @State private var showClearConfirm = false

    private let store = ProcessingHistoryStore.shared

    // MARK: - Formatting

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .short
        f.timeStyle = .medium
        return f
    }()

    // MARK: - Body

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            headerSection
            if entries.isEmpty {
                emptyState
            } else {
                contentSection
            }
        }
        .onAppear { reload() }
    }

    // MARK: - Sections

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Processing History")
                    .font(.title2)
                    .fontWeight(.semibold)
                Text("\(entries.count) entries — local only, never synced")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Spacer()
            Button("Clear All") {
                showClearConfirm = true
            }
            .foregroundColor(.red)
            .disabled(entries.isEmpty)
            .confirmationDialog("Clear all history?",
                                isPresented: $showClearConfirm,
                                titleVisibility: .visible) {
                Button("Clear All", role: .destructive) {
                    store.clearAll()
                    // Give the store's serial queue a moment to finish writing
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { reload() }
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("This cannot be undone.")
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 8) {
            Image(systemName: "clock.arrow.circlepath")
                .font(.largeTitle)
                .foregroundColor(.secondary)
            Text("No history yet")
                .font(.headline)
                .foregroundColor(.secondary)
            Text("Every successful processing run will appear here.")
                .font(.caption)
                .foregroundColor(Color(NSColor.tertiaryLabelColor))
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var contentSection: some View {
        HSplitView {
            // Left: list of entries
            listPanel
                .frame(minWidth: 260, idealWidth: 280, maxWidth: 400)

            // Right: detail pane
            detailPanel
                .frame(minWidth: 300, maxWidth: .infinity)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - List Panel

    private var listPanel: some View {
        List(entries, selection: $selectedEntryID) { entry in
            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(entry.promptName)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .lineLimit(1)
                    Spacer()
                    Text("\(entry.durationMs) ms")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                Text(entry.inputText.prefix(60) + (entry.inputText.count > 60 ? "…" : ""))
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
                Text(Self.dateFormatter.string(from: entry.timestamp))
                    .font(.caption2)
                    .foregroundColor(Color(NSColor.tertiaryLabelColor))
            }
            .padding(.vertical, 2)
            .tag(entry.id)
            .contextMenu {
                Button("Delete Entry") {
                    store.delete(id: entry.id)
                    if selectedEntryID == entry.id { selectedEntryID = nil }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { reload() }
                }
            }
        }
        .listStyle(.plain)
    }

    // MARK: - Detail Panel

    private var detailPanel: some View {
        Group {
            if let id = selectedEntryID, let entry = entries.first(where: { $0.id == id }) {
                entryDetail(entry)
            } else {
                Text("Select an entry to view details")
                    .font(.callout)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    @ViewBuilder
    private func entryDetail(_ entry: ProcessingHistoryEntry) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {

                // Metadata row
                HStack(spacing: 16) {
                    Label(entry.promptName, systemImage: "text.bubble")
                    Label(entry.modelName.isEmpty ? "Unknown model" : entry.modelName,
                          systemImage: "cpu")
                    Label(entry.providerName, systemImage: "network")
                    Spacer()
                    Label("\(entry.durationMs) ms", systemImage: "timer")
                }
                .font(.caption)
                .foregroundColor(.secondary)

                Divider()

                // Input
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Input")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        Spacer()
                        Button("Copy") { copyToClipboard(entry.inputText) }
                            .font(.caption)
                    }
                    ScrollView {
                        Text(entry.inputText)
                            .font(.system(.caption, design: .monospaced))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                    .frame(minHeight: 80, maxHeight: 200)
                    .background(Color(NSColor.textBackgroundColor))
                    .cornerRadius(6)
                }

                // Output
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Output")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        Spacer()
                        Button("Copy") { copyToClipboard(entry.outputText) }
                            .font(.caption)
                    }
                    ScrollView {
                        Text(entry.outputText)
                            .font(.system(.caption, design: .monospaced))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                    .frame(minHeight: 80, maxHeight: 200)
                    .background(Color(NSColor.textBackgroundColor))
                    .cornerRadius(6)
                }

                Spacer()
            }
            .padding()
        }
    }

    // MARK: - Helpers

    private func reload() {
        entries = store.loadAll()
    }

    private func copyToClipboard(_ text: String) {
        let pb = NSPasteboard.general
        pb.clearContents()
        pb.setString(text, forType: .string)
    }
}

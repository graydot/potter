import SwiftUI
import AppKit

extension DateFormatter {
    static let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss.SSS"
        return formatter
    }()
}

@available(macOS 14.0, *)
struct LogsSettingsView: View {
    @StateObject private var logger = PotterLogger.shared
    @State private var logFilter: PotterLogger.LogEntry.LogLevel? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            headerSection
            controlsSection
            contentSection
            footerSection
            Spacer()
        }
    }

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Application Logs")
                .font(.title)
                .fontWeight(.semibold)

            Text("View application logs for debugging and troubleshooting")
                .foregroundColor(.secondary)
        }
    }

    private var controlsSection: some View {
        HStack {
            Text("Filter:")
            Picker("", selection: $logFilter) {
                Text("All").tag(nil as PotterLogger.LogEntry.LogLevel?)
                Text("Info").tag(PotterLogger.LogEntry.LogLevel.info as PotterLogger.LogEntry.LogLevel?)
                Text("Warning").tag(PotterLogger.LogEntry.LogLevel.warning as PotterLogger.LogEntry.LogLevel?)
                Text("Error").tag(PotterLogger.LogEntry.LogLevel.error as PotterLogger.LogEntry.LogLevel?)
                Text("Debug").tag(PotterLogger.LogEntry.LogLevel.debug as PotterLogger.LogEntry.LogLevel?)
            }
            .pickerStyle(MenuPickerStyle())
            .frame(width: 100)

            Spacer()

            Button("Refresh") {
                // Logs auto-refresh via @StateObject
            }

            Button("Clear") {
                logger.clearLogs()
            }

            Button("Open File") {
                if let fileURL = logger.saveLogsToFile() {
                    NSWorkspace.shared.open(fileURL)
                }
            }
        }
    }

    private var contentSection: some View {
        VStack(spacing: 8) {
            HStack {
                Button("Copy All Logs") {
                    let filteredLogs = logger.filteredEntries(level: logFilter)
                    let logText = filteredLogs.map { logEntry in
                        let timestamp = DateFormatter.timeFormatter.string(from: logEntry.timestamp)
                        return "\(timestamp) - \(logEntry.component) - \(logEntry.level.rawValue) - \(logEntry.message)"
                    }.joined(separator: "\n")

                    let pasteboard = NSPasteboard.general
                    pasteboard.clearContents()
                    pasteboard.setString(logText, forType: .string)
                }
                .buttonStyle(.bordered)

                Spacer()

                Text("\(logger.filteredEntries(level: logFilter).count) entries")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }

            ScrollViewReader { proxy in
                TextEditor(text: .constant(formattedLogText()))
                    .font(.system(.caption, design: .monospaced))
                    .frame(height: 300)
                    .background(Color(NSColor.textBackgroundColor))
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color(NSColor.separatorColor))
                    )
                    .onChange(of: logger.logEntries.count) { _ in
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                            if let textView = findTextView() {
                                textView.scrollToEndOfDocument(nil)
                            }
                        }
                    }
            }
        }
    }

    private var footerSection: some View {
        let totalLogs = logger.logEntries.count
        let filteredCount = logger.filteredEntries(level: logFilter).count
        return Text("Showing \(filteredCount) of \(totalLogs) log entries")
            .foregroundColor(.secondary)
            .font(.caption)
    }

    // MARK: - Helpers

    private func formattedLogText() -> String {
        let filteredLogs = logger.filteredEntries(level: logFilter)
        return filteredLogs.map { logEntry in
            let timestamp = DateFormatter.timeFormatter.string(from: logEntry.timestamp)
            let levelIndicator = logEntry.level.emoji
            return "\(timestamp) \(levelIndicator) [\(logEntry.component)] \(logEntry.message)"
        }.joined(separator: "\n")
    }

    private func findTextView() -> NSTextView? {
        guard let window = NSApplication.shared.windows.first(where: { $0.title.contains("Potter") }) else { return nil }
        return findTextViewInView(window.contentView)
    }

    private func findTextViewInView(_ view: NSView?) -> NSTextView? {
        guard let view = view else { return nil }

        if let textView = view as? NSTextView {
            return textView
        }

        for subview in view.subviews {
            if let found = findTextViewInView(subview) {
                return found
            }
        }

        return nil
    }
}

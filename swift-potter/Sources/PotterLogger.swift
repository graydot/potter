import Foundation
import OSLog
import AppKit

class PotterLogger: ObservableObject {
    static let shared = PotterLogger()
    
    @Published var logEntries: [LogEntry] = []
    private let maxLogEntries = 500
    private let logger = Logger(subsystem: "com.potter.app", category: "general")
    
    struct LogEntry {
        let timestamp: Date
        let level: LogLevel
        let component: String
        let message: String
        
        enum LogLevel: String, CaseIterable {
            case info = "INFO"
            case warning = "WARNING"
            case error = "ERROR"
            case debug = "DEBUG"
            
            var color: NSColor {
                switch self {
                case .info: return .systemBlue
                case .warning: return .systemOrange
                case .error: return .systemRed
                case .debug: return .systemGray
                }
            }
            
            var emoji: String {
                switch self {
                case .info: return "ℹ️"
                case .warning: return "⚠️"
                case .error: return "❌"
                case .debug: return "🐛"
                }
            }
        }
        
        var formattedString: String {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd HH:mm:ss.SSS"
            return "\(formatter.string(from: timestamp)) - \(component) - \(level.rawValue) - \(message)"
        }
    }
    
    private init() {
        // Add initial startup logs
        log(.info, component: "main", message: "🎭 Potter - AI Text Processing Tool")
        log(.info, component: "main", message: "Starting Swift version...")
    }
    
    func log(_ level: LogEntry.LogLevel, component: String, message: String) {
        let sanitizedMessage = sanitizeMessage(message)
        let entry = LogEntry(
            timestamp: Date(),
            level: level,
            component: component,
            message: sanitizedMessage
        )
        
        DispatchQueue.main.async {
            self.logEntries.append(entry)
            
            // Keep only the most recent entries
            if self.logEntries.count > self.maxLogEntries {
                self.logEntries.removeFirst(self.logEntries.count - self.maxLogEntries)
            }
        }
        
        // Also log to system logger (using sanitized message)
        switch level {
        case .info:
            logger.info("\(component) - \(sanitizedMessage)")
        case .warning:
            logger.warning("\(component) - \(sanitizedMessage)")
        case .error:
            logger.error("\(component) - \(sanitizedMessage)")
        case .debug:
            logger.debug("\(component) - \(sanitizedMessage)")
        }
        
        // Print to console for development (using sanitized message)
        print("\(entry.formattedString)")
    }
    
    func info(_ component: String, _ message: String) {
        log(.info, component: component, message: message)
    }
    
    func warning(_ component: String, _ message: String) {
        log(.warning, component: component, message: message)
    }
    
    func error(_ component: String, _ message: String) {
        log(.error, component: component, message: message)
    }
    
    func debug(_ component: String, _ message: String) {
        log(.debug, component: component, message: message)
    }
    
    func clearLogs() {
        DispatchQueue.main.async {
            self.logEntries.removeAll()
        }
        log(.info, component: "logger", message: "Log entries cleared")
    }
    
    // MARK: - Message Sanitization
    
    /// Sanitizes log messages to prevent exposure of sensitive information
    /// Delegates to SecuritySanitizer for separation of concerns
    private func sanitizeMessage(_ message: String) -> String {
        return SecuritySanitizer.shared.sanitizeMessage(message)
    }
    
    func filteredEntries(level: LogEntry.LogLevel?) -> [LogEntry] {
        guard let level = level else { return logEntries }
        return logEntries.filter { $0.level == level }
    }
    
    func saveLogsToFile() -> URL? {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd_HH-mm-ss"
        let filename = "potter_logs_\(formatter.string(from: Date())).txt"
        
        let documentsPath = FileManager.default.urls(for: .documentDirectory, 
                                                   in: .userDomainMask).first!
        let logFileURL = documentsPath.appendingPathComponent(filename)
        
        let logContent = logEntries.map { $0.formattedString }.joined(separator: "\n")
        
        do {
            try logContent.write(to: logFileURL, atomically: true, encoding: .utf8)
            return logFileURL
        } catch {
            log(.error, component: "logger", message: "Failed to save logs: \(error)")
            return nil
        }
    }
}
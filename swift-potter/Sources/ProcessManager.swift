import Foundation
import AppKit

// MARK: - Build Info Structure
struct BuildInfo {
    let buildId: String
    let version: String
    let buildDate: String
    let processId: Int32
    
    static func current() -> BuildInfo {
        return BuildInfo(
            buildId: UUID().uuidString.prefix(8).uppercased() + "-DEV",
            version: "2.0.0-dev",
            buildDate: DateFormatter.buildDateFormatter.string(from: Date()),
            processId: getpid()
        )
    }
}

extension DateFormatter {
    static let buildDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter
    }()
}

// MARK: - Process Detection Result
enum ProcessCheckResult {
    case noDuplicates
    case foundDuplicates([RunningPotterProcess])
}

struct RunningPotterProcess {
    let pid: Int32
    let buildInfo: BuildInfo?
    let launchPath: String?
}

// MARK: - Process Manager
class ProcessManager {
    static let shared = ProcessManager()
    private let lockFileName = "potter.lock"
    
    private var lockFileURL: URL {
        // Always use Application Support to ensure consistency between command line and app bundle
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let potterDir = appSupport.appendingPathComponent("Potter")
        try? FileManager.default.createDirectory(at: potterDir, withIntermediateDirectories: true)
        return potterDir.appendingPathComponent(lockFileName)
    }
    
    func checkForDuplicateProcesses() -> ProcessCheckResult {
        PotterLogger.shared.info("process", "🔍 Checking for duplicate Potter processes...")
        
        // Check if lock file exists
        if FileManager.default.fileExists(atPath: lockFileURL.path) {
            // Read existing lock file
            do {
                let lockData = try Data(contentsOf: lockFileURL)
                let lockInfo = try JSONSerialization.jsonObject(with: lockData) as? [String: Any]
                
                if let existingPid = lockInfo?["processId"] as? Int32 {
                    // Check if that process is still running
                    if kill(existingPid, 0) == 0 {
                        PotterLogger.shared.warning("process", "⚠️ Found existing Potter process (PID: \(existingPid))")
                        
                        // Process is still running, show dialog
                        let existingProcess = RunningPotterProcess(
                            pid: existingPid,
                            buildInfo: BuildInfo(
                                buildId: lockInfo?["buildId"] as? String ?? "Unknown",
                                version: lockInfo?["version"] as? String ?? "Unknown", 
                                buildDate: lockInfo?["buildDate"] as? String ?? "Unknown",
                                processId: existingPid
                            ),
                            launchPath: "Potter Application"
                        )
                        return .foundDuplicates([existingProcess])
                    } else {
                        PotterLogger.shared.info("process", "🧹 Removing stale lock file (process \(existingPid) no longer running)")
                        // Process is dead, remove stale lock file
                        try? FileManager.default.removeItem(at: lockFileURL)
                    }
                }
            } catch {
                PotterLogger.shared.warning("process", "⚠️ Error reading lock file: \(error)")
                // If we can't read the lock file, remove it
                try? FileManager.default.removeItem(at: lockFileURL)
            }
        }
        
        PotterLogger.shared.info("process", "✅ No duplicate processes found")
        createLockFile()
        return .noDuplicates
    }
    
    private func getBuildInfoForProcess(pid: Int32) -> BuildInfo? {
        // For now, we can't easily get build info from other processes
        // In a real implementation, this could read from shared files or IPC
        return nil
    }
    
    private func compareBuildInfo(current: BuildInfo, other: BuildInfo) -> String {
        // Compare versions
        if current.version != other.version {
            return "Different versions (this: \(current.version), running: \(other.version))"
        }
        
        // Compare build dates
        let dateFormatter = DateFormatter.buildDateFormatter
        if let currentDate = dateFormatter.date(from: current.buildDate),
           let otherDate = dateFormatter.date(from: other.buildDate) {
            
            let timeDifference = abs(currentDate.timeIntervalSince(otherDate))
            
            if timeDifference < 60 { // Less than 1 minute apart
                return "Both builds are essentially the same"
            } else if currentDate > otherDate {
                return "This build is newer than the running one"
            } else {
                return "The running build is newer than this one"
            }
        }
        
        // Compare build IDs as fallback
        if current.buildId == other.buildId {
            return "Both builds are identical"
        } else {
            return "Different builds"
        }
    }
    
    func showDuplicateProcessDialog(otherProcesses: [RunningPotterProcess]) -> DuplicateProcessAction {
        let currentBuild = BuildInfo.current()
        
        var message = "Potter is already running.\n\n"
        
        // Add comparison summary at the top
        if let otherProcess = otherProcesses.first,
           let buildInfo = otherProcess.buildInfo {
            let comparison = compareBuildInfo(current: currentBuild, other: buildInfo)
            message += "📊 Summary: \(comparison)\n\n"
        }
        
        // Current instance info
        message += "This Instance:\n"
        message += "Version: \(currentBuild.version)\n"
        message += "Built: \(currentBuild.buildDate)\n\n"
        
        // Other instance info
        if let otherProcess = otherProcesses.first,
           let buildInfo = otherProcess.buildInfo {
            message += "Running Instance:\n"
            message += "Version: \(buildInfo.version)\n"
            message += "Built: \(buildInfo.buildDate)\n\n"
        }
        
        message += "You can either close the other copy and continue, or exit this one."
        
        let alert = NSAlert()
        alert.messageText = "Potter is Already Running"
        alert.informativeText = message
        alert.alertStyle = .informational
        alert.icon = NSImage(systemSymbolName: "exclamationmark.triangle", accessibilityDescription: "Warning")
        
        alert.addButton(withTitle: "Close Other & Continue")
        alert.addButton(withTitle: "Exit")
        
        let response = alert.runModal()
        
        switch response {
        case .alertFirstButtonReturn:
            return .killOthersAndContinue
        case .alertSecondButtonReturn:
            return .exitThisProcess
        default:
            return .exitThisProcess
        }
    }
    
    func killProcess(pid: Int32) -> Bool {
        let result = kill(pid, SIGTERM)
        if result == 0 {
            PotterLogger.shared.info("process", "✅ Successfully terminated process \(pid)")
            // Wait a moment for graceful shutdown
            Thread.sleep(forTimeInterval: 1.0)
            
            // If still running, force kill
            if kill(pid, 0) == 0 {
                kill(pid, SIGKILL)
                PotterLogger.shared.info("process", "🔫 Force killed process \(pid)")
            }
            return true
        } else {
            PotterLogger.shared.error("process", "❌ Failed to terminate process \(pid)")
            return false
        }
    }
    
    private func createLockFile() {
        let currentBuild = BuildInfo.current()
        let lockData = """
        {
            "buildId": "\(currentBuild.buildId)",
            "version": "\(currentBuild.version)",
            "buildDate": "\(currentBuild.buildDate)",
            "processId": \(currentBuild.processId),
            "timestamp": "\(ISO8601DateFormatter().string(from: Date()))"
        }
        """.data(using: .utf8)
        
        do {
            try lockData?.write(to: lockFileURL)
            PotterLogger.shared.info("process", "📝 Created lock file at \(lockFileURL.path)")
        } catch {
            PotterLogger.shared.error("process", "Failed to create lock file: \(error)")
        }
    }
    
    func removeLockFile() {
        do {
            if FileManager.default.fileExists(atPath: lockFileURL.path) {
                try FileManager.default.removeItem(at: lockFileURL)
                PotterLogger.shared.info("process", "🗑️ Removed lock file")
            }
        } catch {
            PotterLogger.shared.error("process", "Failed to remove lock file: \(error)")
        }
    }
}

// MARK: - User Action Enum
enum DuplicateProcessAction {
    case killOthersAndContinue
    case exitThisProcess
}
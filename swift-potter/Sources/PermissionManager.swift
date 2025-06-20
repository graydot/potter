import Foundation
import AppKit
import UserNotifications

// MARK: - Permission Types
enum PermissionType: String, CaseIterable {
    case accessibility = "accessibility"
    case notifications = "notifications"
    
    var displayName: String {
        switch self {
        case .accessibility: return "Accessibility"
        case .notifications: return "Notifications"
        }
    }
    
    var description: String {
        switch self {
        case .accessibility: return "Required for global hotkey (⌘⇧9)"
        case .notifications: return "Optional for status updates"
        }
    }
    
    var isRequired: Bool {
        switch self {
        case .accessibility: return true
        case .notifications: return false
        }
    }
}

// MARK: - Permission Status
enum PermissionStatus {
    case granted
    case denied
    case notDetermined
    case unknown
    
    var color: NSColor {
        switch self {
        case .granted: return .systemGreen
        case .denied: return .systemRed
        case .notDetermined: return .systemOrange
        case .unknown: return .systemGray
        }
    }
    
    var iconName: String {
        switch self {
        case .granted: return "checkmark.circle.fill"
        case .denied: return "xmark.circle.fill"
        case .notDetermined: return "questionmark.circle.fill"
        case .unknown: return "minus.circle.fill"
        }
    }
    
    var displayText: String {
        switch self {
        case .granted: return "Granted"
        case .denied: return "Denied"
        case .notDetermined: return "Not Set"
        case .unknown: return "Unknown"
        }
    }
}

// MARK: - Permission Manager
@MainActor
class PermissionManager: ObservableObject {
    @Published var accessibilityStatus: PermissionStatus = .unknown
    @Published var notificationsStatus: PermissionStatus = .unknown
    @Published var isCheckingPermissions = false
    
    private var permissionCheckTimer: Timer?
    private var checkStartTime: Date?
    
    // Track initial states to detect changes since app launch
    private var initialAccessibilityStatus: PermissionStatus = .unknown
    private var hasPromptedForRestartThisSession = false
    
    static let shared = PermissionManager()
    
    init() {
        checkAllPermissions()
        // Store initial state after first check
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            self.initialAccessibilityStatus = self.accessibilityStatus
        }
    }
    
    // MARK: - Permission Checking
    func checkAllPermissions() {
        checkAccessibilityPermission()
        checkNotificationPermission()
        
        // Force reset checking state if it's been too long
        if isCheckingPermissions {
            if let startTime = checkStartTime, Date().timeIntervalSince(startTime) > 600 { // 10 minutes
                PotterLogger.shared.warning("permissions", "⚠️ Permission checking stuck - forcing reset")
                stopPermissionMonitoring()
            }
        }
    }
    
    private func checkAccessibilityPermission() {
        let trusted = AXIsProcessTrusted()
        accessibilityStatus = trusted ? .granted : .denied
        
        PotterLogger.shared.info("permissions", "🔐 Accessibility: \(accessibilityStatus.displayText)")
        
        // Only prompt for restart if:
        // 1. We haven't already prompted this session
        // 2. Permission changed from not-granted to granted since app launch
        // 3. We're currently monitoring (user just granted permission)
        if !hasPromptedForRestartThisSession && 
           initialAccessibilityStatus != .granted && 
           accessibilityStatus == .granted && 
           isCheckingPermissions {
            
            PotterLogger.shared.info("permissions", "🔐 Accessibility permission newly granted since launch - prompting for restart")
            hasPromptedForRestartThisSession = true
            stopPermissionMonitoring()
            
            // Delay prompt slightly to let UI update
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.promptForRestart()
            }
        }
    }
    
    private func checkNotificationPermission() {
        // Check if we're running in debug mode without proper bundle
        let isDebugMode = Bundle.main.bundleIdentifier == nil
        
        if isDebugMode {
            // For debug mode, simulate a reasonable notification status
            notificationsStatus = .notDetermined
            PotterLogger.shared.info("permissions", "📱 Notifications: \(notificationsStatus.displayText) (debug mode)")
            return
        }
        
        // For production builds with proper bundle identifier
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            DispatchQueue.main.async {
                switch settings.authorizationStatus {
                case .authorized:
                    self.notificationsStatus = .granted
                case .denied:
                    self.notificationsStatus = .denied
                case .notDetermined:
                    self.notificationsStatus = .notDetermined
                case .provisional:
                    self.notificationsStatus = .granted
                case .ephemeral:
                    self.notificationsStatus = .granted
                @unknown default:
                    self.notificationsStatus = .unknown
                }
                
                PotterLogger.shared.info("permissions", "📱 Notifications: \(self.notificationsStatus.displayText)")
            }
        }
    }
    
    // MARK: - Permission Requests
    func requestAccessibilityPermission() {
        PotterLogger.shared.info("permissions", "🔐 Requesting accessibility permission...")
        openSystemSettings(for: .accessibility)
        startPermissionMonitoring()
    }
    
    func requestNotificationPermission() {
        PotterLogger.shared.info("permissions", "📱 Requesting notification permission...")
        
        // Check if we're running in debug mode without proper bundle
        let isDebugMode = Bundle.main.bundleIdentifier == nil
        
        if isDebugMode {
            PotterLogger.shared.warning("permissions", "📱 Notification permission not available in debug mode")
            openSystemSettings(for: .notifications)
            return
        }
        
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            DispatchQueue.main.async {
                if let error = error {
                    PotterLogger.shared.error("permissions", "❌ Notification permission error: \(error.localizedDescription)")
                } else {
                    PotterLogger.shared.info("permissions", "📱 Notification permission: \(granted ? "granted" : "denied")")
                }
                self.checkNotificationPermission()
            }
        }
    }
    
    // MARK: - System Settings Navigation
    func openSystemSettings(for permission: PermissionType) {
        let urlString: String
        
        switch permission {
        case .accessibility:
            urlString = "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        case .notifications:
            urlString = "x-apple.systempreferences:com.apple.preference.notifications"
        }
        
        if let url = URL(string: urlString) {
            NSWorkspace.shared.open(url)
            PotterLogger.shared.info("permissions", "🔗 Opened System Settings for \(permission.displayName)")
        } else {
            // Fallback to general System Settings
            NSWorkspace.shared.open(URL(string: "x-apple.systempreferences:")!)
            PotterLogger.shared.warning("permissions", "⚠️ Opened general System Settings (deep link failed)")
        }
        
        startPermissionMonitoring()
    }
    
    // MARK: - Permission Monitoring
    private func startPermissionMonitoring() {
        guard !isCheckingPermissions else { return }
        
        isCheckingPermissions = true
        checkStartTime = Date()
        
        PotterLogger.shared.info("permissions", "⏱️ Starting permission monitoring...")
        
        // Check every 1 second for 1 minute
        permissionCheckTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] timer in
            self?.checkAllPermissions()
            
            guard let startTime = self?.checkStartTime else {
                timer.invalidate()
                return
            }
            
            let elapsed = Date().timeIntervalSince(startTime)
            
            if elapsed >= 60 { // After 1 minute, switch to 10-second intervals
                timer.invalidate()
                self?.startSlowMonitoring()
            }
        }
    }
    
    private func startSlowMonitoring() {
        PotterLogger.shared.info("permissions", "⏱️ Switching to slow permission monitoring...")
        
        // Check every 10 seconds for 5 minutes
        permissionCheckTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: true) { [weak self] timer in
            self?.checkAllPermissions()
            
            guard let startTime = self?.checkStartTime else {
                timer.invalidate()
                return
            }
            
            let elapsed = Date().timeIntervalSince(startTime)
            
            if elapsed >= 360 { // 6 minutes total (1 min fast + 5 min slow)
                self?.stopPermissionMonitoring()
            }
        }
    }
    
    func stopPermissionMonitoring() {
        permissionCheckTimer?.invalidate()
        permissionCheckTimer = nil
        checkStartTime = nil
        isCheckingPermissions = false
        
        PotterLogger.shared.info("permissions", "⏹️ Stopped permission monitoring")
    }
    
    // MARK: - Permission Reset
    func resetAllPermissions() async -> Bool {
        do {
            PotterLogger.shared.info("permissions", "🔄 Resetting all permissions...")
            
            let bundleIdentifier = Bundle.main.bundleIdentifier ?? "com.potter.app"
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/tccutil")
            process.arguments = ["reset", "All", bundleIdentifier]
            
            try process.run()
            process.waitUntilExit()
            
            let success = process.terminationStatus == 0
            
            if success {
                PotterLogger.shared.info("permissions", "✅ Successfully reset all permissions")
                // Update status after reset
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    self.checkAllPermissions()
                }
            } else {
                PotterLogger.shared.error("permissions", "❌ Failed to reset permissions (exit code: \(process.terminationStatus))")
            }
            
            return success
        } catch {
            PotterLogger.shared.error("permissions", "❌ Error resetting permissions: \(error.localizedDescription)")
            return false
        }
    }
    
    // MARK: - Restart Management
    func promptForRestart() {
        let alert = NSAlert()
        alert.messageText = "Restart Required"
        alert.informativeText = "Some permission changes require Potter to be restarted to take effect. Would you like to restart now?"
        alert.addButton(withTitle: "Restart Now")
        alert.addButton(withTitle: "Restart Later")
        alert.alertStyle = .informational
        
        let response = alert.runModal()
        
        if response == .alertFirstButtonReturn {
            restartApplication()
        } else {
            PotterLogger.shared.info("permissions", "📝 User chose to restart later")
        }
    }
    
    private func restartApplication() {
        PotterLogger.shared.info("permissions", "🔄 Restarting Potter application...")
        
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/open")
        task.arguments = [Bundle.main.bundlePath]
        
        do {
            try task.run()
            NSApplication.shared.terminate(nil)
        } catch {
            PotterLogger.shared.error("permissions", "❌ Failed to restart: \(error.localizedDescription)")
            
            let alert = NSAlert()
            alert.messageText = "Restart Failed"
            alert.informativeText = "Please restart Potter manually for permission changes to take effect."
            alert.runModal()
        }
    }
    
    // MARK: - Status Helpers
    func getAllPermissions() -> [(PermissionType, PermissionStatus)] {
        return [
            (.accessibility, accessibilityStatus),
            (.notifications, notificationsStatus)
        ]
    }
    
    func forceStopChecking() {
        PotterLogger.shared.info("permissions", "🛑 Force stopping permission checking")
        stopPermissionMonitoring()
    }
    
    func hasRequiredPermissions() -> Bool {
        return accessibilityStatus == .granted
    }
    
    func getPermissionStatus(for type: PermissionType) -> PermissionStatus {
        switch type {
        case .accessibility: return accessibilityStatus
        case .notifications: return notificationsStatus
        }
    }
}
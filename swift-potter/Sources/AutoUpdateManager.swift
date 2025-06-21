import Foundation
import Sparkle

/**
 * AutoUpdateManager - Handles automatic updates for Potter using Sparkle framework
 * 
 * Features:
 * - Automatic update checking on startup
 * - Periodic update checks
 * - User-controlled update preferences
 * - Signature verification for security
 */
class AutoUpdateManager: NSObject {
    static let shared = AutoUpdateManager()
    
    private var updaterController: SPUStandardUpdaterController?
    private var updater: SPUUpdater?
    
    // Update configuration
    private let feedURL = "https://raw.githubusercontent.com/graydot/rephrasely/main/releases/appcast.xml"
    private let updateCheckInterval: TimeInterval = 60 * 60 * 24 // 24 hours
    
    private override init() {
        super.init()
        setupSparkleUpdater()
    }
    
    private func setupSparkleUpdater() {
        PotterLogger.shared.info("autoupdate", "🔄 Setting up Sparkle auto-updater...")
        
        // Create updater controller with minimal configuration
        // Let Sparkle use Info.plist settings to avoid configuration issues
        updaterController = SPUStandardUpdaterController(
            startingUpdater: false,  // Start manually to control initialization
            updaterDelegate: self,
            userDriverDelegate: nil
        )
        
        guard let controller = updaterController else {
            PotterLogger.shared.error("autoupdate", "❌ Failed to create Sparkle updater controller")
            return
        }
        
        updater = controller.updater
        
        // Use minimal configuration - let Info.plist handle most settings
        updater?.sendsSystemProfile = false
        
        // Start the updater after configuration
        controller.startUpdater()
        
        PotterLogger.shared.info("autoupdate", "✅ Sparkle auto-updater configured using Info.plist settings")
    }
    
    // MARK: - Public API
    
    /**
     * Check for updates manually (triggered by user)
     */
    func checkForUpdatesManually() {
        PotterLogger.shared.info("autoupdate", "🔍 Manual update check requested")
        updater?.checkForUpdates()
    }
    
    /**
     * Check for updates silently (background check)
     */
    func checkForUpdatesInBackground() {
        PotterLogger.shared.info("autoupdate", "🔍 Background update check")
        updater?.checkForUpdatesInBackground()
    }
    
    /**
     * Start automatic background update checks (no user alerts for errors)
     */
    func startBackgroundUpdateChecks() {
        guard let updater = updater else { return }
        
        // Use background checks to avoid user-facing error alerts
        if updater.automaticallyChecksForUpdates {
            PotterLogger.shared.info("autoupdate", "🔄 Starting background update checks")
            checkForUpdatesInBackground()
        }
    }
    
    /**
     * Enable or disable automatic update checking
     */
    func setAutoUpdateEnabled(_ enabled: Bool) {
        updater?.automaticallyChecksForUpdates = enabled
        UserDefaults.standard.set(enabled, forKey: "auto_update_enabled")
        PotterLogger.shared.info("autoupdate", "🔧 Auto-update \(enabled ? "enabled" : "disabled")")
    }
    
    /**
     * Get current auto-update preference
     */
    func getAutoUpdateEnabled() -> Bool {
        return UserDefaults.standard.object(forKey: "auto_update_enabled") as? Bool ?? true // Default to enabled
    }
    
    /**
     * Get current app version
     */
    func getCurrentVersion() -> String {
        return Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
    }
    
    /**
     * Get build number
     */
    func getBuildNumber() -> String {
        return Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "Unknown"
    }
    
    /**
     * Get last update check date
     */
    func getLastUpdateCheckDate() -> Date? {
        return updater?.lastUpdateCheckDate
    }
    
    // MARK: - Private Methods
    
    private func loadUpdatePreferences() {
        // Load preferences from UserDefaults and configure for gentle operation
        let autoUpdateEnabled = getAutoUpdateEnabled()
        updater?.automaticallyChecksForUpdates = autoUpdateEnabled
        
        PotterLogger.shared.info("autoupdate", "📋 Loaded update preferences: auto-update \(autoUpdateEnabled ? "enabled" : "disabled")")
    }
    
    /**
     * Schedule next update check
     */
    private func scheduleNextUpdateCheck() {
        // Sparkle handles this automatically, but we can add custom logic here
        PotterLogger.shared.debug("autoupdate", "⏰ Next update check scheduled by Sparkle")
    }
}

// MARK: - SPUUpdaterDelegate

extension AutoUpdateManager: SPUUpdaterDelegate {
    
    func updater(_ updater: SPUUpdater, mayPerform updateCheck: SPUUpdateCheck) -> Bool {
        PotterLogger.shared.info("autoupdate", "🔍 Sparkle requesting permission for update check")
        
        // Allow all update checks but log them for monitoring
        return true
    }
    
    func updater(_ updater: SPUUpdater, didFind validUpdate: SUAppcastItem) {
        PotterLogger.shared.info("autoupdate", "✨ Update found: \(validUpdate.displayVersionString)")
        if let releaseNotesURL = validUpdate.releaseNotesURL {
            PotterLogger.shared.info("autoupdate", "📝 Release notes: \(releaseNotesURL.absoluteString)")
        }
    }
    
    func updaterDidNotFindUpdate(_ updater: SPUUpdater) {
        PotterLogger.shared.info("autoupdate", "✅ No updates found - running latest version")
    }
    
    func updater(_ updater: SPUUpdater, didAbortWithError error: Error) {
        // Log the error silently - Sparkle framework may still show alerts
        PotterLogger.shared.warning("autoupdate", "⚠️ Update check failed: \(error.localizedDescription)")
        
        // For network errors, we don't want to bother the user
        // The error alert is handled by Sparkle's UI layer, not our delegate
    }
    
    func updater(_ updater: SPUUpdater, willInstallUpdate item: SUAppcastItem) {
        PotterLogger.shared.info("autoupdate", "📦 Installing update: \(item.displayVersionString)")
    }
    
    func updater(_ updater: SPUUpdater, didFinishLoading appcast: SUAppcast) {
        PotterLogger.shared.info("autoupdate", "📡 Successfully loaded appcast")
    }
    
    func updater(_ updater: SPUUpdater, failedToDownloadFileAtURL url: URL, withError error: Error) {
        PotterLogger.shared.error("autoupdate", "❌ Failed to download update from \(url): \(error.localizedDescription)")
    }
}

// MARK: - Update Notifications

extension AutoUpdateManager {
    
    /**
     * Show update notification to user
     */
    private func showUpdateNotification(version: String, releaseNotes: String?) {
        PotterLogger.shared.info("autoupdate", "📢 Showing update notification for version \(version)")
        
        // This is handled by Sparkle's built-in UI, but we can add custom logic here
        // For example, posting to notification center or updating menu bar
    }
    
    /**
     * Show update installation progress
     */
    private func showUpdateProgress() {
        PotterLogger.shared.info("autoupdate", "📊 Update installation in progress...")
    }
}

// MARK: - Version Comparison Utilities

extension AutoUpdateManager {
    
    /**
     * Compare version strings
     */
    func compareVersions(_ version1: String, _ version2: String) -> ComparisonResult {
        return version1.compare(version2, options: .numeric)
    }
    
    /**
     * Check if a version is newer than current
     */
    func isNewerVersion(_ version: String) -> Bool {
        let currentVersion = getCurrentVersion()
        return compareVersions(version, currentVersion) == .orderedDescending
    }
}
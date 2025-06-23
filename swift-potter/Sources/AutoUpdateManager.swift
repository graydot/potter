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
    private let feedURL = "https://raw.githubusercontent.com/graydot/potter/master/appcast.xml"
    private let updateCheckInterval: TimeInterval = 60 * 60 * 24 // 24 hours
    
    private override init() {
        super.init()
        setupSparkleUpdater()
    }
    
    private func setupSparkleUpdater() {
        // Check if we're running in development mode (swift run)
        if isRunningInDevelopmentMode() {
            PotterLogger.shared.info("autoupdate", "🚧 Development mode detected - skipping Sparkle auto-updater setup")
            return
        }
        
        // Check if we have Sparkle configuration in Info.plist
        guard let _ = Bundle.main.infoDictionary?["SUFeedURL"] as? String else {
            PotterLogger.shared.info("autoupdate", "⚠️  No Sparkle configuration found in Info.plist - skipping auto-updater setup")
            return
        }
        
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
    
    private func isRunningInDevelopmentMode() -> Bool {
        // Check if we're running from swift run (executable path contains .build)
        let executablePath = Bundle.main.executablePath ?? ""
        return executablePath.contains(".build") || 
               executablePath.contains("swift-potter") ||
               Bundle.main.bundlePath.hasSuffix(".build/debug") ||
               Bundle.main.bundlePath.hasSuffix(".build/release")
    }
    
    // MARK: - Public API
    
    /**
     * Check for updates manually (triggered by user)
     */
    func checkForUpdatesManually() {
        if updater == nil {
            PotterLogger.shared.info("autoupdate", "⚠️  Auto-updater not available (development mode or missing configuration)")
            return
        }
        PotterLogger.shared.info("autoupdate", "🔍 Manual update check requested")
        updater?.checkForUpdates()
    }
    
    /**
     * Check for updates silently (background check)
     */
    func checkForUpdatesInBackground() {
        if updater == nil {
            PotterLogger.shared.debug("autoupdate", "⚠️  Auto-updater not available (development mode or missing configuration)")
            return
        }
        PotterLogger.shared.info("autoupdate", "🔍 Background update check")
        updater?.checkForUpdatesInBackground()
    }
    
    /**
     * Schedule periodic automatic checks
     */
    func schedulePeriodicChecks() {
        PotterLogger.shared.info("autoupdate", "⏰ Periodic update checks enabled via Info.plist")
        // Sparkle handles this automatically via SUEnableAutomaticChecks in Info.plist
    }
    
    /**
     * Check if an update is available
     */
    func isUpdateAvailable() -> Bool {
        // This is a basic check - Sparkle handles the actual update logic
        return false // Real implementation would check Sparkle's state
    }
    
    /**
     * Get update information
     */
    func getUpdateInformation() -> String {
        return "Automatic updates managed by Sparkle"
    }
    
    func getCurrentVersion() -> String {
        return Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "2.0.2"
    }
    
    func getBuildNumber() -> String {
        return Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "2.0.2"
    }
    
    func getLastUpdateCheckDate() -> Date? {
        return updater?.lastUpdateCheckDate
    }
    
    func getAutoUpdateEnabled() -> Bool {
        return updater?.automaticallyChecksForUpdates ?? false
    }
    
    func setAutoUpdateEnabled(_ enabled: Bool) {
        updater?.automaticallyChecksForUpdates = enabled
    }
}

// MARK: - SPUUpdaterDelegate

extension AutoUpdateManager: SPUUpdaterDelegate {
    func feedURLString(for updater: SPUUpdater) -> String? {
        return feedURL
    }
    
    func updater(_ updater: SPUUpdater, willInstallUpdate item: SUAppcastItem) {
        PotterLogger.shared.info("autoupdate", "📦 Installing update: \(item.displayVersionString)")
    }
    
    func updaterDidNotFindUpdate(_ updater: SPUUpdater) {
        PotterLogger.shared.info("autoupdate", "✅ No updates available")
    }
    
    func updater(_ updater: SPUUpdater, didFindValidUpdate item: SUAppcastItem) {
        PotterLogger.shared.info("autoupdate", "🆕 Update available: \(item.displayVersionString)")
    }
    
    func updater(_ updater: SPUUpdater, didAbortWithError error: Error) {
        PotterLogger.shared.error("autoupdate", "❌ Update check failed: \(error.localizedDescription)")
    }
}
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
    private let feedURL = "https://raw.githubusercontent.com/graydot/potter/master/releases/appcast.xml"
    private let updateCheckInterval: TimeInterval = 60 * 60 * 24 // 24 hours
    
    private override init() {
        super.init()
        setupSparkleUpdater()
    }
    
    private func setupSparkleUpdater() {
        // Check if we're running in development mode (swift run)
        if isRunningInDevelopmentMode() {
            PotterLogger.shared.info("autoupdate", "🚧 Development mode detected - skipping Sparkle auto-updater setup")
            PotterLogger.shared.debug("autoupdate", "   Bundle path: \(Bundle.main.bundlePath)")
            PotterLogger.shared.debug("autoupdate", "   Executable path: \(Bundle.main.executablePath ?? "unknown")")
            return
        }
        
        // Check if we have Sparkle configuration in Info.plist
        guard let feedURL = Bundle.main.infoDictionary?["SUFeedURL"] as? String else {
            PotterLogger.shared.error("autoupdate", "❌ No SUFeedURL found in Info.plist - skipping auto-updater setup")
            PotterLogger.shared.debug("autoupdate", "   Available Info.plist keys: \(Bundle.main.infoDictionary?.keys.sorted() ?? [])")
            return
        }
        
        PotterLogger.shared.info("autoupdate", "🔄 Setting up Sparkle auto-updater...")
        PotterLogger.shared.info("autoupdate", "   Feed URL: \(feedURL)")
        PotterLogger.shared.info("autoupdate", "   Bundle ID: \(Bundle.main.bundleIdentifier ?? "unknown")")
        PotterLogger.shared.info("autoupdate", "   App Version: \(Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "unknown")")
        
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
        PotterLogger.shared.info("autoupdate", "✅ Sparkle updater controller created")
        
        // Log current configuration
        PotterLogger.shared.info("autoupdate", "   Automatic checks enabled: \(updater?.automaticallyChecksForUpdates ?? false)")
        PotterLogger.shared.info("autoupdate", "   Check interval: \(updater?.updateCheckInterval ?? 0) seconds")
        PotterLogger.shared.info("autoupdate", "   Last check: \(updater?.lastUpdateCheckDate?.description ?? "never")")
        
        // Use minimal configuration - let Info.plist handle most settings
        updater?.sendsSystemProfile = false
        
        // Start the updater after configuration
        PotterLogger.shared.info("autoupdate", "🚀 Starting Sparkle updater...")
        controller.startUpdater()
        
        PotterLogger.shared.info("autoupdate", "✅ Sparkle auto-updater configured and started")
        
        // Schedule an initial background check after startup
        DispatchQueue.main.asyncAfter(deadline: .now() + 10.0) {
            PotterLogger.shared.info("autoupdate", "🔍 Performing initial background update check...")
            self.checkForUpdatesInBackground()
        }
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
        PotterLogger.shared.info("autoupdate", "   Current version: \(getCurrentVersion())")
        PotterLogger.shared.info("autoupdate", "   Feed URL: \(feedURL)")
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
        PotterLogger.shared.info("autoupdate", "🔍 Background update check starting...")
        PotterLogger.shared.info("autoupdate", "   Current version: \(getCurrentVersion())")
        PotterLogger.shared.info("autoupdate", "   Feed URL: \(feedURL)")
        PotterLogger.shared.info("autoupdate", "   Last check: \(updater?.lastUpdateCheckDate?.description ?? "never")")
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
        PotterLogger.shared.debug("autoupdate", "🔗 Sparkle requesting feed URL: \(feedURL)")
        return feedURL
    }
    
    func updater(_ updater: SPUUpdater, willInstallUpdate item: SUAppcastItem) {
        PotterLogger.shared.info("autoupdate", "📦 Installing update: \(item.displayVersionString)")
        PotterLogger.shared.info("autoupdate", "   Update URL: \(item.fileURL?.absoluteString ?? "unknown")")
        PotterLogger.shared.info("autoupdate", "   Update size: \(item.contentLength) bytes")
    }
    
    func updaterDidNotFindUpdate(_ updater: SPUUpdater) {
        PotterLogger.shared.info("autoupdate", "✅ No updates available")
        PotterLogger.shared.info("autoupdate", "   Current version: \(getCurrentVersion()) is up to date")
        PotterLogger.shared.info("autoupdate", "   Feed checked: \(feedURL)")
    }
    
    func updater(_ updater: SPUUpdater, didFindValidUpdate item: SUAppcastItem) {
        PotterLogger.shared.info("autoupdate", "🆕 Update available: \(item.displayVersionString)")
        PotterLogger.shared.info("autoupdate", "   Current version: \(getCurrentVersion())")
        PotterLogger.shared.info("autoupdate", "   New version: \(item.displayVersionString)")
        PotterLogger.shared.info("autoupdate", "   Download URL: \(item.fileURL?.absoluteString ?? "unknown")")
        PotterLogger.shared.info("autoupdate", "   Release notes: \(item.itemDescription ?? "none")")
    }
    
    func updater(_ updater: SPUUpdater, didAbortWithError error: Error) {
        PotterLogger.shared.error("autoupdate", "❌ Update check failed: \(error.localizedDescription)")
        PotterLogger.shared.error("autoupdate", "   Error domain: \(error._domain)")
        PotterLogger.shared.error("autoupdate", "   Error code: \(error._code)")
        PotterLogger.shared.error("autoupdate", "   Feed URL: \(feedURL)")
    }
    
    func updaterDidFinishDownloadingUpdate(_ updater: SPUUpdater, downloadPath: String, updateItem: SUAppcastItem) {
        PotterLogger.shared.info("autoupdate", "📥 Update downloaded successfully")
        PotterLogger.shared.info("autoupdate", "   Downloaded to: \(downloadPath)")
        PotterLogger.shared.info("autoupdate", "   Update version: \(updateItem.displayVersionString)")
    }
    
    func updater(_ updater: SPUUpdater, failedToDownloadUpdate item: SUAppcastItem, error: Error) {
        PotterLogger.shared.error("autoupdate", "📥 Failed to download update: \(error.localizedDescription)")
        PotterLogger.shared.error("autoupdate", "   Update version: \(item.displayVersionString)")
        PotterLogger.shared.error("autoupdate", "   Download URL: \(item.fileURL?.absoluteString ?? "unknown")")
    }
    
    func updaterWillRelaunchApplication(_ updater: SPUUpdater) {
        PotterLogger.shared.info("autoupdate", "🔄 Application will relaunch to complete update")
    }
}
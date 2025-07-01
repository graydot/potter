import AppKit
import Foundation

// Main entry point - using traditional approach for Swift CLI apps
let app = NSApplication.shared
app.setActivationPolicy(.accessory) // Menu bar app

// Set custom app icon for dock (when settings window opens)
if let iconURL = Bundle.potterResources.url(forResource: "potter-icon-512", withExtension: "png", subdirectory: "Resources/AppIcon"),
   let appIcon = NSImage(contentsOf: iconURL) {
    app.applicationIconImage = appIcon
}

let delegate = AppDelegate()
app.delegate = delegate

print("🎭 Potter.ai: Copy → Enhance → Paste")
print("Starting Swift version...")

app.run()

class AppDelegate: NSObject, NSApplicationDelegate {
    var potterCore: PotterCore?
    var menuBarManager: MenuBarManager?
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Check for duplicate processes first
        if !checkForDuplicateProcesses() {
            return // Exit if user chose to exit this process
        }
        
        setupEditMenu() // This is the key fix for keyboard shortcuts!
        setupCore()
        setupMenuBar()
        setupAutoUpdater()
        checkAndShowSettingsIfNeeded()
    }
    
    // MARK: - Edit Menu Setup (Fixes keyboard shortcuts in modals)
    private func setupEditMenu() {
        let mainMenu = NSMenu()
        NSApp.mainMenu = mainMenu
        
        // App menu
        let appMenuItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenuItem.submenu = appMenu
        mainMenu.addItem(appMenuItem)
        
        appMenu.addItem(NSMenuItem(title: "Quit Potter", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        
        // Edit menu - THIS IS THE CRUCIAL PART
        let editMenuItem = NSMenuItem()
        let editMenu = NSMenu(title: "Edit")
        editMenuItem.submenu = editMenu
        mainMenu.addItem(editMenuItem)
        
        // Undo/Redo first
        editMenu.addItem(NSMenuItem(title: "Undo", action: Selector(("undo:")), keyEquivalent: "z"))
        let redoItem = NSMenuItem(title: "Redo", action: Selector(("redo:")), keyEquivalent: "z")
        redoItem.keyEquivalentModifierMask = [.command, .shift]
        editMenu.addItem(redoItem)
        
        editMenu.addItem(NSMenuItem.separator())
        
        // Standard text editing
        editMenu.addItem(NSMenuItem(title: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x"))
        editMenu.addItem(NSMenuItem(title: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c"))
        editMenu.addItem(NSMenuItem(title: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v"))
        
        editMenu.addItem(NSMenuItem.separator())
        editMenu.addItem(NSMenuItem(title: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a"))
    }
    
    private func checkForDuplicateProcesses() -> Bool {
        let processManager = ProcessManager.shared
        let result = processManager.checkForDuplicateProcesses()
        
        switch result {
        case .noDuplicates:
            return true
            
        case .foundDuplicates(let otherProcesses):
            let action = processManager.showDuplicateProcessDialog(otherProcesses: otherProcesses)
            
            switch action {
            case .killOthersAndContinue:
                var allKilled = true
                for process in otherProcesses {
                    if !processManager.killProcess(pid: process.pid) {
                        allKilled = false
                    }
                }
                
                if allKilled {
                    PotterLogger.shared.info("startup", "✅ All other processes terminated, continuing...")
                    return true
                } else {
                    showAlert(title: "Failed to Kill Processes", 
                             message: "Could not terminate all other Potter processes. Exiting for safety.")
                    NSApplication.shared.terminate(nil)
                    return false
                }
                
            case .exitThisProcess:
                PotterLogger.shared.info("startup", "👋 User chose to exit this process")
                NSApplication.shared.terminate(nil)
                return false
            }
        }
    }
    
    
    private func setupMenuBar() {
        guard let potterCore = potterCore else {
            PotterLogger.shared.error("startup", "❌ Cannot setup menu bar - PotterCore is nil")
            return
        }
        
        // Ensure PromptService is fully loaded before creating menu
        PotterLogger.shared.debug("startup", "⏳ Ensuring PromptService is loaded...")
        PromptService.shared.loadPrompts()
        PotterLogger.shared.debug("startup", "📋 PromptService loaded with \(PromptService.shared.prompts.count) prompts")
        
        menuBarManager = MenuBarManager(potterCore: potterCore)
        potterCore.iconDelegate = menuBarManager
    }
    
    
    
    
    
    
    
    private func setupCore() {
        potterCore = PotterCore()
        potterCore?.setup()
    }
    
    private func setupAutoUpdater() {
        PotterLogger.shared.info("startup", "🔄 Setting up auto-updater with proper Info.plist configuration...")
        
        // Initialize auto-updater with Info.plist configuration
        _ = AutoUpdateManager.shared
        
        PotterLogger.shared.info("startup", "✅ Auto-updater initialized")
    }
    
    private func checkAndShowSettingsIfNeeded() {
        if !hasValidProviderConfiguration() {
            PotterLogger.shared.info("startup", "📋 No valid provider configuration, showing settings dialog")
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.showSettingsUntilSelectedProviderHasKey()
            }
        } else {
            PotterLogger.shared.debug("startup", "✅ Valid provider configuration found, settings dialog will remain hidden")
        }
    }
    
    private func hasValidProviderConfiguration() -> Bool {
        // Get the currently selected LLM provider
        guard let selectedProviderString = UserDefaults.standard.string(forKey: "llm_provider"),
              let selectedProvider = LLMProvider(rawValue: selectedProviderString.lowercased()) else {
            PotterLogger.shared.debug("startup", "❌ No provider selected or invalid provider")
            return false
        }
        
        // Check if the selected provider has a validated API key
        let hasKey = StorageAdapter.shared.hasAPIKey(for: selectedProvider)
        PotterLogger.shared.debug("startup", "🔍 Provider: \(selectedProvider.displayName), has validated key: \(hasKey)")
        
        return hasKey
    }
    
    private func showSettingsUntilSelectedProviderHasKey() {
        showSettings()
    }
    
    
    
    
    func applicationWillTerminate(_ notification: Notification) {
        ProcessManager.shared.removeLockFile()
        PotterLogger.shared.info("startup", "👋 Potter shutting down...")
    }
    
    @objc func showSettings() {
        print("📋 Settings menu clicked!")
        ModernSettingsWindowController.shared.showWindow(nil)
    }
    
    private func showAlert(title: String, message: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.addButton(withTitle: "OK")
        
        // Add custom Potter icon to the alert
        if let iconURL = Bundle.potterResources.url(forResource: "potter-alert-icon", withExtension: "png", subdirectory: "Resources/AppIcon"),
           let alertIcon = NSImage(contentsOf: iconURL) {
            alert.icon = alertIcon
        }
        
        alert.runModal()
    }
}

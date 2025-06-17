import AppKit
import Foundation

// Main entry point - using traditional approach for Swift CLI apps
let app = NSApplication.shared
app.setActivationPolicy(.accessory) // Menu bar app

let delegate = AppDelegate()
app.delegate = delegate

print("🎭 Potter - AI Text Processing Tool")
print("Starting Swift version...")

app.run()

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem?
    var potterCore: PotterCore?
    var menuUpdateTimer: Timer?
    var currentPromptName: String = "summarize" // Default prompt
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Check for duplicate processes first
        if !checkForDuplicateProcesses() {
            return // Exit if user chose to exit this process
        }
        
        loadSavedPromptSelection()
        setupMenuBar()
        setupCore()
        requestAccessibilityPermissions()
        checkAndShowSettingsIfNeeded()
        startMenuUpdateTimer()
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
    
    private func loadSavedPromptSelection() {
        if let savedPrompt = UserDefaults.standard.string(forKey: "current_prompt") {
            currentPromptName = savedPrompt
        }
    }
    
    private func startMenuUpdateTimer() {
        // Update menu every 30 seconds to reflect permission changes
        menuUpdateTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.updateMenu()
            }
        }
    }
    
    private func setupMenuBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        
        if let button = statusItem?.button {
            button.image = NSImage(systemSymbolName: "wand.and.stars", accessibilityDescription: "Potter")
            button.toolTip = "Potter - AI Text Processing"
        }
        
        setupMenu()
    }
    
    private func setupMenu() {
        Task { @MainActor in
            updateMenu() // Use dynamic menu that updates with permission status
        }
    }
    
    @MainActor
    private func updateMenu() {
        let menu = NSMenu()
        
        let processItem = NSMenuItem(title: "Process Text (⌘⇧R)", action: #selector(processText), keyEquivalent: "")
        processItem.target = self
        menu.addItem(processItem)
        
        // Permission status items (right below Process Text)
        addPermissionMenuItems(to: menu)
        
        menu.addItem(NSMenuItem.separator())
        
        // Dynamic Prompts at first level (no submenu)
        addPromptsToMenu(menu)
        
        menu.addItem(NSMenuItem.separator())
        let settingsItem = NSMenuItem(title: "Preferences...", action: #selector(showSettings), keyEquivalent: ",")
        settingsItem.target = self
        menu.addItem(settingsItem)
        
        menu.addItem(NSMenuItem.separator())
        let quitItem = NSMenuItem(title: "Quit Potter", action: #selector(quit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)
        
        statusItem?.menu = menu
    }
    
    @MainActor
    private func addPermissionMenuItems(to menu: NSMenu) {
        let permissionManager = PermissionManager.shared
        permissionManager.checkAllPermissions()
        
        for permission in PermissionType.allCases {
            let status = permissionManager.getPermissionStatus(for: permission)
            let statusIcon = getStatusIcon(for: status)
            let title = "\(statusIcon) \(permission.displayName): \(status.displayText)"
            
            let item = NSMenuItem(title: title, action: #selector(openPermissionSettings(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = permission
            
            menu.addItem(item)
        }
    }
    
    private func getStatusIcon(for status: PermissionStatus) -> String {
        switch status {
        case .granted: return "🟢" // green circle
        case .denied: return "🔴" // red circle  
        case .notDetermined: return "🟡" // yellow circle
        case .unknown: return "⚪" // white circle
        }
    }
    
    private func setupCore() {
        potterCore = PotterCore()
        potterCore?.setup()
    }
    
    private func checkAndShowSettingsIfNeeded() {
        // Check if any API key is configured by checking UserDefaults directly
        let hasOpenAIKey = !(UserDefaults.standard.string(forKey: "api_key_openai") ?? "").isEmpty
        let hasAnthropicKey = !(UserDefaults.standard.string(forKey: "api_key_anthropic") ?? "").isEmpty
        let hasGoogleKey = !(UserDefaults.standard.string(forKey: "api_key_google") ?? "").isEmpty
        
        let hasAnyAPIKey = hasOpenAIKey || hasAnthropicKey || hasGoogleKey
        
        if !hasAnyAPIKey {
            // No API key found, show settings
            PotterLogger.shared.info("startup", "📋 No API key configured, showing settings dialog")
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.showSettings()
            }
        } else {
            PotterLogger.shared.info("startup", "✅ API key found, settings dialog will remain hidden")
        }
    }
    
    private func requestAccessibilityPermissions() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue(): true]
        let trusted = AXIsProcessTrustedWithOptions(options as CFDictionary)
        
        if !trusted {
            showAlert(
                title: "Accessibility Permission Required",
                message: "Potter needs accessibility permissions to capture global hotkeys. Please grant permission in System Settings."
            )
        }
    }
    
    @objc func processText() {
        potterCore?.processClipboardText()
    }
    
    private func addPromptsToMenu(_ menu: NSMenu) {
        // Load prompts from JSON
        let prompts = PromptManager.shared.loadPrompts()
        
        for prompt in prompts {
            let isSelected = prompt.name == currentPromptName
            let title = isSelected ? "✓ \(prompt.name.capitalized)" : "  \(prompt.name.capitalized)"
            
            let promptItem = NSMenuItem(title: title, action: #selector(selectPrompt(_:)), keyEquivalent: "")
            promptItem.target = self
            promptItem.representedObject = prompt.name
            menu.addItem(promptItem)
        }
    }
    
    @objc func selectPrompt(_ sender: NSMenuItem) {
        guard let promptName = sender.representedObject as? String else { return }
        currentPromptName = promptName
        
        // Save selection to UserDefaults
        UserDefaults.standard.set(promptName, forKey: "current_prompt")
        
        // Update the menu to show new selection
        Task { @MainActor in
            updateMenu()
        }
        
        PotterLogger.shared.info("menu", "📝 Selected prompt: \(promptName)")
    }
    
    @objc func showSettings() {
        print("📋 Settings menu clicked!")
        ModernSettingsWindowController.shared.showWindow(nil)
    }
    
    @objc func openPermissionSettings(_ sender: NSMenuItem) {
        guard let permission = sender.representedObject as? PermissionType else { return }
        
        Task { @MainActor in
            let permissionManager = PermissionManager.shared
            permissionManager.openSystemSettings(for: permission)
        }
    }
    
    @objc func quit() {
        ProcessManager.shared.removeLockFile()
        NSApplication.shared.terminate(nil)
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        ProcessManager.shared.removeLockFile()
        PotterLogger.shared.info("startup", "👋 Potter shutting down...")
    }
    
    private func showAlert(title: String, message: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
}

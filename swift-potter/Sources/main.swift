import AppKit
import Foundation

// Main entry point - using traditional approach for Swift CLI apps
let app = NSApplication.shared
app.setActivationPolicy(.accessory) // Menu bar app

// Set custom app icon for dock (when settings window opens)
if let iconURL = Bundle.module.url(forResource: "potter-icon-512", withExtension: "png", subdirectory: "Resources/AppIcon"),
   let appIcon = NSImage(contentsOf: iconURL) {
    app.applicationIconImage = appIcon
}

let delegate = AppDelegate()
app.delegate = delegate

print("🎭 Potter - AI Text Processing Tool")
print("Starting Swift version...")

app.run()

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem?
    var potterCore: PotterCore!
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
            updateMenuBarIcon()
            button.toolTip = "Potter - AI Text Processing"
        }
        
        setupMenu()
        
        // Listen for appearance changes to update icon
        DistributedNotificationCenter.default.addObserver(
            forName: Notification.Name("AppleInterfaceThemeChangedNotification"),
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.updateMenuBarIcon()
        }
    }
    
    private func updateMenuBarIcon() {
        guard let button = statusItem?.button else { return }
        
        // Determine if we're in dark mode
        let isDarkMode = NSApp.effectiveAppearance.name == .darkAqua
        
        // Create the cauldron icon programmatically
        let iconImage = createCauldronIcon(forDarkMode: isDarkMode)
        iconImage.isTemplate = true // This makes it adapt to menu bar appearance automatically
        button.image = iconImage
        
        PotterLogger.shared.debug("ui", "🎨 Updated menu bar icon for \(isDarkMode ? "dark" : "light") mode")
    }
    
    private func createCauldronIcon(forDarkMode isDarkMode: Bool) -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)
        
        image.lockFocus()
        
        // Use appropriate color for the theme
        let color = NSColor.controlAccentColor
        color.setFill()
        color.setStroke()
        
        // Scale everything down to fit in 18x18
        let scale: CGFloat = 0.8
        let offsetX: CGFloat = (18 * (1 - scale)) / 2
        let offsetY: CGFloat = (18 * (1 - scale)) / 2
        
        // Draw magical particles (small squares)
        let particles = [
            NSRect(x: 8 + offsetX, y: 15 + offsetY, width: 1.5, height: 1.5),
            NSRect(x: 6 + offsetX, y: 13 + offsetY, width: 1.5, height: 1.5),
            NSRect(x: 10 + offsetX, y: 13.5 + offsetY, width: 1, height: 1),
            NSRect(x: 9 + offsetX, y: 12 + offsetY, width: 1, height: 1),
            NSRect(x: 5 + offsetX, y: 11 + offsetY, width: 1, height: 1),
        ]
        
        for particle in particles {
            NSBezierPath(roundedRect: particle, xRadius: 0.5, yRadius: 0.5).fill()
        }
        
        // Draw cauldron body (rounded bottom)
        let cauldronBody = NSBezierPath()
        cauldronBody.move(to: NSPoint(x: 4 + offsetX, y: 8 + offsetY))
        cauldronBody.line(to: NSPoint(x: 4 + offsetX, y: 6 + offsetY))
        cauldronBody.curve(to: NSPoint(x: 14 + offsetX, y: 6 + offsetY), 
                          controlPoint1: NSPoint(x: 4 + offsetX, y: 3 + offsetY), 
                          controlPoint2: NSPoint(x: 14 + offsetX, y: 3 + offsetY))
        cauldronBody.line(to: NSPoint(x: 14 + offsetX, y: 8 + offsetY))
        cauldronBody.lineWidth = 1.5
        cauldronBody.stroke()
        
        // Draw cauldron rim (ellipse)
        let rim = NSBezierPath(ovalIn: NSRect(x: 3.5 + offsetX, y: 7.5 + offsetY, width: 11, height: 2))
        rim.fill()
        
        // Draw cauldron legs (small circles)
        let leg1 = NSBezierPath(ovalIn: NSRect(x: 5 + offsetX, y: 1 + offsetY, width: 1.5, height: 1.5))
        let leg2 = NSBezierPath(ovalIn: NSRect(x: 8.5 + offsetX, y: 1 + offsetY, width: 1.5, height: 1.5))
        let leg3 = NSBezierPath(ovalIn: NSRect(x: 12 + offsetX, y: 1 + offsetY, width: 1.5, height: 1.5))
        
        leg1.fill()
        leg2.fill()
        leg3.fill()
        
        // Draw handle (small rectangle)
        let handle = NSRect(x: 9 + offsetX, y: 6.5 + offsetY, width: 0.8, height: 2)
        NSColor.white.setFill()
        NSBezierPath(rect: handle).fill()
        
        image.unlockFocus()
        
        return image
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
        potterCore.setup()
    }
    
    private func checkAndShowSettingsIfNeeded() {
        // Check if any API key is configured by checking UserDefaults directly
        let hasOpenAIKey = !(UserDefaults.standard.string(forKey: "api_key_openai") ?? "").isEmpty
        let hasAnthropicKey = !(UserDefaults.standard.string(forKey: "api_key_anthropic") ?? "").isEmpty
        let hasGoogleKey = !(UserDefaults.standard.string(forKey: "api_key_google") ?? "").isEmpty
        
        let hasAnyAPIKey = hasOpenAIKey || hasAnthropicKey || hasGoogleKey
        
        if !hasAnyAPIKey {
            // No API key found, show settings and keep open until one is added
            PotterLogger.shared.info("startup", "📋 No API key configured, showing settings dialog")
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.showSettingsUntilAPIKey()
            }
        } else {
            PotterLogger.shared.debug("startup", "✅ API key found, settings dialog will remain hidden")
        }
    }
    
    private func showSettingsUntilAPIKey() {
        showSettings()
        
        // Start monitoring for API keys (check UserDefaults directly to avoid actor issues)
        Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { timer in
            let hasOpenAIKey = !(UserDefaults.standard.string(forKey: "api_key_openai") ?? "").isEmpty
            let hasAnthropicKey = !(UserDefaults.standard.string(forKey: "api_key_anthropic") ?? "").isEmpty
            let hasGoogleKey = !(UserDefaults.standard.string(forKey: "api_key_google") ?? "").isEmpty
            
            let hasAnyAPIKey = hasOpenAIKey || hasAnthropicKey || hasGoogleKey
            
            PotterLogger.shared.debug("startup", "🔍 Checking API keys: OpenAI=\(hasOpenAIKey), Anthropic=\(hasAnthropicKey), Google=\(hasGoogleKey)")
            
            if hasAnyAPIKey {
                // We have an API key, can close settings
                timer.invalidate()
                PotterLogger.shared.debug("startup", "✅ API key detected, allowing settings to close")
                
                // Close settings window if it's still open
                DispatchQueue.main.async {
                    ModernSettingsWindowController.shared.close()
                }
            }
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
        PotterLogger.shared.info("hotkey", "🎯 Global hotkey triggered (⌘⇧R)")
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
        
        // Add custom Potter icon to the alert
        if let iconURL = Bundle.module.url(forResource: "potter-alert-icon", withExtension: "png", subdirectory: "Resources/AppIcon"),
           let alertIcon = NSImage(contentsOf: iconURL) {
            alert.icon = alertIcon
        }
        
        alert.runModal()
    }
}

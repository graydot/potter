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

class AppDelegate: NSObject, NSApplicationDelegate, IconStateDelegate {
    var statusItem: NSStatusItem?
    var potterCore: PotterCore?
    var menuUpdateTimer: Timer?
    var currentPromptName: String = "summarize" // Default prompt
    var currentMenu: NSMenu?
    
    // Icon state management
    enum IconState {
        case normal
        case processing
        case success
        case error
    }
    private var currentIconState: IconState = .normal
    private var spinnerTimer: Timer?
    private var spinnerRotation: CGFloat = 0
    private var currentErrorMessage: String = ""
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Check for duplicate processes first
        if !checkForDuplicateProcesses() {
            return // Exit if user chose to exit this process
        }
        
        setupEditMenu() // This is the key fix for keyboard shortcuts!
        loadSavedPromptSelection()
        setupMenuBar()
        setupCore()
        setupAutoUpdater()
        requestAccessibilityPermissions()
        checkAndShowSettingsIfNeeded()
        startMenuUpdateTimer()
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
        let iconImage = createCauldronIcon(forDarkMode: isDarkMode, state: currentIconState)
        iconImage.isTemplate = (currentIconState == .normal) // Only use template for normal state
        button.image = iconImage
        
        PotterLogger.shared.debug("ui", "🎨 Updated menu bar icon for \(isDarkMode ? "dark" : "light") mode, state: \(currentIconState)")
    }
    
    // Public methods to update icon state
    func setProcessingState() {
        currentIconState = .processing
        currentErrorMessage = "" // Clear any error message
        updateMenuBarIcon()
        startSpinnerAnimation()
        
        // Update menu to remove error message
        Task { @MainActor in
            updateMenu()
        }
    }
    
    func setSuccessState() {
        currentIconState = .success
        stopSpinnerAnimation()
        updateMenuBarIcon()
        
        // Automatically return to normal after 5 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) {
            self.setNormalState()
        }
    }
    
    func setNormalState() {
        currentIconState = .normal
        currentErrorMessage = ""
        stopSpinnerAnimation()
        updateMenuBarIcon()
        
        // Update menu to remove error message
        Task { @MainActor in
            updateMenu()
        }
    }
    
    func setErrorState(message: String) {
        currentIconState = .error
        currentErrorMessage = message
        stopSpinnerAnimation()
        updateMenuBarIcon()
        
        // Update menu to show error message
        Task { @MainActor in
            updateMenu()
        }
        
        // Automatically return to normal after 10 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 10.0) {
            if self.currentIconState == .error {
                self.setNormalState()
            }
        }
    }
    
    private func startSpinnerAnimation() {
        spinnerTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            if self?.currentIconState == .processing {
                self?.spinnerRotation -= 30 // Rotate 30 degrees each frame (opposite direction)
                if self?.spinnerRotation ?? 0 <= -360 {
                    self?.spinnerRotation = 0
                }
                self?.updateMenuBarIcon()
            }
        }
    }
    
    private func stopSpinnerAnimation() {
        spinnerTimer?.invalidate()
        spinnerTimer = nil
    }
    
    private func createCauldronIcon(forDarkMode isDarkMode: Bool, state: IconState = .normal) -> NSImage {
        switch state {
        case .normal:
            // Use image files for normal state
            return loadMenuBarIcon(forDarkMode: isDarkMode)
        case .processing:
            // Draw yellow animated spinner
            return createSpinnerIcon()
        case .success:
            // Draw green success dot
            return createStatusIcon(color: .systemGreen)
        case .error:
            // Draw red error dot
            return createStatusIcon(color: .systemRed)
        }
    }
    
    private func loadMenuBarIcon(forDarkMode isDarkMode: Bool) -> NSImage {
        // Try to load from Resources bundle
        let iconName = isDarkMode ? "menubar-icon-dark-18" : "menubar-icon-light-18"
        
        if let iconURL = Bundle.module.url(forResource: iconName, withExtension: "png", subdirectory: "Resources"),
           let image = NSImage(contentsOf: iconURL) {
            image.size = NSSize(width: 18, height: 18)
            return image
        }
        
        // Fallback: try @2x version and scale down
        let iconName2x = isDarkMode ? "menubar-icon-dark-18@2x" : "menubar-icon-light-18@2x"
        if let iconURL = Bundle.module.url(forResource: iconName2x, withExtension: "png", subdirectory: "Resources"),
           let image = NSImage(contentsOf: iconURL) {
            image.size = NSSize(width: 18, height: 18)
            return image
        }
        
        // Final fallback: use template icon and let system handle theming
        if let iconURL = Bundle.module.url(forResource: "menubar-icon-template", withExtension: "png", subdirectory: "Resources"),
           let image = NSImage(contentsOf: iconURL) {
            image.size = NSSize(width: 18, height: 18)
            image.isTemplate = true  // Let system handle light/dark theming
            return image
        }
        
        // Ultimate fallback: create programmatically (keep old code as backup)
        return createFallbackIcon(forDarkMode: isDarkMode)
    }
    
    private func createSpinnerIcon() -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)
        
        image.lockFocus()
        drawSpinner()
        image.unlockFocus()
        
        return image
    }
    
    private func createStatusIcon(color: NSColor) -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)
        
        image.lockFocus()
        color.setFill()
        let dotRect = NSRect(x: 2, y: 2, width: 14, height: 14)
        let dot = NSBezierPath(ovalIn: dotRect)
        dot.fill()
        image.unlockFocus()
        
        return image
    }
    
    private func createFallbackIcon(forDarkMode isDarkMode: Bool) -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)
        
        image.lockFocus()
        drawCauldronIcon(isDarkMode: isDarkMode, size: size)
        image.unlockFocus()
        
        return image
    }
    
    private func drawCauldronIcon(isDarkMode: Bool, size: NSSize) {
        // Use appropriate colors for light/dark mode
        let potColor: NSColor
        let steamColor: NSColor
        let handleColor: NSColor
        
        if isDarkMode {
            // White pot for dark mode
            potColor = NSColor.white
            steamColor = NSColor.lightGray
            handleColor = NSColor.lightGray
        } else {
            // Black pot for light mode
            potColor = NSColor.black
            steamColor = NSColor.darkGray
            handleColor = NSColor.darkGray
        }
        
        // Scale everything down to fit in 18x18
        let scale: CGFloat = 0.9
        let offsetX: CGFloat = (18 * (1 - scale)) / 2
        let offsetY: CGFloat = (18 * (1 - scale)) / 2
        
        // Draw steam particles (small circles)
        steamColor.setFill()
        let steamParticles = [
            NSRect(x: 7 + offsetX, y: 3 + offsetY, width: 1, height: 1),
            NSRect(x: 9 + offsetX, y: 2.5 + offsetY, width: 0.8, height: 0.8),
            NSRect(x: 11 + offsetX, y: 3.5 + offsetY, width: 0.7, height: 0.7),
        ]
        
        for particle in steamParticles {
            NSBezierPath(ovalIn: particle).fill()
        }
        
        // Draw main pot body (ellipse)
        potColor.setFill()
        let potBody = NSBezierPath(ovalIn: NSRect(x: 4 + offsetX, y: 6.5 + offsetY, width: 10, height: 7))
        potBody.fill()
        
        // Draw pot rim (darker ellipse)
        let rimColor = isDarkMode ? NSColor.lightGray : NSColor.darkGray
        rimColor.setFill()
        let rim = NSBezierPath(ovalIn: NSRect(x: 3.5 + offsetX, y: 6 + offsetY, width: 11, height: 2.4))
        rim.fill()
        
        // Draw pot spout
        let spout = NSBezierPath(ovalIn: NSRect(x: 13 + offsetX, y: 6.8 + offsetY, width: 3, height: 1.6))
        spout.fill()
        
        // Draw pot base
        let baseColor = isDarkMode ? NSColor.gray : NSColor.black
        baseColor.setFill()
        let base = NSBezierPath(ovalIn: NSRect(x: 5 + offsetX, y: 13 + offsetY, width: 8, height: 1.6))
        base.fill()
        
        // Draw handle (simple rectangle)
        handleColor.setFill()
        let handle = NSRect(x: 14.5 + offsetX, y: 8 + offsetY, width: 1, height: 4)
        NSBezierPath(rect: handle).fill()
    }
    
    private func drawSpinner() {
        let center = NSPoint(x: 9, y: 9)
        let radius: CGFloat = 7.5 // Make it bigger
        
        // Save current graphics state
        NSGraphicsContext.current?.saveGraphicsState()
        
        // Apply rotation transform around center
        let transform = NSAffineTransform()
        transform.translateX(by: center.x, yBy: center.y)
        transform.rotate(byDegrees: spinnerRotation)
        transform.translateX(by: -center.x, yBy: -center.y)
        transform.concat()
        
        NSColor.systemYellow.setFill()
        
        // Draw spinner segments with varying opacity
        let numberOfSegments = 8
        for i in 0..<numberOfSegments {
            let angle = CGFloat(i) * 360.0 / CGFloat(numberOfSegments)
            let opacity = 1.0 - (CGFloat(i) / CGFloat(numberOfSegments)) * 0.8
            
            NSColor.systemYellow.withAlphaComponent(opacity).setFill()
            
            let segmentPath = NSBezierPath()
            segmentPath.move(to: center)
            
            let startAngle = angle - 15
            let endAngle = angle + 15
            
            let startPoint = NSPoint(
                x: center.x + cos(startAngle * .pi / 180) * radius,
                y: center.y + sin(startAngle * .pi / 180) * radius
            )
            
            segmentPath.line(to: startPoint)
            segmentPath.appendArc(withCenter: center, radius: radius, startAngle: startAngle, endAngle: endAngle)
            segmentPath.close()
            segmentPath.fill()
        }
        
        // Restore graphics state
        NSGraphicsContext.current?.restoreGraphicsState()
    }
    
    private func setupMenu() {
        Task { @MainActor in
            updateMenu() // Use dynamic menu that updates with permission status
        }
    }
    
    @MainActor
    private func updateMenu() {
        let menu = NSMenu()
        
        let processItem = NSMenuItem(title: "Process Text (⌘⇧9)", action: #selector(processText), keyEquivalent: "")
        processItem.target = self
        menu.addItem(processItem)
        
        // Show error message if in error state
        if currentIconState == .error && !currentErrorMessage.isEmpty {
            menu.addItem(NSMenuItem.separator())
            let errorItem = NSMenuItem(title: "🔴 \(currentErrorMessage)", action: #selector(clearError), keyEquivalent: "")
            errorItem.target = self
            menu.addItem(errorItem)
            menu.addItem(NSMenuItem.separator())
        }
        
        // Permission status items (right below Process Text or error)
        addPermissionMenuItems(to: menu)
        
        menu.addItem(NSMenuItem.separator())
        
        // Dynamic Prompts at first level (no submenu)
        addPromptsToMenu(menu)
        
        menu.addItem(NSMenuItem.separator())
        let settingsItem = NSMenuItem(title: "Preferences...", action: #selector(showSettings), keyEquivalent: ",")
        settingsItem.target = self
        menu.addItem(settingsItem)
        
        let updateItem = NSMenuItem(title: "Check for Updates...", action: #selector(checkForUpdates), keyEquivalent: "")
        updateItem.target = self
        menu.addItem(updateItem)
        
        menu.addItem(NSMenuItem.separator())
        let quitItem = NSMenuItem(title: "Quit Potter", action: #selector(quit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)
        
        // Set menu normally
        statusItem?.menu = menu
        currentMenu = menu
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
        potterCore?.iconDelegate = self
        potterCore?.setup()
    }
    
    private func setupAutoUpdater() {
        PotterLogger.shared.info("startup", "🔄 Setting up auto-updater with proper Info.plist configuration...")
        
        // Initialize auto-updater with Info.plist configuration
        _ = AutoUpdateManager.shared
        
        PotterLogger.shared.info("startup", "✅ Auto-updater initialized")
    }
    
    private func checkAndShowSettingsIfNeeded() {
        // Get the currently selected LLM provider
        let selectedProviderString = UserDefaults.standard.string(forKey: "llm_provider") ?? "openAI"
        guard let selectedProvider = LLMProvider(rawValue: selectedProviderString) else {
            PotterLogger.shared.warning("startup", "⚠️ Invalid provider '\(selectedProviderString)', defaulting to OpenAI")
            return
        }
        
        // Check if the currently selected provider has an API key using lightweight check
        let hasSelectedProviderKey = SecureAPIKeyStorage.shared.hasAPIKey(for: selectedProvider)
        
        PotterLogger.shared.debug("startup", "🔍 Checking selected provider: \(selectedProvider.displayName), has key: \(hasSelectedProviderKey)")
        
        if !hasSelectedProviderKey {
            // Currently selected provider has no API key, show settings
            PotterLogger.shared.info("startup", "📋 Selected provider '\(selectedProvider.displayName)' has no API key, showing settings dialog")
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.showSettingsUntilSelectedProviderHasKey()
            }
        } else {
            PotterLogger.shared.debug("startup", "✅ Selected provider '\(selectedProvider.displayName)' has API key, settings dialog will remain hidden")
        }
    }
    
    private func showSettingsUntilSelectedProviderHasKey() {
        showSettings()
        
        // Start monitoring for the selected provider's API key after a brief delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { timer in
                // Get the currently selected provider
                let selectedProviderString = UserDefaults.standard.string(forKey: "llm_provider") ?? "openAI"
                guard let selectedProvider = LLMProvider(rawValue: selectedProviderString) else {
                    timer.invalidate()
                    return
                }
                
                // Check if the currently selected provider has an API key using lightweight check
                let hasSelectedProviderKey = SecureAPIKeyStorage.shared.hasAPIKey(for: selectedProvider)
                
                PotterLogger.shared.debug("startup", "🔍 Monitoring selected provider: \(selectedProvider.displayName), has key: \(hasSelectedProviderKey)")
                
                if hasSelectedProviderKey {
                    // Selected provider now has an API key, stop checking
                    timer.invalidate()
                    PotterLogger.shared.debug("startup", "✅ Selected provider '\(selectedProvider.displayName)' now has API key, stopping auto-check")
                    
                    // Don't auto-close settings - let user close manually
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
        PotterLogger.shared.info("hotkey", "🎯 Global hotkey triggered (⌘⇧9)")
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
    
    @objc func checkForUpdates() {
        PotterLogger.shared.info("menu", "🔍 Manual update check requested from menu")
        AutoUpdateManager.shared.checkForUpdatesManually()
    }
    
    @objc func openPermissionSettings(_ sender: NSMenuItem) {
        guard let permission = sender.representedObject as? PermissionType else { return }
        
        Task { @MainActor in
            let permissionManager = PermissionManager.shared
            permissionManager.openSystemSettings(for: permission)
        }
    }
    
    
    @objc func clearError() {
        setNormalState()
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

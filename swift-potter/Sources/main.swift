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

print("🎭 Potter.ai: Copy → Enhance → Paste")
print("Starting Swift version...")

app.run()

class AppDelegate: NSObject, NSApplicationDelegate, IconStateDelegate {
    var statusItem: NSStatusItem?
    var potterCore: PotterCore?
    var menuUpdateTimer: Timer?
    var currentPromptName: String = "polish" // Default prompt
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
        let savedPrompt = UserDefaults.standard.string(forKey: "current_prompt")
        currentPromptName = ensureValidPromptSelection(savedPrompt)
    }
    
    /// Ensures a valid prompt is selected, falling back to first available prompt if needed
    private func ensureValidPromptSelection(_ requestedPrompt: String?) -> String {
        let availablePrompts = PromptService.shared.prompts
        
        // If no prompts available at all, something is seriously wrong
        guard !availablePrompts.isEmpty else {
            PotterLogger.shared.error("prompts", "❌ No prompts available - this should never happen")
            return "polish" // Fallback to hardcoded default
        }
        
        // Check if requested prompt exists in available prompts
        if let requested = requestedPrompt,
           availablePrompts.contains(where: { $0.name == requested }) {
            PotterLogger.shared.debug("prompts", "✅ Using saved prompt: \(requested)")
            return requested
        }
        
        // Fallback to first available prompt
        let firstPrompt = availablePrompts[0].name
        PotterLogger.shared.info("prompts", "🔄 Falling back to first available prompt: \(firstPrompt)")
        
        // Save the selection for next time
        UserDefaults.standard.set(firstPrompt, forKey: "current_prompt")
        
        return firstPrompt
    }
    
    private func startMenuUpdateTimer() {
        // Update menu less frequently to reflect permission changes (2 minutes is sufficient)
        menuUpdateTimer = Timer.scheduledTimer(withTimeInterval: 120.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.updateMenu()
            }
        }
    }
    
    private func setupMenuBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        
        if let button = statusItem?.button {
            updateMenuBarIcon()
            button.toolTip = "Potter.ai: Copy → Enhance → Paste"
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
        
        // PotterLogger.shared.debug("ui", "🎨 Updated menu bar icon for \(isDarkMode ? "dark" : "light") mode, state: \(currentIconState)")
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
        // Load from Resources bundle
        if let iconURL = Bundle.module.url(forResource: "menubar-icon-template", withExtension: "png", subdirectory: "Resources"),
           let image = NSImage(contentsOf: iconURL) {
            image.size = NSSize(width: 18, height: 18)
            image.isTemplate = true  // This makes it adapt to light/dark mode automatically
            return image
        }
        
        // Direct file path
        let templatePath = "Sources/Resources/menubar-icon-template.png"
        if FileManager.default.fileExists(atPath: templatePath),
           let image = NSImage(contentsOfFile: templatePath) {
            image.size = NSSize(width: 18, height: 18)
            image.isTemplate = true
            return image
        }
        
        // If no image found, create blank template
        let image = NSImage(size: NSSize(width: 18, height: 18))
        image.isTemplate = true
        return image
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
    func updateMenu() {
        let menu = NSMenu()
        
        // Load current hotkey from UserDefaults
        let currentHotkey = UserDefaults.standard.array(forKey: HotkeyConstants.userDefaultsKey) as? [String] ?? HotkeyConstants.defaultHotkey
        let hotkeyString = currentHotkey.joined(separator: "")
        
        let processItem = NSMenuItem(title: "Process Text (\(hotkeyString))", action: #selector(processText), keyEquivalent: "")
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
        
        menu.addItem(NSMenuItem.separator())
        
        // Dynamic Prompts at first level (no submenu)
        addPromptsToMenu(menu)
        
        menu.addItem(NSMenuItem.separator())
        let settingsItem = NSMenuItem(title: "Preferences...", action: #selector(showSettings), keyEquivalent: "")
        settingsItem.target = self
        menu.addItem(settingsItem)
        
        menu.addItem(NSMenuItem.separator())
        let quitItem = NSMenuItem(title: "Quit Potter", action: #selector(quit), keyEquivalent: "")
        quitItem.target = self
        menu.addItem(quitItem)
        
        // Set menu normally
        statusItem?.menu = menu
        currentMenu = menu
    }
    
    @MainActor
    func updateMenuForHotkeyChange() {
        updateMenu()
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
        
        // Check if the currently selected provider has an API key using StorageAdapter
        let hasSelectedProviderKey = StorageAdapter.shared.hasAPIKey(for: selectedProvider)
        
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
                
                // Check if the currently selected provider has an API key using StorageAdapter
                let hasSelectedProviderKey = StorageAdapter.shared.hasAPIKey(for: selectedProvider)
                
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
    
    
    @objc func processText() {
        PotterLogger.shared.info("hotkey", "🎯 Global hotkey triggered (⌘⇧9)")
        potterCore?.processClipboardText()
    }
    
    private func addPromptsToMenu(_ menu: NSMenu) {
        // Load prompts from JSON
        let prompts = PromptService.shared.prompts
        
        // Ensure current selection is valid before building menu
        currentPromptName = ensureValidPromptSelection(currentPromptName)
        
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

import AppKit
import Foundation

// MARK: - MenuBarManager
/// Manages all menu bar operations, icon states, and menu building
/// Separates menu bar UI concerns from application lifecycle and business logic
class MenuBarManager: NSObject, IconStateDelegate {
    
    // MARK: - Properties
    private var statusItem: NSStatusItem?
    private var currentMenu: NSMenu?
    private var menuUpdateTimer: Timer?
    
    // Icon state management
    private var currentIconState: IconState = .normal
    private var spinnerTimer: Timer?
    private var spinnerRotation: CGFloat = 0
    private var currentErrorMessage: String = ""
    
    // Dependencies
    private let potterCore: PotterCore
    private var currentPromptName: String = "" // Will be set to first available prompt
    
    // MARK: - Icon State
    enum IconState {
        case normal
        case processing
        case success
        case error
    }
    
    // MARK: - Initialization
    init(potterCore: PotterCore) {
        self.potterCore = potterCore
        super.init()
        
        PotterLogger.shared.debug("menu", "🏗️ Initializing MenuBarManager")
        PotterLogger.shared.debug("menu", "📋 PromptService prompts count at init: \(PromptService.shared.prompts.count)")
        
        setupMenuBar()
        startMenuUpdateTimer()
    }
    
    deinit {
        cleanup()
    }
    
    // MARK: - Public Interface
    
    /// Update the menu with current prompts and state
    @MainActor
    func updateMenu() {
        PotterLogger.shared.debug("menu", "🔄 Updating menu...")
        let menu = NSMenu()
        
        // Process Text item (always show)
        let processItem = NSMenuItem(title: "Process Text (⌘⇧9)", action: #selector(processText), keyEquivalent: "")
        processItem.target = self
        menu.addItem(processItem)
        
        // Add error message below Process Text if there's an error
        if currentIconState == .error && !currentErrorMessage.isEmpty {
            let errorItem = NSMenuItem(title: currentErrorMessage, action: #selector(clearError), keyEquivalent: "")
            errorItem.target = self
            
            // Style the error item
            let attributes: [NSAttributedString.Key: Any] = [
                .foregroundColor: NSColor.systemRed,
                .font: NSFont.systemFont(ofSize: 13, weight: .medium)
            ]
            errorItem.attributedTitle = NSAttributedString(string: currentErrorMessage, attributes: attributes)
            menu.addItem(errorItem)
        }
        
        menu.addItem(NSMenuItem.separator())
        
        // Add prompts section
        addPromptsToMenu(menu)
        
        // Add separator before preferences
        menu.addItem(NSMenuItem.separator())
        
        // Preferences
        let preferencesItem = NSMenuItem(title: "Preferences...", action: #selector(showSettings), keyEquivalent: "")
        preferencesItem.target = self
        menu.addItem(preferencesItem)
        
        // Quit
        let quitItem = NSMenuItem(title: "Quit Potter", action: #selector(quit), keyEquivalent: "")
        quitItem.target = self
        menu.addItem(quitItem)
        
        currentMenu = menu
        statusItem?.menu = menu
    }
    
    /// Update menu when hotkey changes
    @MainActor
    func updateMenuForHotkeyChange() {
        updateMenu()
    }
    
    // MARK: - Icon State Management
    
    func setProcessingState() {
        DispatchQueue.main.async { [weak self] in
            self?.currentIconState = .processing
            self?.currentErrorMessage = "" // Clear any previous error
            self?.updateMenuBarIcon()
            self?.startSpinnerAnimation()
            self?.updateMenu() // Update menu to remove any error messages
        }
    }
    
    func setSuccessState() {
        DispatchQueue.main.async { [weak self] in
            self?.currentIconState = .success
            self?.stopSpinnerAnimation()
            self?.updateMenuBarIcon()
            
            // Auto-reset to normal after 2 seconds
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) { [weak self] in
                self?.setNormalState()
            }
        }
    }
    
    func setNormalState() {
        DispatchQueue.main.async { [weak self] in
            self?.currentIconState = .normal
            self?.currentErrorMessage = ""
            self?.stopSpinnerAnimation()
            self?.updateMenuBarIcon()
            self?.updateMenu()
        }
    }
    
    func setErrorState(message: String) {
        DispatchQueue.main.async { [weak self] in
            PotterLogger.shared.debug("menu", "🔴 Setting error state: \(message)")
            self?.currentIconState = .error
            self?.currentErrorMessage = message
            self?.stopSpinnerAnimation()
            self?.updateMenuBarIcon()
            self?.updateMenu()
            
            // Auto-reset to normal after 10 seconds
            DispatchQueue.main.asyncAfter(deadline: .now() + 10.0) { [weak self] in
                PotterLogger.shared.debug("menu", "⏰ Auto-resetting from error state")
                self?.setNormalState()
            }
        }
    }
    
    // MARK: - Private Methods
    
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
    
    private func setupMenu() {
        Task { @MainActor in
            updateMenu()
        }
    }
    
    private func startMenuUpdateTimer() {
        // Update menu less frequently to reflect permission changes (2 minutes is sufficient)
        menuUpdateTimer = Timer.scheduledTimer(withTimeInterval: 120.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.updateMenu()
            }
        }
    }
    
    private func cleanup() {
        menuUpdateTimer?.invalidate()
        spinnerTimer?.invalidate()
        DistributedNotificationCenter.default.removeObserver(self)
    }
    
    // MARK: - Menu Building
    
    private func addPromptsToMenu(_ menu: NSMenu) {
        let availablePrompts = PromptService.shared.prompts
        
        PotterLogger.shared.debug("menu", "📋 Available prompts count: \(availablePrompts.count)")
        for prompt in availablePrompts {
            PotterLogger.shared.debug("menu", "📋 Prompt: \(prompt.name)")
        }
        
        guard !availablePrompts.isEmpty else {
            PotterLogger.shared.warning("menu", "⚠️ No prompts available, showing placeholder")
            let noPromptsItem = NSMenuItem(title: "No prompts available", action: nil, keyEquivalent: "")
            noPromptsItem.isEnabled = false
            menu.addItem(noPromptsItem)
            return
        }
        
        // Get the current prompt from UserDefaults, defaulting to first available prompt
        let defaultPromptName = availablePrompts.first!.name
        let savedPromptName = UserDefaults.standard.string(forKey: "current_prompt") ?? defaultPromptName
        currentPromptName = savedPromptName
        
        for prompt in availablePrompts {
            let menuItem = NSMenuItem(title: prompt.name, action: #selector(selectPrompt(_:)), keyEquivalent: "")
            menuItem.target = self
            menuItem.representedObject = prompt.name
            
            // Mark the currently selected prompt
            if prompt.name == currentPromptName {
                menuItem.state = .on
            }
            
            menu.addItem(menuItem)
        }
    }
    
    // MARK: - Menu Actions
    
    @objc private func processText() {
        potterCore.processClipboardText()
    }
    
    @objc private func showSettings() {
        // Open settings window
        if let settingsWindow = ModernSettingsWindowController.shared.window,
           !settingsWindow.isVisible {
            ModernSettingsWindowController.shared.showWindow(nil)
        }
        NSApp.activate(ignoringOtherApps: true)
    }
    
    @objc private func selectPrompt(_ sender: NSMenuItem) {
        if let promptName = sender.representedObject as? String {
            currentPromptName = promptName
            UserDefaults.standard.set(promptName, forKey: "current_prompt")
            
            PotterLogger.shared.info("menu", "📋 Selected prompt: \(promptName)")
            
            // Update menu to reflect new selection
            Task { @MainActor in
                updateMenu()
            }
        }
    }
    
    @objc private func clearError() {
        setNormalState()
    }
    
    @objc private func quit() {
        NSApplication.shared.terminate(nil)
    }
    
    // MARK: - Icon Management
    
    private func updateMenuBarIcon() {
        guard let button = statusItem?.button else { return }
        
        // Dark mode detection removed - not needed with proper tinting
        
        let iconImage: NSImage
        
        switch currentIconState {
        case .normal:
            iconImage = createMenuBarIcon()
            button.contentTintColor = nil // Use default tint
        case .processing:
            iconImage = createSpinnerIcon()
            button.contentTintColor = nil
        case .success:
            PotterLogger.shared.debug("menu", "🟢 Creating green success icon")
            iconImage = createTintedIcon(color: NSColor.systemGreen)
            button.contentTintColor = nil
        case .error:
            PotterLogger.shared.debug("menu", "🔴 Creating red error icon")
            iconImage = createTintedIcon(color: NSColor.systemRed)
            button.contentTintColor = nil
        }
        
        button.image = iconImage
    }
    
    private func startSpinnerAnimation() {
        stopSpinnerAnimation() // Stop any existing timer
        
        spinnerTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            DispatchQueue.main.async {
                self?.spinnerRotation += 15 // Degrees
                if let rotation = self?.spinnerRotation, rotation >= 360 {
                    self?.spinnerRotation = 0
                }
                self?.updateMenuBarIcon()
            }
        }
    }
    
    private func stopSpinnerAnimation() {
        spinnerTimer?.invalidate()
        spinnerTimer = nil
        spinnerRotation = 0
    }
    
    // MARK: - Icon Drawing
    
    private func createMenuBarIcon() -> NSImage {
        // Load the template icon - no fallbacks
        guard let templateIcon = Bundle.module.image(forResource: "menubar-icon-template") else {
            fatalError("menubar-icon-template.png not found in Resources")
        }
        
        let icon = templateIcon.copy() as! NSImage
        icon.isTemplate = true
        return icon
    }
    
    private func createTintedIcon(color: NSColor) -> NSImage {
        guard let templateIcon = Bundle.module.image(forResource: "menubar-icon-template") else {
            fatalError("menubar-icon-template.png not found in Resources")
        }
        
        let tintedIcon = NSImage(size: templateIcon.size)
        tintedIcon.lockFocus()
        
        // Fill with the color
        color.set()
        NSRect(origin: .zero, size: templateIcon.size).fill()
        
        // Use the original icon as a mask
        templateIcon.draw(at: .zero, from: NSRect(origin: .zero, size: templateIcon.size), operation: .destinationIn, fraction: 1.0)
        
        tintedIcon.unlockFocus()
        return tintedIcon
    }
    
    private func createSpinnerIcon() -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)
        
        image.lockFocus()
        
        // Draw spinner with current rotation
        let context = NSGraphicsContext.current?.cgContext
        context?.saveGState()
        
        let center = NSPoint(x: size.width / 2, y: size.height / 2)
        context?.translateBy(x: center.x, y: center.y)
        context?.rotate(by: -spinnerRotation * .pi / 180)
        context?.translateBy(x: -center.x, y: -center.y)
        
        drawSpinner()
        
        context?.restoreGState()
        
        image.unlockFocus()
        
        return image
    }
    
    private func drawSpinner() {
        let center = NSPoint(x: 9, y: 9)
        let radius: CGFloat = 6
        let lineWidth: CGFloat = 2
        
        // Draw spinner segments with varying opacity
        for i in 0..<8 {
            let angle = Double(i) * .pi / 4
            let startPoint = NSPoint(
                x: center.x + CGFloat(cos(angle)) * (radius - lineWidth),
                y: center.y + CGFloat(sin(angle)) * (radius - lineWidth)
            )
            let endPoint = NSPoint(
                x: center.x + CGFloat(cos(angle)) * radius,
                y: center.y + CGFloat(sin(angle)) * radius
            )
            
            let opacity = 0.2 + (0.8 * Double(7 - i) / 7.0)
            NSColor.white.withAlphaComponent(opacity).setStroke()
            
            let path = NSBezierPath()
            path.move(to: startPoint)
            path.line(to: endPoint)
            path.lineWidth = lineWidth
            path.stroke()
        }
    }
}
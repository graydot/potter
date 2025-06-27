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
    private var currentPromptName: String = "Fix Grammar" // Default prompt
    
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
        let menu = NSMenu()
        
        // Add error message at top if there's an error
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
            menu.addItem(NSMenuItem.separator())
        }
        
        // Add prompts section
        addPromptsToMenu(menu)
        
        // Add separator and settings
        menu.addItem(NSMenuItem.separator())
        
        // Process Text item (only if no error)
        if currentIconState != .error {
            let processItem = NSMenuItem(title: "Process Text (⌘⇧9)", action: #selector(processText), keyEquivalent: "")
            processItem.target = self
            menu.addItem(processItem)
            menu.addItem(NSMenuItem.separator())
        }
        
        // Settings
        let settingsItem = NSMenuItem(title: "Settings...", action: #selector(showSettings), keyEquivalent: ",")
        settingsItem.target = self
        menu.addItem(settingsItem)
        
        // Quit
        let quitItem = NSMenuItem(title: "Quit Potter", action: #selector(quit), keyEquivalent: "q")
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
            self?.updateMenuBarIcon()
            self?.startSpinnerAnimation()
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
            self?.currentIconState = .error
            self?.currentErrorMessage = message
            self?.stopSpinnerAnimation()
            self?.updateMenuBarIcon()
            self?.updateMenu()
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
        
        guard !availablePrompts.isEmpty else {
            let noPromptsItem = NSMenuItem(title: "No prompts available", action: nil, keyEquivalent: "")
            noPromptsItem.isEnabled = false
            menu.addItem(noPromptsItem)
            return
        }
        
        // Get the current prompt from UserDefaults
        let savedPromptName = UserDefaults.standard.string(forKey: "current_prompt") ?? currentPromptName
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
        
        let isDarkMode = NSApp.effectiveAppearance.name == .darkAqua || 
                         NSApp.effectiveAppearance.name == .vibrantDark
        
        let iconImage: NSImage
        
        switch currentIconState {
        case .normal:
            iconImage = createCauldronIcon(forDarkMode: isDarkMode)
        case .processing:
            iconImage = createSpinnerIcon()
        case .success:
            iconImage = createCauldronIcon(forDarkMode: isDarkMode, state: .success)
        case .error:
            iconImage = createCauldronIcon(forDarkMode: isDarkMode, state: .error)
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
    
    private func createCauldronIcon(forDarkMode isDarkMode: Bool, state: IconState = .normal) -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let image = NSImage(size: size)
        
        image.lockFocus()
        
        let color: NSColor
        
        switch state {
        case .normal:
            color = isDarkMode ? NSColor.white : NSColor.black
        case .success:
            color = NSColor.systemGreen
        case .error:
            color = NSColor.systemRed
        case .processing:
            color = NSColor.systemBlue
        }
        
        // Draw a simple cauldron shape
        let path = NSBezierPath()
        
        // Cauldron body (rounded rectangle)
        let bodyRect = NSRect(x: 3, y: 4, width: 12, height: 10)
        path.appendRoundedRect(bodyRect, xRadius: 2, yRadius: 2)
        
        // Cauldron handle (left)
        let leftHandle = NSBezierPath()
        leftHandle.move(to: NSPoint(x: 2, y: 8))
        leftHandle.curve(to: NSPoint(x: 3, y: 10), controlPoint1: NSPoint(x: 1, y: 8), controlPoint2: NSPoint(x: 1, y: 10))
        
        // Cauldron handle (right)
        let rightHandle = NSBezierPath()
        rightHandle.move(to: NSPoint(x: 15, y: 10))
        rightHandle.curve(to: NSPoint(x: 16, y: 8), controlPoint1: NSPoint(x: 17, y: 10), controlPoint2: NSPoint(x: 17, y: 8))
        
        // Set color and draw
        color.setStroke()
        path.lineWidth = 1.5
        path.stroke()
        
        leftHandle.lineWidth = 1.0
        leftHandle.stroke()
        
        rightHandle.lineWidth = 1.0
        rightHandle.stroke()
        
        image.unlockFocus()
        
        return image
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
        context?.rotate(by: spinnerRotation * .pi / 180)
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
            
            let opacity = 0.2 + (0.8 * Double(i) / 7.0)
            NSColor.systemBlue.withAlphaComponent(opacity).setStroke()
            
            let path = NSBezierPath()
            path.move(to: startPoint)
            path.line(to: endPoint)
            path.lineWidth = lineWidth
            path.stroke()
        }
    }
}
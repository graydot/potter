import AppKit
import Foundation

// MARK: - MenuBarManager
/// Coordinates menu bar state transitions, timers, and user actions.
/// Delegates icon creation to IconFactory and menu construction to MenuBuilder.
class MenuBarManager: NSObject, IconStateDelegate {

    // MARK: - Properties
    private var statusItem: NSStatusItem?
    private var currentMenu: NSMenu?
    private var menuUpdateTimer: Timer?

    // Icon state management
    private var currentIconState: MenuBarIconState = .normal
    private var spinnerTimer: Timer?
    private var spinnerRotation: CGFloat = 0
    private var currentErrorMessage: String = ""

    // Dependencies
    private let potterCore: PotterCore
    private var currentPromptName: String = "" // Will be set to first available prompt

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

        // Show Onboarding
        let onboardingItem = NSMenuItem(title: "Show Onboarding/Help", action: #selector(showOnboarding), keyEquivalent: "")
        onboardingItem.target = self
        menu.addItem(onboardingItem)

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

        // Get the current prompt from PromptService
        currentPromptName = PromptService.shared.currentPromptName

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

    @objc private func showOnboarding() {
        OnboardingWindowController.shared.showOnboarding()
    }

    @objc private func selectPrompt(_ sender: NSMenuItem) {
        if let promptName = sender.representedObject as? String {
            PromptService.shared.setCurrentPrompt(promptName)
            currentPromptName = promptName

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

        let iconImage: NSImage

        switch currentIconState {
        case .normal:
            iconImage = IconFactory.createIcon(for: .normal)
            button.contentTintColor = nil // Use default tint
        case .processing:
            iconImage = IconFactory.createSpinnerFrame(rotation: spinnerRotation)
            button.contentTintColor = nil
        case .success:
            PotterLogger.shared.debug("menu", "🟢 Creating green success icon")
            iconImage = IconFactory.createIcon(for: .success)
            button.contentTintColor = nil
        case .error:
            PotterLogger.shared.debug("menu", "🔴 Creating red error icon")
            iconImage = IconFactory.createIcon(for: .error)
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
}

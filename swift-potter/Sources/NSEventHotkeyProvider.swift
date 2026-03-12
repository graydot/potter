import Foundation
import AppKit
import Carbon

/// App Store / sandbox compatible hotkey provider using NSEvent global monitoring.
/// Unlike Carbon's RegisterEventHotKey, NSEvent.addGlobalMonitorForEvents works
/// within the App Sandbox (requires accessibility permissions).
class NSEventHotkeyProvider: HotkeyProvider {

    // MARK: - Properties

    private(set) var currentHotkeyCombo: [String] = HotkeyConstants.defaultHotkey
    private var globalMonitor: Any?
    private var localMonitor: Any?
    private var hotkeyHandler: (() -> Void)?
    private var targetKeyCode: UInt32 = 0
    private var targetModifiers: CGEventFlags = []

    // MARK: - HotkeyProvider conformance

    func register(hotkey: [String], handler: @escaping () -> Void) {
        hotkeyHandler = handler
        currentHotkeyCombo = hotkey
        installMonitors(for: hotkey)
    }

    func unregister() {
        removeMonitors()
    }

    // MARK: - Setup

    /// Sets up the global hotkey: loads saved combo and installs event monitors.
    func setup(handler: @escaping () -> Void) {
        hotkeyHandler = handler

        // Load saved hotkey or use default
        if let savedHotkey = UserDefaults.standard.array(forKey: UserDefaultsKeys.globalHotkey) as? [String] {
            currentHotkeyCombo = savedHotkey
        }

        installMonitors(for: currentHotkeyCombo)
    }

    // MARK: - Hotkey Update

    /// Unregisters the current hotkey, registers a new one, and persists the choice.
    func updateHotkey(_ newHotkey: [String]) {
        removeMonitors()
        currentHotkeyCombo = newHotkey
        installMonitors(for: newHotkey)

        UserDefaults.standard.set(newHotkey, forKey: UserDefaultsKeys.globalHotkey)
        PotterLogger.shared.info("hotkeys", "🔄 Updated hotkey to: \(newHotkey.joined(separator: "+"))")
    }

    // MARK: - Enable / Disable

    func disableGlobalHotkey() {
        if globalMonitor != nil || localMonitor != nil {
            removeMonitors()
            PotterLogger.shared.debug("hotkeys", "⏸️ Temporarily disabled global hotkey")
        }
    }

    func enableGlobalHotkey() {
        if globalMonitor == nil && localMonitor == nil {
            installMonitors(for: currentHotkeyCombo)
            PotterLogger.shared.debug("hotkeys", "▶️ Re-enabled global hotkey")
        }
    }

    // MARK: - Private

    private func installMonitors(for combo: [String]) {
        removeMonitors()

        let (keyCode, modifiers) = HotkeyKeyMapping.parseCGCombo(combo)
        targetKeyCode = keyCode
        targetModifiers = modifiers

        // Global monitor: fires when another app is focused
        globalMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            self?.handleKeyEvent(event)
        }

        // Local monitor: fires when our app is focused
        localMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if self?.matchesHotkey(event) == true {
                self?.hotkeyHandler?()
                return nil // consume the event
            }
            return event
        }

        PotterLogger.shared.info("hotkeys", "✅ Registered hotkey (NSEvent): \(combo.joined(separator: "+"))")
    }

    private func removeMonitors() {
        if let monitor = globalMonitor {
            NSEvent.removeMonitor(monitor)
            globalMonitor = nil
        }
        if let monitor = localMonitor {
            NSEvent.removeMonitor(monitor)
            localMonitor = nil
        }
    }

    private func handleKeyEvent(_ event: NSEvent) {
        if matchesHotkey(event) {
            hotkeyHandler?()
        }
    }

    private func matchesHotkey(_ event: NSEvent) -> Bool {
        guard UInt32(event.keyCode) == targetKeyCode else { return false }

        // Check modifiers — mask out caps lock and other device-specific flags
        let relevantFlags: CGEventFlags = [.maskCommand, .maskAlternate, .maskControl, .maskShift]
        let eventModifiers = CGEventFlags(rawValue: UInt64(event.modifierFlags.rawValue)).intersection(relevantFlags)
        let targetRelevant = targetModifiers.intersection(relevantFlags)

        return eventModifiers == targetRelevant
    }

    deinit {
        removeMonitors()
    }
}

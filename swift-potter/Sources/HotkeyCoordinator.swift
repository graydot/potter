import Foundation
import Carbon

/// Protocol for hotkey registration, enabling mock implementations for testing.
/// Two implementations: HotkeyCoordinator (Carbon, direct distribution) and
/// NSEventHotkeyProvider (NSEvent, App Store / sandbox compatible).
protocol HotkeyProvider: AnyObject {
    func register(hotkey: [String], handler: @escaping () -> Void)
    func unregister()
    func setup(handler: @escaping () -> Void)
    func updateHotkey(_ newHotkey: [String])
    func disableGlobalHotkey()
    func enableGlobalHotkey()
    var currentHotkeyCombo: [String] { get }
}

/// Manages global hotkey registration using the Carbon Event API.
/// Used for direct (non-App Store) distribution where Carbon APIs are available.
/// For App Store / sandbox builds, use NSEventHotkeyProvider instead.
class HotkeyCoordinator: HotkeyProvider {

    // MARK: - Properties

    private(set) var currentHotkeyCombo: [String] = HotkeyConstants.defaultHotkey
    private var hotkeyEventHandler: EventHotKeyRef?
    var hotkeyHandler: (() -> Void)?

    // MARK: - HotkeyProvider conformance

    func register(hotkey: [String], handler: @escaping () -> Void) {
        hotkeyHandler = handler
        currentHotkeyCombo = hotkey
        registerHotkey(hotkey)
    }

    func unregister() {
        unregisterHotkey()
    }

    // MARK: - Setup

    /// Sets up the global hotkey: loads saved combo, installs the Carbon event handler, and registers the hotkey.
    func setup(handler: @escaping () -> Void) {
        hotkeyHandler = handler

        // Load saved hotkey or use default
        if let savedHotkey = UserDefaults.standard.array(forKey: HotkeyConstants.userDefaultsKey) as? [String] {
            currentHotkeyCombo = savedHotkey
        }

        // Install event handler for hotkey events
        var eventTypes = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        InstallEventHandler(
            GetApplicationEventTarget(),
            { (nextHandler, theEvent, userData) -> OSStatus in
                let coordinator = Unmanaged<HotkeyCoordinator>.fromOpaque(userData!).takeUnretainedValue()
                coordinator.hotkeyHandler?()
                return noErr
            },
            1,
            &eventTypes,
            Unmanaged.passUnretained(self).toOpaque(),
            nil
        )

        // Register the current hotkey
        registerHotkey(currentHotkeyCombo)
    }

    // MARK: - Hotkey Update

    /// Unregisters the current hotkey, registers a new one, and persists the choice.
    func updateHotkey(_ newHotkey: [String]) {
        unregisterHotkey()
        currentHotkeyCombo = newHotkey
        registerHotkey(newHotkey)

        // Save to UserDefaults
        UserDefaults.standard.set(newHotkey, forKey: HotkeyConstants.userDefaultsKey)
        PotterLogger.shared.info("hotkeys", "🔄 Updated hotkey to: \(newHotkey.joined(separator: "+"))")
    }

    // MARK: - Enable / Disable

    func disableGlobalHotkey() {
        if hotkeyEventHandler != nil {
            unregisterHotkey()
            PotterLogger.shared.debug("hotkeys", "⏸️ Temporarily disabled global hotkey")
        }
    }

    func enableGlobalHotkey() {
        if hotkeyEventHandler == nil {
            registerHotkey(currentHotkeyCombo)
            PotterLogger.shared.debug("hotkeys", "▶️ Re-enabled global hotkey")
        }
    }

    // MARK: - Internal helpers (accessible from tests, delegate to HotkeyKeyMapping)

    /// Parses a hotkey combo array (e.g. ["⌘","⇧","9"]) into (keyCode, modifiers).
    func parseHotkeyCombo(_ combo: [String]) -> (UInt32, UInt32) {
        let result = HotkeyKeyMapping.parseCarbonCombo(combo)
        return (result.keyCode, result.modifiers)
    }

    /// Converts a 4-character string to a FourCharCode (UInt32).
    func fourCharCode(_ string: String) -> UInt32 {
        return HotkeyKeyMapping.fourCharCode(string)
    }

    // MARK: - Private

    private func registerHotkey(_ hotkeyCombo: [String]) {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCarbonCombo(hotkeyCombo)

        var eventHotKeyRef: EventHotKeyRef?
        let hotKeyID = EventHotKeyID(signature: HotkeyKeyMapping.fourCharCode("POTR"), id: UInt32(1))

        let status = RegisterEventHotKey(
            keyCode,
            modifiers,
            hotKeyID,
            GetApplicationEventTarget(),
            0,
            &eventHotKeyRef
        )

        if status == noErr {
            self.hotkeyEventHandler = eventHotKeyRef
            PotterLogger.shared.info("hotkeys", "✅ Registered hotkey: \(hotkeyCombo.joined(separator: "+"))")
        } else {
            PotterLogger.shared.error("hotkeys", "❌ Failed to register hotkey: \(hotkeyCombo.joined(separator: "+"))")
        }
    }

    private func unregisterHotkey() {
        if let currentHandler = hotkeyEventHandler {
            UnregisterEventHotKey(currentHandler)
            hotkeyEventHandler = nil
        }
    }
}

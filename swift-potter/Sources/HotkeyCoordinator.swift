import Foundation
import Carbon

/// Protocol for hotkey registration, enabling mock implementations for testing.
protocol HotkeyProvider: AnyObject {
    func register(hotkey: [String], handler: @escaping () -> Void)
    func unregister()
    var currentHotkeyCombo: [String] { get }
}

/// Manages global hotkey registration, parsing, and persistence using the Carbon Event API.
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

    // MARK: - Internal helpers (accessible from tests)

    /// Parses a hotkey combo array (e.g. ["⌘","⇧","9"]) into (keyCode, modifiers).
    func parseHotkeyCombo(_ combo: [String]) -> (UInt32, UInt32) {
        var modifiers: UInt32 = 0
        var keyCode: UInt32 = UInt32(kVK_ANSI_9) // Default to 9

        for key in combo {
            switch key {
            case "⌘":
                modifiers |= UInt32(cmdKey)
            case "⌥":
                modifiers |= UInt32(optionKey)
            case "⌃":
                modifiers |= UInt32(controlKey)
            case "⇧":
                modifiers |= UInt32(shiftKey)
            case "R":
                keyCode = UInt32(kVK_ANSI_R)
            case "T":
                keyCode = UInt32(kVK_ANSI_T)
            case "Y":
                keyCode = UInt32(kVK_ANSI_Y)
            case "U":
                keyCode = UInt32(kVK_ANSI_U)
            case "I":
                keyCode = UInt32(kVK_ANSI_I)
            case "O":
                keyCode = UInt32(kVK_ANSI_O)
            case "P":
                keyCode = UInt32(kVK_ANSI_P)
            case "A":
                keyCode = UInt32(kVK_ANSI_A)
            case "S":
                keyCode = UInt32(kVK_ANSI_S)
            case "D":
                keyCode = UInt32(kVK_ANSI_D)
            case "F":
                keyCode = UInt32(kVK_ANSI_F)
            case "G":
                keyCode = UInt32(kVK_ANSI_G)
            case "H":
                keyCode = UInt32(kVK_ANSI_H)
            case "J":
                keyCode = UInt32(kVK_ANSI_J)
            case "K":
                keyCode = UInt32(kVK_ANSI_K)
            case "L":
                keyCode = UInt32(kVK_ANSI_L)
            case "Z":
                keyCode = UInt32(kVK_ANSI_Z)
            case "X":
                keyCode = UInt32(kVK_ANSI_X)
            case "C":
                keyCode = UInt32(kVK_ANSI_C)
            case "V":
                keyCode = UInt32(kVK_ANSI_V)
            case "B":
                keyCode = UInt32(kVK_ANSI_B)
            case "N":
                keyCode = UInt32(kVK_ANSI_N)
            case "M":
                keyCode = UInt32(kVK_ANSI_M)
            case "9":
                keyCode = UInt32(kVK_ANSI_9)
            case "8":
                keyCode = UInt32(kVK_ANSI_8)
            case "7":
                keyCode = UInt32(kVK_ANSI_7)
            case "6":
                keyCode = UInt32(kVK_ANSI_6)
            case "5":
                keyCode = UInt32(kVK_ANSI_5)
            case "4":
                keyCode = UInt32(kVK_ANSI_4)
            case "3":
                keyCode = UInt32(kVK_ANSI_3)
            case "2":
                keyCode = UInt32(kVK_ANSI_2)
            case "1":
                keyCode = UInt32(kVK_ANSI_1)
            case "0":
                keyCode = UInt32(kVK_ANSI_0)
            default:
                break
            }
        }

        return (keyCode, modifiers)
    }

    /// Converts a 4-character string to a FourCharCode (UInt32).
    func fourCharCode(_ string: String) -> UInt32 {
        let chars = Array(string.utf8)
        return chars.indices.reduce(0) { acc, i in
            acc + (UInt32(chars[i]) << (8 * (3 - i)))
        }
    }

    // MARK: - Private

    private func registerHotkey(_ hotkeyCombo: [String]) {
        let (keyCode, modifiers) = parseHotkeyCombo(hotkeyCombo)

        var eventHotKeyRef: EventHotKeyRef?
        let hotKeyID = EventHotKeyID(signature: fourCharCode("POTR"), id: UInt32(1))

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

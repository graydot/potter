import Foundation
import Carbon

/// Shared key code and modifier mapping used by all hotkey providers.
/// Extracts the 40+ case key mapping from HotkeyCoordinator into a reusable utility.
enum HotkeyKeyMapping {

    // MARK: - Modifier Mapping

    /// Maps modifier symbols to Carbon modifier flags.
    static let modifierMap: [String: UInt32] = [
        "⌘": UInt32(cmdKey),
        "⌥": UInt32(optionKey),
        "⌃": UInt32(controlKey),
        "⇧": UInt32(shiftKey),
    ]

    /// Maps modifier symbols to CGEventFlags for NSEvent/CGEvent-based providers.
    static let cgModifierMap: [String: CGEventFlags] = [
        "⌘": .maskCommand,
        "⌥": .maskAlternate,
        "⌃": .maskControl,
        "⇧": .maskShift,
    ]

    // MARK: - Key Code Mapping

    /// Maps key characters to Carbon virtual key codes.
    static let keyCodeMap: [String: UInt32] = [
        "A": UInt32(kVK_ANSI_A),
        "B": UInt32(kVK_ANSI_B),
        "C": UInt32(kVK_ANSI_C),
        "D": UInt32(kVK_ANSI_D),
        "F": UInt32(kVK_ANSI_F),
        "G": UInt32(kVK_ANSI_G),
        "H": UInt32(kVK_ANSI_H),
        "I": UInt32(kVK_ANSI_I),
        "J": UInt32(kVK_ANSI_J),
        "K": UInt32(kVK_ANSI_K),
        "L": UInt32(kVK_ANSI_L),
        "M": UInt32(kVK_ANSI_M),
        "N": UInt32(kVK_ANSI_N),
        "O": UInt32(kVK_ANSI_O),
        "P": UInt32(kVK_ANSI_P),
        "R": UInt32(kVK_ANSI_R),
        "S": UInt32(kVK_ANSI_S),
        "T": UInt32(kVK_ANSI_T),
        "U": UInt32(kVK_ANSI_U),
        "V": UInt32(kVK_ANSI_V),
        "X": UInt32(kVK_ANSI_X),
        "Y": UInt32(kVK_ANSI_Y),
        "Z": UInt32(kVK_ANSI_Z),
        "0": UInt32(kVK_ANSI_0),
        "1": UInt32(kVK_ANSI_1),
        "2": UInt32(kVK_ANSI_2),
        "3": UInt32(kVK_ANSI_3),
        "4": UInt32(kVK_ANSI_4),
        "5": UInt32(kVK_ANSI_5),
        "6": UInt32(kVK_ANSI_6),
        "7": UInt32(kVK_ANSI_7),
        "8": UInt32(kVK_ANSI_8),
        "9": UInt32(kVK_ANSI_9),
    ]

    /// Set of all modifier symbols for quick lookup.
    static let modifierSymbols: Set<String> = Set(modifierMap.keys)

    // MARK: - Parsing

    /// Parses a hotkey combo array (e.g. ["⌘","⇧","9"]) into (keyCode, carbonModifiers).
    static func parseCarbonCombo(_ combo: [String]) -> (keyCode: UInt32, modifiers: UInt32) {
        var modifiers: UInt32 = 0
        var keyCode: UInt32 = UInt32(kVK_ANSI_9) // Default

        for key in combo {
            if let mod = modifierMap[key] {
                modifiers |= mod
            } else if let code = keyCodeMap[key] {
                keyCode = code
            }
        }

        return (keyCode, modifiers)
    }

    /// Parses a hotkey combo array into (keyCode, CGEventFlags) for NSEvent/CGEvent providers.
    static func parseCGCombo(_ combo: [String]) -> (keyCode: UInt32, modifiers: CGEventFlags) {
        var modifiers: CGEventFlags = []
        var keyCode: UInt32 = UInt32(kVK_ANSI_9) // Default

        for key in combo {
            if let mod = cgModifierMap[key] {
                modifiers.insert(mod)
            } else if let code = keyCodeMap[key] {
                keyCode = code
            }
        }

        return (keyCode, modifiers)
    }

    /// Converts a 4-character string to a FourCharCode (UInt32).
    static func fourCharCode(_ string: String) -> UInt32 {
        let chars = Array(string.utf8)
        return chars.indices.reduce(0) { acc, i in
            acc + (UInt32(chars[i]) << (8 * (3 - i)))
        }
    }
}

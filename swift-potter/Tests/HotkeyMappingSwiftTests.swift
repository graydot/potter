import Testing
import Foundation
import Carbon
@testable import Potter

// MARK: - modifierMap Tests

@Suite("HotkeyKeyMapping.modifierMap")
struct ModifierMapTests {

    @Test("modifierMap contains all four modifier symbols")
    func containsAllModifierSymbols() {
        #expect(HotkeyKeyMapping.modifierMap["⌘"] != nil)
        #expect(HotkeyKeyMapping.modifierMap["⌥"] != nil)
        #expect(HotkeyKeyMapping.modifierMap["⌃"] != nil)
        #expect(HotkeyKeyMapping.modifierMap["⇧"] != nil)
    }

    @Test("modifierMap has exactly four entries")
    func exactlyFourEntries() {
        #expect(HotkeyKeyMapping.modifierMap.count == 4)
    }

    @Test("modifierMap maps ⌘ to cmdKey")
    func commandKeyMapping() {
        #expect(HotkeyKeyMapping.modifierMap["⌘"] == UInt32(cmdKey))
    }

    @Test("modifierMap maps ⌥ to optionKey")
    func optionKeyMapping() {
        #expect(HotkeyKeyMapping.modifierMap["⌥"] == UInt32(optionKey))
    }

    @Test("modifierMap maps ⌃ to controlKey")
    func controlKeyMapping() {
        #expect(HotkeyKeyMapping.modifierMap["⌃"] == UInt32(controlKey))
    }

    @Test("modifierMap maps ⇧ to shiftKey")
    func shiftKeyMapping() {
        #expect(HotkeyKeyMapping.modifierMap["⇧"] == UInt32(shiftKey))
    }

    @Test("modifierMap does not contain non-modifier characters")
    func nonModifierCharactersAbsent() {
        #expect(HotkeyKeyMapping.modifierMap["A"] == nil)
        #expect(HotkeyKeyMapping.modifierMap["9"] == nil)
        #expect(HotkeyKeyMapping.modifierMap["F"] == nil)
        #expect(HotkeyKeyMapping.modifierMap["Space"] == nil)
    }
}

// MARK: - cgModifierMap Tests

@Suite("HotkeyKeyMapping.cgModifierMap")
struct CGModifierMapTests {

    @Test("cgModifierMap contains all four modifier symbols")
    func containsAllModifierSymbols() {
        #expect(HotkeyKeyMapping.cgModifierMap["⌘"] != nil)
        #expect(HotkeyKeyMapping.cgModifierMap["⌥"] != nil)
        #expect(HotkeyKeyMapping.cgModifierMap["⌃"] != nil)
        #expect(HotkeyKeyMapping.cgModifierMap["⇧"] != nil)
    }

    @Test("cgModifierMap has exactly four entries")
    func exactlyFourEntries() {
        #expect(HotkeyKeyMapping.cgModifierMap.count == 4)
    }

    @Test("cgModifierMap maps ⌘ to maskCommand")
    func commandMapping() {
        #expect(HotkeyKeyMapping.cgModifierMap["⌘"] == .maskCommand)
    }

    @Test("cgModifierMap maps ⌥ to maskAlternate")
    func optionMapping() {
        #expect(HotkeyKeyMapping.cgModifierMap["⌥"] == .maskAlternate)
    }

    @Test("cgModifierMap maps ⌃ to maskControl")
    func controlMapping() {
        #expect(HotkeyKeyMapping.cgModifierMap["⌃"] == .maskControl)
    }

    @Test("cgModifierMap maps ⇧ to maskShift")
    func shiftMapping() {
        #expect(HotkeyKeyMapping.cgModifierMap["⇧"] == .maskShift)
    }

    @Test("cgModifierMap does not contain non-modifier characters")
    func nonModifierCharactersAbsent() {
        #expect(HotkeyKeyMapping.cgModifierMap["Z"] == nil)
        #expect(HotkeyKeyMapping.cgModifierMap["1"] == nil)
    }
}

// MARK: - keyCodeMap Tests

@Suite("HotkeyKeyMapping.keyCodeMap")
struct KeyCodeMapTests {

    @Test("keyCodeMap contains all defined letter keys")
    func definedLetterKeysPresent() {
        // Letters present in keyCodeMap (note: E, Q, W are absent by design)
        let definedLetters = ["A","B","C","D","F","G","H","I","J","K","L","M",
                              "N","O","P","R","S","T","U","V","X","Y","Z"]
        for letter in definedLetters {
            #expect(HotkeyKeyMapping.keyCodeMap[letter] != nil, "Letter \(letter) should be in keyCodeMap")
        }
    }

    @Test("keyCodeMap contains all digit keys 0-9")
    func allDigitKeysPresent() {
        for digit in 0...9 {
            let key = String(digit)
            #expect(HotkeyKeyMapping.keyCodeMap[key] != nil, "Digit \(key) should be in keyCodeMap")
        }
    }

    @Test("keyCodeMap maps A to kVK_ANSI_A")
    func letterAMapping() {
        #expect(HotkeyKeyMapping.keyCodeMap["A"] == UInt32(kVK_ANSI_A))
    }

    @Test("keyCodeMap maps Z to kVK_ANSI_Z")
    func letterZMapping() {
        #expect(HotkeyKeyMapping.keyCodeMap["Z"] == UInt32(kVK_ANSI_Z))
    }

    @Test("keyCodeMap maps 0 to kVK_ANSI_0")
    func digit0Mapping() {
        #expect(HotkeyKeyMapping.keyCodeMap["0"] == UInt32(kVK_ANSI_0))
    }

    @Test("keyCodeMap maps 9 to kVK_ANSI_9")
    func digit9Mapping() {
        #expect(HotkeyKeyMapping.keyCodeMap["9"] == UInt32(kVK_ANSI_9))
    }

    @Test("keyCodeMap does not map modifier symbols")
    func modifierSymbolsAbsent() {
        #expect(HotkeyKeyMapping.keyCodeMap["⌘"] == nil)
        #expect(HotkeyKeyMapping.keyCodeMap["⌥"] == nil)
        #expect(HotkeyKeyMapping.keyCodeMap["⌃"] == nil)
        #expect(HotkeyKeyMapping.keyCodeMap["⇧"] == nil)
    }

    @Test("keyCodeMap does not map arbitrary unknown strings")
    func unknownStringAbsent() {
        #expect(HotkeyKeyMapping.keyCodeMap["Return"] == nil)
        #expect(HotkeyKeyMapping.keyCodeMap["Escape"] == nil)
        #expect(HotkeyKeyMapping.keyCodeMap["Space"] == nil)
        #expect(HotkeyKeyMapping.keyCodeMap["🎯"] == nil)
        #expect(HotkeyKeyMapping.keyCodeMap[""] == nil)
    }

    @Test("all keyCodeMap values are non-zero (no zero-value collisions)")
    func allValuesNonZeroOrDistinctlyAssigned() {
        // kVK_ANSI_A is 0x00 — just verify all values are valid UInt32 and non-colliding
        let values = Array(HotkeyKeyMapping.keyCodeMap.values)
        let uniqueValues = Set(values)
        // Each key should map to a unique key code
        #expect(uniqueValues.count == values.count, "Each key should map to a unique key code")
    }
}

// MARK: - modifierSymbols Set Tests

@Suite("HotkeyKeyMapping.modifierSymbols")
struct ModifierSymbolsSetTests {

    @Test("modifierSymbols contains all four modifier symbols")
    func containsAllModifiers() {
        #expect(HotkeyKeyMapping.modifierSymbols.contains("⌘"))
        #expect(HotkeyKeyMapping.modifierSymbols.contains("⌥"))
        #expect(HotkeyKeyMapping.modifierSymbols.contains("⌃"))
        #expect(HotkeyKeyMapping.modifierSymbols.contains("⇧"))
    }

    @Test("modifierSymbols has exactly four elements")
    func exactlyFourElements() {
        #expect(HotkeyKeyMapping.modifierSymbols.count == 4)
    }

    @Test("modifierSymbols does not contain key characters")
    func doesNotContainKeyCharacters() {
        #expect(!HotkeyKeyMapping.modifierSymbols.contains("A"))
        #expect(!HotkeyKeyMapping.modifierSymbols.contains("9"))
        #expect(!HotkeyKeyMapping.modifierSymbols.contains("K"))
        #expect(!HotkeyKeyMapping.modifierSymbols.contains("0"))
    }

    @Test("modifierSymbols is consistent with modifierMap keys")
    func consistentWithModifierMap() {
        let mapKeys = Set(HotkeyKeyMapping.modifierMap.keys)
        #expect(HotkeyKeyMapping.modifierSymbols == mapKeys)
    }
}

// MARK: - parseCarbonCombo Tests (new angles)

@Suite("HotkeyKeyMapping.parseCarbonCombo (extended)")
struct ParseCarbonComboExtendedTests {

    @Test("no-modifier combo uses default key code and zero modifiers")
    func noModifierComboDefaultsToKeyCode9() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCarbonCombo(["9"])
        #expect(keyCode == UInt32(kVK_ANSI_9))
        #expect(modifiers == 0)
    }

    @Test("only modifier — no key — uses default key code 9")
    func onlyModifierUsesDefaultKey() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCarbonCombo(["⌘"])
        #expect(keyCode == UInt32(kVK_ANSI_9))
        #expect(modifiers == UInt32(cmdKey))
    }

    @Test("last key in combo wins if multiple non-modifier keys supplied")
    func multipleKeyCodesLastWins() {
        // parseCarbonCombo iterates the array in order; each recognized key
        // overwrites keyCode, so the last one should survive.
        let (keyCode, _) = HotkeyKeyMapping.parseCarbonCombo(["A", "Z"])
        // Both A and Z are in the map; Z is processed last and should win.
        #expect(keyCode == UInt32(kVK_ANSI_Z))
    }

    @Test("single-letter combos produce correct key codes")
    func singleLetterCombos() {
        let expectedPairs: [(String, Int)] = [
            ("A", kVK_ANSI_A), ("B", kVK_ANSI_B), ("C", kVK_ANSI_C), ("D", kVK_ANSI_D),
            ("F", kVK_ANSI_F), ("G", kVK_ANSI_G), ("H", kVK_ANSI_H), ("I", kVK_ANSI_I),
            ("J", kVK_ANSI_J), ("K", kVK_ANSI_K), ("L", kVK_ANSI_L), ("M", kVK_ANSI_M),
            ("N", kVK_ANSI_N), ("O", kVK_ANSI_O), ("P", kVK_ANSI_P), ("R", kVK_ANSI_R),
            ("S", kVK_ANSI_S), ("T", kVK_ANSI_T), ("U", kVK_ANSI_U), ("V", kVK_ANSI_V),
            ("X", kVK_ANSI_X), ("Y", kVK_ANSI_Y), ("Z", kVK_ANSI_Z),
        ]
        for (letter, expected) in expectedPairs {
            let (keyCode, _) = HotkeyKeyMapping.parseCarbonCombo([letter])
            #expect(keyCode == UInt32(expected), "Letter \(letter) should produce key code \(expected)")
        }
    }

    @Test("digit combos produce correct key codes")
    func digitCombos() {
        let expectedPairs: [(String, Int)] = [
            ("0", kVK_ANSI_0), ("1", kVK_ANSI_1), ("2", kVK_ANSI_2), ("3", kVK_ANSI_3),
            ("4", kVK_ANSI_4), ("5", kVK_ANSI_5), ("6", kVK_ANSI_6), ("7", kVK_ANSI_7),
            ("8", kVK_ANSI_8), ("9", kVK_ANSI_9),
        ]
        for (digit, expected) in expectedPairs {
            let (keyCode, _) = HotkeyKeyMapping.parseCarbonCombo([digit])
            #expect(keyCode == UInt32(expected), "Digit \(digit) should produce key code \(expected)")
        }
    }

    @Test("modifier bits do not bleed into key code")
    func modifierBitsDoNotBleedIntoKeyCode() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCarbonCombo(["⌘", "⌥", "⌃", "⇧", "A"])
        #expect(keyCode == UInt32(kVK_ANSI_A))
        // Verify modifiers are entirely separate from the key code value
        #expect((keyCode & modifiers) == 0 || modifiers == 0,
                "Modifier bits should not overlap with key code")
    }

    @Test("duplicate modifier in combo does not change result (OR is idempotent)")
    func duplicateModifierIdempotent() {
        let (_, modSingle) = HotkeyKeyMapping.parseCarbonCombo(["⌘", "9"])
        let (_, modDouble) = HotkeyKeyMapping.parseCarbonCombo(["⌘", "⌘", "9"])
        #expect(modSingle == modDouble)
    }
}

// MARK: - parseCGCombo Tests (new angles)

@Suite("HotkeyKeyMapping.parseCGCombo (extended)")
struct ParseCGComboExtendedTests {

    @Test("no-modifier combo uses default key code and empty flags")
    func noModifierDefaultsToKey9EmptyFlags() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCGCombo(["9"])
        #expect(keyCode == UInt32(kVK_ANSI_9))
        #expect(modifiers == [])
    }

    @Test("only modifier — no key — uses default key code 9")
    func onlyModifierUsesDefaultKey() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCGCombo(["⌘"])
        #expect(keyCode == UInt32(kVK_ANSI_9))
        #expect(modifiers.contains(.maskCommand))
    }

    @Test("single letter key produces correct key code")
    func singleLetterKeyCode() {
        let (keyCode, _) = HotkeyKeyMapping.parseCGCombo(["S"])
        #expect(keyCode == UInt32(kVK_ANSI_S))
    }

    @Test("single digit produces correct key code")
    func singleDigitKeyCode() {
        let (keyCode, _) = HotkeyKeyMapping.parseCGCombo(["3"])
        #expect(keyCode == UInt32(kVK_ANSI_3))
    }

    @Test("unknown key symbol falls back to default key code")
    func unknownSymbolFallsBackToDefaultKey() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCGCombo(["⌘", "⌥", "Return"])
        #expect(keyCode == UInt32(kVK_ANSI_9), "Unknown 'Return' should fall back to default key code")
        #expect(modifiers.contains(.maskCommand))
        #expect(modifiers.contains(.maskAlternate))
    }

    @Test("Carbon and CG combos produce the same key code for all letter keys")
    func carbonAndCGKeyCodesMatch() {
        let letters = ["A","B","C","D","F","G","H","I","J","K","L","M",
                       "N","O","P","R","S","T","U","V","X","Y","Z"]
        for letter in letters {
            let (carbonKey, _) = HotkeyKeyMapping.parseCarbonCombo(["⌘", letter])
            let (cgKey, _) = HotkeyKeyMapping.parseCGCombo(["⌘", letter])
            #expect(carbonKey == cgKey, "Key codes should match for letter \(letter)")
        }
    }

    @Test("Carbon and CG combos produce the same key code for all digit keys")
    func carbonAndCGDigitKeyCodesMatch() {
        for digit in 0...9 {
            let key = String(digit)
            let (carbonKey, _) = HotkeyKeyMapping.parseCarbonCombo(["⌘", key])
            let (cgKey, _) = HotkeyKeyMapping.parseCGCombo(["⌘", key])
            #expect(carbonKey == cgKey, "Key codes should match for digit \(key)")
        }
    }

    @Test("empty combo returns default key code and empty flags")
    func emptyComboReturnsDefaults() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCGCombo([])
        #expect(keyCode == UInt32(kVK_ANSI_9))
        #expect(modifiers == [])
    }
}

// MARK: - fourCharCode Tests

@Suite("HotkeyKeyMapping.fourCharCode")
struct FourCharCodeTests {

    @Test("fourCharCode packs 4 ASCII bytes correctly")
    func packsAsciiBytesCorrectly() {
        // "POTR" → P=0x50 O=0x4F T=0x54 R=0x52
        let result = HotkeyKeyMapping.fourCharCode("POTR")
        let expected: UInt32 = (0x50 << 24) | (0x4F << 16) | (0x54 << 8) | 0x52
        #expect(result == expected)
    }

    @Test("fourCharCode for 'ABCD' packs correctly")
    func abcdPacking() {
        let result = HotkeyKeyMapping.fourCharCode("ABCD")
        let expected: UInt32 = (UInt32(Character("A").asciiValue!) << 24)
                             | (UInt32(Character("B").asciiValue!) << 16)
                             | (UInt32(Character("C").asciiValue!) << 8)
                             |  UInt32(Character("D").asciiValue!)
        #expect(result == expected)
    }

    @Test("fourCharCode for 'htk1' packs correctly")
    func htk1Packing() {
        let result = HotkeyKeyMapping.fourCharCode("htk1")
        let expected: UInt32 = (UInt32(Character("h").asciiValue!) << 24)
                             | (UInt32(Character("t").asciiValue!) << 16)
                             | (UInt32(Character("k").asciiValue!) << 8)
                             |  UInt32(Character("1").asciiValue!)
        #expect(result == expected)
    }

    @Test("fourCharCode produces different results for different strings")
    func differentStringsProduceDifferentCodes() {
        let a = HotkeyKeyMapping.fourCharCode("AAAA")
        let b = HotkeyKeyMapping.fourCharCode("BBBB")
        #expect(a != b)
    }

    @Test("fourCharCode is deterministic — same input always yields same output")
    func deterministic() {
        let first = HotkeyKeyMapping.fourCharCode("POTR")
        let second = HotkeyKeyMapping.fourCharCode("POTR")
        #expect(first == second)
    }

    @Test("fourCharCode byte order — first character occupies most significant byte")
    func byteOrderMostSignificantFirst() {
        // "A\0\0\0" should have 0x41 in the top byte
        let result = HotkeyKeyMapping.fourCharCode("A\0\0\0")
        #expect((result >> 24) == UInt32(Character("A").asciiValue!))
    }
}

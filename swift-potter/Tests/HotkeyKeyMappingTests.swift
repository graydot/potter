import XCTest
@testable import Potter
import Carbon

final class HotkeyKeyMappingTests: TestBase {

    // MARK: - Carbon Combo Parsing

    func testParseCarbonComboDefaultKey() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCarbonCombo(["⌘", "⇧", "9"])
        XCTAssertEqual(keyCode, UInt32(kVK_ANSI_9))
        XCTAssertEqual(modifiers, UInt32(cmdKey) | UInt32(shiftKey))
    }

    func testParseCarbonComboLetterKey() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCarbonCombo(["⌘", "⌥", "K"])
        XCTAssertEqual(keyCode, UInt32(kVK_ANSI_K))
        XCTAssertEqual(modifiers, UInt32(cmdKey) | UInt32(optionKey))
    }

    func testParseCarbonComboAllModifiers() {
        let (_, modifiers) = HotkeyKeyMapping.parseCarbonCombo(["⌘", "⌥", "⌃", "⇧", "9"])
        let expected = UInt32(cmdKey) | UInt32(optionKey) | UInt32(controlKey) | UInt32(shiftKey)
        XCTAssertEqual(modifiers, expected)
    }

    func testParseCarbonComboSingleModifiers() {
        let (_, cmdMod) = HotkeyKeyMapping.parseCarbonCombo(["⌘", "9"])
        XCTAssertEqual(cmdMod, UInt32(cmdKey))

        let (_, optMod) = HotkeyKeyMapping.parseCarbonCombo(["⌥", "9"])
        XCTAssertEqual(optMod, UInt32(optionKey))

        let (_, ctrlMod) = HotkeyKeyMapping.parseCarbonCombo(["⌃", "9"])
        XCTAssertEqual(ctrlMod, UInt32(controlKey))

        let (_, shiftMod) = HotkeyKeyMapping.parseCarbonCombo(["⇧", "9"])
        XCTAssertEqual(shiftMod, UInt32(shiftKey))
    }

    // MARK: - CG Combo Parsing

    func testParseCGComboDefaultKey() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCGCombo(["⌘", "⇧", "9"])
        XCTAssertEqual(keyCode, UInt32(kVK_ANSI_9))
        XCTAssertTrue(modifiers.contains(.maskCommand))
        XCTAssertTrue(modifiers.contains(.maskShift))
        XCTAssertFalse(modifiers.contains(.maskAlternate))
        XCTAssertFalse(modifiers.contains(.maskControl))
    }

    func testParseCGComboLetterKey() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCGCombo(["⌘", "⌥", "K"])
        XCTAssertEqual(keyCode, UInt32(kVK_ANSI_K))
        XCTAssertTrue(modifiers.contains(.maskCommand))
        XCTAssertTrue(modifiers.contains(.maskAlternate))
    }

    func testParseCGComboAllModifiers() {
        let (_, modifiers) = HotkeyKeyMapping.parseCGCombo(["⌘", "⌥", "⌃", "⇧", "9"])
        XCTAssertTrue(modifiers.contains(.maskCommand))
        XCTAssertTrue(modifiers.contains(.maskAlternate))
        XCTAssertTrue(modifiers.contains(.maskControl))
        XCTAssertTrue(modifiers.contains(.maskShift))
    }

    // MARK: - Key Code Coverage

    func testAllLetterKeysMapCorrectly() {
        let letters = ["A", "B", "C", "D", "F", "G", "H", "I", "J", "K", "L", "M",
                       "N", "O", "P", "R", "S", "T", "U", "V", "X", "Y", "Z"]
        for letter in letters {
            let (keyCode, _) = HotkeyKeyMapping.parseCarbonCombo(["⌘", letter])
            XCTAssertNotEqual(keyCode, UInt32(kVK_ANSI_9), "Letter \(letter) should not fall back to default key code")
        }
    }

    func testAllDigitKeysMapCorrectly() {
        let expectedCodes: [String: Int] = [
            "0": kVK_ANSI_0, "1": kVK_ANSI_1, "2": kVK_ANSI_2, "3": kVK_ANSI_3,
            "4": kVK_ANSI_4, "5": kVK_ANSI_5, "6": kVK_ANSI_6, "7": kVK_ANSI_7,
            "8": kVK_ANSI_8, "9": kVK_ANSI_9,
        ]
        for (digit, expected) in expectedCodes {
            let (keyCode, _) = HotkeyKeyMapping.parseCarbonCombo(["⌘", digit])
            XCTAssertEqual(keyCode, UInt32(expected), "Digit \(digit) should map to correct key code")
        }
    }

    // MARK: - Carbon and CG Consistency

    func testCarbonAndCGProduceSameKeyCodes() {
        let combos: [[String]] = [
            ["⌘", "⇧", "9"],
            ["⌘", "⌥", "K"],
            ["⌃", "A"],
            ["⌘", "⌥", "⌃", "⇧", "0"],
        ]
        for combo in combos {
            let (carbonKey, _) = HotkeyKeyMapping.parseCarbonCombo(combo)
            let (cgKey, _) = HotkeyKeyMapping.parseCGCombo(combo)
            XCTAssertEqual(carbonKey, cgKey, "Key codes should match for combo \(combo)")
        }
    }

    // MARK: - FourCharCode

    func testFourCharCode() {
        let result = HotkeyKeyMapping.fourCharCode("POTR")
        let expected: UInt32 = (UInt32(0x50) << 24) | (UInt32(0x4F) << 16) | (UInt32(0x54) << 8) | UInt32(0x52)
        XCTAssertEqual(result, expected)
    }

    // MARK: - Modifier Symbols Set

    func testModifierSymbolsContainsAllModifiers() {
        XCTAssertTrue(HotkeyKeyMapping.modifierSymbols.contains("⌘"))
        XCTAssertTrue(HotkeyKeyMapping.modifierSymbols.contains("⌥"))
        XCTAssertTrue(HotkeyKeyMapping.modifierSymbols.contains("⌃"))
        XCTAssertTrue(HotkeyKeyMapping.modifierSymbols.contains("⇧"))
        XCTAssertFalse(HotkeyKeyMapping.modifierSymbols.contains("9"))
        XCTAssertFalse(HotkeyKeyMapping.modifierSymbols.contains("A"))
    }

    // MARK: - Edge Cases

    func testEmptyComboReturnsDefaults() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCarbonCombo([])
        XCTAssertEqual(keyCode, UInt32(kVK_ANSI_9), "Empty combo should default to key code 9")
        XCTAssertEqual(modifiers, 0, "Empty combo should have no modifiers")
    }

    func testUnknownKeyIgnored() {
        let (keyCode, modifiers) = HotkeyKeyMapping.parseCarbonCombo(["⌘", "🎯"])
        XCTAssertEqual(keyCode, UInt32(kVK_ANSI_9), "Unknown key should fall back to default")
        XCTAssertEqual(modifiers, UInt32(cmdKey), "Known modifier should still be parsed")
    }
}

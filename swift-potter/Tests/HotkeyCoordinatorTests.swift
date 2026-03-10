import XCTest
@testable import Potter
import Carbon

final class HotkeyCoordinatorTests: TestBase {

    // MARK: - Test 1: parseHotkeyCombo with default key ⌘⇧9

    func testParseHotkeyComboDefaultKey() {
        let coordinator = HotkeyCoordinator()
        let (keyCode, modifiers) = coordinator.parseHotkeyCombo(["⌘", "⇧", "9"])

        XCTAssertEqual(keyCode, UInt32(kVK_ANSI_9), "Key code should be kVK_ANSI_9 for '9'")
        XCTAssertEqual(modifiers, UInt32(cmdKey) | UInt32(shiftKey), "Modifiers should be cmdKey | shiftKey")
    }

    // MARK: - Test 2: parseHotkeyCombo with letter key ⌘⌥K

    func testParseHotkeyComboLetterKey() {
        let coordinator = HotkeyCoordinator()
        let (keyCode, modifiers) = coordinator.parseHotkeyCombo(["⌘", "⌥", "K"])

        XCTAssertEqual(keyCode, UInt32(kVK_ANSI_K), "Key code should be kVK_ANSI_K for 'K'")
        XCTAssertEqual(modifiers, UInt32(cmdKey) | UInt32(optionKey), "Modifiers should be cmdKey | optionKey")
    }

    // MARK: - Test 3: parseHotkeyCombo modifier symbols

    func testParseHotkeyComboModifiers() {
        let coordinator = HotkeyCoordinator()

        // Command only
        let (_, cmdMod) = coordinator.parseHotkeyCombo(["⌘", "9"])
        XCTAssertEqual(cmdMod, UInt32(cmdKey), "⌘ should map to cmdKey")

        // Option only
        let (_, optMod) = coordinator.parseHotkeyCombo(["⌥", "9"])
        XCTAssertEqual(optMod, UInt32(optionKey), "⌥ should map to optionKey")

        // Control only
        let (_, ctrlMod) = coordinator.parseHotkeyCombo(["⌃", "9"])
        XCTAssertEqual(ctrlMod, UInt32(controlKey), "⌃ should map to controlKey")

        // Shift only
        let (_, shiftMod) = coordinator.parseHotkeyCombo(["⇧", "9"])
        XCTAssertEqual(shiftMod, UInt32(shiftKey), "⇧ should map to shiftKey")

        // All four modifiers
        let (_, allMod) = coordinator.parseHotkeyCombo(["⌘", "⌥", "⌃", "⇧", "9"])
        let expected = UInt32(cmdKey) | UInt32(optionKey) | UInt32(controlKey) | UInt32(shiftKey)
        XCTAssertEqual(allMod, expected, "All four modifiers should combine correctly")
    }

    // MARK: - Test 4: fourCharCode

    func testFourCharCode() {
        let coordinator = HotkeyCoordinator()
        let result = coordinator.fourCharCode("POTR")

        // "POTR" = P(0x50) O(0x4F) T(0x54) R(0x52)
        // = 0x50 << 24 | 0x4F << 16 | 0x54 << 8 | 0x52
        let expected: UInt32 = (UInt32(0x50) << 24) | (UInt32(0x4F) << 16) | (UInt32(0x54) << 8) | UInt32(0x52)
        XCTAssertEqual(result, expected, "fourCharCode('POTR') should produce correct UInt32")
    }

    // MARK: - Test 5: Default hotkey combo

    func testCurrentHotkeyComboDefault() {
        let coordinator = HotkeyCoordinator()
        XCTAssertEqual(coordinator.currentHotkeyCombo, ["⌘", "⇧", "9"],
                       "Default hotkey combo should be ⌘⇧9")
    }

    // MARK: - Test 6: updateHotkey changes currentHotkeyCombo

    func testUpdateHotkeyChangesCurrentCombo() {
        let coordinator = HotkeyCoordinator()
        coordinator.updateHotkey(["⌘", "⌥", "K"])
        XCTAssertEqual(coordinator.currentHotkeyCombo, ["⌘", "⌥", "K"],
                       "currentHotkeyCombo should reflect the updated combo")
    }

    // MARK: - Test 7: updateHotkey saves to UserDefaults

    func testUpdateHotkeySavesToUserDefaults() {
        let coordinator = HotkeyCoordinator()
        let newCombo = ["⌘", "⌥", "K"]
        coordinator.updateHotkey(newCombo)

        let saved = UserDefaults.standard.array(forKey: HotkeyConstants.userDefaultsKey) as? [String]
        XCTAssertEqual(saved, newCombo,
                       "updateHotkey should persist the combo to UserDefaults under 'global_hotkey'")
    }
}

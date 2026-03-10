import XCTest
@testable import Potter

final class NSEventHotkeyProviderTests: TestBase {

    // MARK: - Default State

    func testDefaultHotkeyCombo() {
        let provider = NSEventHotkeyProvider()
        XCTAssertEqual(provider.currentHotkeyCombo, ["⌘", "⇧", "9"])
    }

    // MARK: - Register / Unregister

    func testRegisterUpdatesComboAndStoresHandler() {
        let provider = NSEventHotkeyProvider()
        var handlerCalled = false

        provider.register(hotkey: ["⌘", "⌥", "K"]) {
            handlerCalled = true
        }

        XCTAssertEqual(provider.currentHotkeyCombo, ["⌘", "⌥", "K"])
        // Handler stored but not called yet
        XCTAssertFalse(handlerCalled)
    }

    func testUnregisterDoesNotCrash() {
        let provider = NSEventHotkeyProvider()
        provider.register(hotkey: ["⌘", "⇧", "9"]) { }
        // Should not crash even if monitors can't be created in test environment
        provider.unregister()
    }

    // MARK: - Update Hotkey

    func testUpdateHotkeyChangesCombo() {
        let provider = NSEventHotkeyProvider()
        provider.register(hotkey: ["⌘", "⇧", "9"]) { }

        provider.updateHotkey(["⌘", "⌥", "K"])
        XCTAssertEqual(provider.currentHotkeyCombo, ["⌘", "⌥", "K"])
    }

    func testUpdateHotkeySavesToUserDefaults() {
        let provider = NSEventHotkeyProvider()
        let newCombo = ["⌘", "⌥", "K"]
        provider.updateHotkey(newCombo)

        let saved = UserDefaults.standard.array(forKey: HotkeyConstants.userDefaultsKey) as? [String]
        XCTAssertEqual(saved, newCombo)
    }

    // MARK: - Enable / Disable

    func testDisableAndEnableDoNotCrash() {
        let provider = NSEventHotkeyProvider()
        provider.register(hotkey: ["⌘", "⇧", "9"]) { }

        provider.disableGlobalHotkey()
        provider.enableGlobalHotkey()
        // Verifying no crash and that the provider remains functional
        XCTAssertEqual(provider.currentHotkeyCombo, ["⌘", "⇧", "9"])
    }

    // MARK: - Setup

    func testSetupLoadsFromUserDefaults() {
        let savedCombo = ["⌘", "⌥", "T"]
        UserDefaults.standard.set(savedCombo, forKey: HotkeyConstants.userDefaultsKey)

        let provider = NSEventHotkeyProvider()
        provider.setup { }

        XCTAssertEqual(provider.currentHotkeyCombo, savedCombo)
    }

    func testSetupUsesDefaultWhenNoSavedHotkey() {
        UserDefaults.standard.removeObject(forKey: HotkeyConstants.userDefaultsKey)

        let provider = NSEventHotkeyProvider()
        provider.setup { }

        XCTAssertEqual(provider.currentHotkeyCombo, HotkeyConstants.defaultHotkey)
    }

    // MARK: - HotkeyProvider Protocol Conformance

    func testConformsToHotkeyProvider() {
        let provider = NSEventHotkeyProvider()
        XCTAssertTrue(provider is HotkeyProvider)
    }

    // MARK: - Deinit Cleanup

    func testDeinitDoesNotCrash() {
        var provider: NSEventHotkeyProvider? = NSEventHotkeyProvider()
        provider?.register(hotkey: ["⌘", "⇧", "9"]) { }
        provider = nil // Should clean up monitors without crashing
        XCTAssertNil(provider)
    }
}

import XCTest
@testable import Potter

// MARK: - Mock Icon State Delegate

class MockIconStateDelegate: IconStateDelegate {
    var processingCalled = false
    var successCalled = false
    var normalCalled = false
    var lastError: String?

    func setProcessingState() { processingCalled = true }
    func setSuccessState() { successCalled = true }
    func setNormalState() { normalCalled = true }
    func setErrorState(message: String) { lastError = message }
}

// MARK: - PotterCore Dependency Injection Tests

@MainActor
final class PotterCoreDITests: TestBase {

    // MARK: - Test 1: Default initialization (backward compatible)
    // This test should PASS because PotterCore() already works with no args.
    func testDefaultInitialization() {
        let core = PotterCore()
        XCTAssertNotNil(core, "PotterCore should be creatable with default init")
    }

    // MARK: - Test 2: Injected LLMManager
    // This test should FAIL because PotterCore's init doesn't accept an llmManager parameter yet.
    func testInjectedLLMManager() {
        let mockManager = LLMManager()
        let core = PotterCore(llmManager: mockManager)
        XCTAssertNotNil(core, "PotterCore should be creatable with injected LLMManager")
    }

    // MARK: - Test 3: getLLMManager returns the injected manager
    // This test should FAIL because PotterCore's init doesn't accept an llmManager parameter yet.
    func testGetLLMManagerReturnsInjectedManager() {
        let mockManager = LLMManager()
        let core = PotterCore(llmManager: mockManager)

        let returned = core.getLLMManager()
        XCTAssertTrue(returned === mockManager, "getLLMManager() should return the same instance that was injected")
    }

    // MARK: - Test 4: Icon delegate still works with DI-constructed core
    // This test should FAIL because PotterCore's init doesn't accept an llmManager parameter yet.
    func testIconDelegateStillWorksWithDI() {
        let mockManager = LLMManager()
        let core = PotterCore(llmManager: mockManager)
        let delegate = MockIconStateDelegate()

        core.iconDelegate = delegate
        XCTAssertNotNil(core.iconDelegate, "iconDelegate should be settable on DI-constructed PotterCore")
    }

    // MARK: - Test 5: setPromptMode doesn't crash with DI
    // This test should FAIL because PotterCore's init doesn't accept an llmManager parameter yet.
    func testSetPromptModeStillWorksWithDI() {
        let mockManager = LLMManager()
        let core = PotterCore(llmManager: mockManager)

        // Should not crash
        core.setPromptMode(.casual)
        core.setPromptMode(.formal)
        core.setPromptMode(.summarize)
    }

    // MARK: - Test 6: updateHotkey stores the new combo with DI
    // This test should FAIL because PotterCore's init doesn't accept an llmManager parameter yet.
    func testUpdateHotkeyStillWorksWithDI() {
        let mockManager = LLMManager()
        let core = PotterCore(llmManager: mockManager)
        let newCombo = ["⌘", "⌥", "K"]

        // Should not crash - stores the new hotkey combo
        core.updateHotkey(newCombo)
    }

    // MARK: - Test 7: Injected HotkeyProvider is used
    func testInjectedHotkeyProviderIsUsed() {
        let mockProvider = MockHotkeyProvider()
        let core = PotterCore(hotkeyProvider: mockProvider)

        core.setup()

        XCTAssertTrue(mockProvider.setupCalled, "setup() should call through to injected HotkeyProvider")
    }

    // MARK: - Test 8: Injected HotkeyProvider receives updateHotkey
    func testInjectedHotkeyProviderReceivesUpdate() {
        let mockProvider = MockHotkeyProvider()
        let core = PotterCore(hotkeyProvider: mockProvider)

        core.setup()
        core.updateHotkey(["⌘", "⌥", "K"])

        XCTAssertEqual(mockProvider.lastUpdatedHotkey, ["⌘", "⌥", "K"])
    }

    // MARK: - Test 9: Injected HotkeyProvider receives disable/enable
    func testInjectedHotkeyProviderDisableEnable() {
        let mockProvider = MockHotkeyProvider()
        let core = PotterCore(hotkeyProvider: mockProvider)

        core.setup()
        core.disableGlobalHotkey()
        XCTAssertTrue(mockProvider.disableCalled)

        core.enableGlobalHotkey()
        XCTAssertTrue(mockProvider.enableCalled)
    }
}

// MARK: - Mock HotkeyProvider for DI Tests

class MockHotkeyProvider: HotkeyProvider {
    var currentHotkeyCombo: [String] = HotkeyConstants.defaultHotkey
    var setupCalled = false
    var registerCalled = false
    var unregisterCalled = false
    var disableCalled = false
    var enableCalled = false
    var lastUpdatedHotkey: [String]?
    var storedHandler: (() -> Void)?

    func register(hotkey: [String], handler: @escaping () -> Void) {
        registerCalled = true
        currentHotkeyCombo = hotkey
        storedHandler = handler
    }

    func unregister() {
        unregisterCalled = true
    }

    func setup(handler: @escaping () -> Void) {
        setupCalled = true
        storedHandler = handler
    }

    func updateHotkey(_ newHotkey: [String]) {
        lastUpdatedHotkey = newHotkey
        currentHotkeyCombo = newHotkey
    }

    func disableGlobalHotkey() {
        disableCalled = true
    }

    func enableGlobalHotkey() {
        enableCalled = true
    }
}

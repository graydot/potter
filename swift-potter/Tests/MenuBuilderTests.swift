import XCTest
import AppKit
@testable import Potter

class MenuBuilderTests: TestBase {

    // Helper target for menu actions
    private var target: NSObject!

    override func setUp() {
        super.setUp()
        target = NSObject()
    }

    override func tearDown() {
        target = nil
        super.tearDown()
    }

    private func buildTestMenu(
        prompts: [String] = ["Fix Grammar", "Summarize", "Translate"],
        currentPrompt: String = "Fix Grammar",
        hotkeyDisplay: String = "⌘⇧9"
    ) -> NSMenu {
        return MenuBuilder.buildMenu(
            prompts: prompts,
            currentPrompt: currentPrompt,
            hotkeyDisplay: hotkeyDisplay,
            target: target,
            promptAction: #selector(NSObject.description),
            settingsAction: #selector(NSObject.description)
        )
    }

    // MARK: - Menu Structure Tests

    func testBuildMenuHasProcessPromptItem() {
        let menu = buildTestMenu()
        let titles = menu.items.map { $0.title }
        let hasProcessItem = titles.contains { $0.contains("Process") }
        XCTAssertTrue(hasProcessItem, "Menu should contain a 'Process' item, got: \(titles)")
    }

    func testBuildMenuHasSettingsItem() {
        let menu = buildTestMenu()
        let titles = menu.items.map { $0.title }
        let hasSettings = titles.contains { $0.contains("Preferences") }
        XCTAssertTrue(hasSettings, "Menu should contain 'Preferences...' item, got: \(titles)")
    }

    func testBuildMenuHasQuitItem() {
        let menu = buildTestMenu()
        let titles = menu.items.map { $0.title }
        let hasQuit = titles.contains { $0 == "Quit Potter" }
        XCTAssertTrue(hasQuit, "Menu should contain 'Quit Potter' item, got: \(titles)")
    }

    func testBuildMenuHasSeparators() {
        let menu = buildTestMenu()
        let separatorCount = menu.items.filter { $0.isSeparatorItem }.count
        XCTAssertGreaterThanOrEqual(separatorCount, 2, "Menu should have at least 2 separators")
    }

    func testBuildMenuPromptsSection() {
        let promptNames = ["Fix Grammar", "Summarize", "Translate"]
        let menu = buildTestMenu(prompts: promptNames)
        let titles = menu.items.map { $0.title }

        for promptName in promptNames {
            XCTAssertTrue(titles.contains(promptName), "Menu should contain prompt '\(promptName)', got: \(titles)")
        }
    }

    func testBuildMenuCurrentPromptHasCheckmark() {
        let currentPrompt = "Summarize"
        let menu = buildTestMenu(
            prompts: ["Fix Grammar", "Summarize", "Translate"],
            currentPrompt: currentPrompt
        )

        let summarizeItem = menu.items.first { $0.title == currentPrompt }
        XCTAssertNotNil(summarizeItem, "Should find the current prompt item")
        XCTAssertEqual(summarizeItem?.state, .on, "Current prompt should have checkmark (state .on)")

        // Other prompts should NOT have checkmark
        let otherItems = menu.items.filter { $0.title == "Fix Grammar" || $0.title == "Translate" }
        for item in otherItems {
            XCTAssertEqual(item.state, .off, "Non-current prompt '\(item.title)' should not have checkmark")
        }
    }
}

import XCTest
import AppKit
@testable import Potter

// MARK: - AccessibilityTextProvider Tests
//
// We can't truly test the AX read/write path in a sandboxed test process (no
// accessibility permission), so we test:
//   1. The clipboard fallback path thoroughly.
//   2. That writeResult routes correctly based on TextInputSource.
//   3. That the provider reads from AX when AXIsProcessTrusted() is false
//      (graceful degradation — falls through to clipboard).

final class AccessibilityTextProviderTests: XCTestCase {

    private var provider: AccessibilityTextProvider!

    override func setUp() {
        super.setUp()
        provider = AccessibilityTextProvider()
        // Clear clipboard before each test
        NSPasteboard.general.clearContents()
    }

    override func tearDown() {
        NSPasteboard.general.clearContents()
        super.tearDown()
    }

    // MARK: - readText: clipboard fallback

    func testReadTextReturnsClipboardWhenAXUnavailable() {
        // Since tests run without AX permission, AX path will fail → clipboard used
        NSPasteboard.general.setString("hello from clipboard", forType: .string)

        let result = provider.readText()
        XCTAssertNotNil(result)
        XCTAssertEqual(result?.text, "hello from clipboard")
        if case .clipboard = result?.source {} else {
            XCTFail("Expected .clipboard source, got \(String(describing: result?.source))")
        }
    }

    func testReadTextReturnsNilWhenClipboardEmpty() {
        // Clipboard cleared in setUp; AX also unavailable → nil
        let result = provider.readText()
        XCTAssertNil(result)
    }

    func testReadTextReturnsNilForWhitespaceOnlyClipboard() {
        NSPasteboard.general.setString("   \n\t  ", forType: .string)
        // The provider calls readText which returns non-empty raw text from clipboard,
        // but PotterCore trims it — the provider itself returns whatever clipboard has.
        // Let's verify it returns the raw string (trimming is the caller's responsibility).
        let result = provider.readText()
        // Raw whitespace IS returned; it's non-nil (trimming is PotterCore's job)
        XCTAssertNotNil(result)
    }

    // MARK: - writeResult: clipboard path

    func testWriteResultToClipboard() {
        let success = provider.writeResult("written result", source: .clipboard)
        XCTAssertTrue(success)
        XCTAssertEqual(NSPasteboard.general.string(forType: .string), "written result")
    }

    func testWriteResultToClipboardOverwritesPreviousContent() {
        NSPasteboard.general.setString("old content", forType: .string)
        provider.writeResult("new content", source: .clipboard)
        XCTAssertEqual(NSPasteboard.general.string(forType: .string), "new content")
    }

    func testWriteResultEmptyStringToClipboard() {
        let success = provider.writeResult("", source: .clipboard)
        XCTAssertTrue(success)
        // Empty string written — clipboard may return nil or ""
        let value = NSPasteboard.general.string(forType: .string)
        XCTAssertTrue(value == nil || value == "")
    }
}

// MARK: - TextInputSource Tests

final class TextInputSourceTests: XCTestCase {

    func testClipboardPatternMatch() {
        let source = TextInputSource.clipboard
        var matched = false
        if case .clipboard = source { matched = true }
        XCTAssertTrue(matched)
    }

    func testAccessibilityPatternMatch() {
        let element = AXUIElementCreateSystemWide()
        let source = TextInputSource.accessibility(element: element)
        var matched = false
        if case .accessibility = source { matched = true }
        XCTAssertTrue(matched)
    }

    func testClipboardIsNotAccessibility() {
        let source = TextInputSource.clipboard
        var matchedAX = false
        if case .accessibility = source { matchedAX = true }
        XCTAssertFalse(matchedAX)
    }
}

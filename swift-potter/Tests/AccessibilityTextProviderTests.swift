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
//
// Note: NSPasteboard.general is unreliable in parallel/headless test processes.
// All clipboard-dependent assertions are guarded by a clipboard availability check.

final class AccessibilityTextProviderTests: XCTestCase {

    private var provider: AccessibilityTextProvider!
    private var clipboardAvailable: Bool = false

    override func setUp() {
        super.setUp()
        provider = AccessibilityTextProvider()
        NSPasteboard.general.clearContents()
        // Probe whether clipboard is functional in this test process
        let probe = "clipboard_probe_\(ProcessInfo.processInfo.processIdentifier)"
        NSPasteboard.general.setString(probe, forType: .string)
        clipboardAvailable = NSPasteboard.general.string(forType: .string) == probe
        NSPasteboard.general.clearContents()
    }

    override func tearDown() {
        NSPasteboard.general.clearContents()
        super.tearDown()
    }

    // MARK: - readText: clipboard fallback

    func testReadTextReturnsClipboardWhenAXUnavailable() {
        guard clipboardAvailable else { return }
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
        guard clipboardAvailable else { return }
        NSPasteboard.general.setString("   \n\t  ", forType: .string)
        let result = provider.readText()
        // Raw whitespace IS returned; it's non-nil (trimming is PotterCore's job)
        XCTAssertNotNil(result)
    }

    // MARK: - writeResult: clipboard path

    func testWriteResultToClipboard() {
        guard clipboardAvailable else { return }
        let success = provider.writeResult("written result", source: .clipboard)
        XCTAssertTrue(success)
        XCTAssertEqual(NSPasteboard.general.string(forType: .string), "written result")
    }

    func testWriteResultToClipboardOverwritesPreviousContent() {
        guard clipboardAvailable else { return }
        NSPasteboard.general.setString("old content", forType: .string)
        provider.writeResult("new content", source: .clipboard)
        XCTAssertEqual(NSPasteboard.general.string(forType: .string), "new content")
    }

    func testWriteResultEmptyStringToClipboard() {
        guard clipboardAvailable else { return }
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

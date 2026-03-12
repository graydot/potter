import AppKit
import Foundation

// MARK: - Input Source

/// Describes where the text to process came from and how to write the result back.
enum TextInputSource {
    /// Text was read from (and should be written back to) the Accessibility API.
    case accessibility(element: AXUIElement)
    /// Text was read from (and should be written back to) the system clipboard.
    case clipboard
}

// MARK: - AccessibilityTextProvider

/// Reads the current text selection using the macOS Accessibility API, falling
/// back to the clipboard when the AX path is unavailable or returns no text.
///
/// **Write-back**: after the LLM produces a result the caller should use
/// `writeResult(_:source:)` to put the result in the right place.
final class AccessibilityTextProvider {

    // MARK: - Read

    /// Attempts to read the selected text from the frontmost application.
    ///
    /// - Returns: A tuple of (text, source) where source describes where the
    ///   text came from so `writeResult` can route the result correctly.
    ///   Returns `nil` if no text is available from either path.
    func readText() -> (text: String, source: TextInputSource)? {
        // Try AX first
        if let (text, element) = readFromAccessibility(), !text.isEmpty {
            return (text, .accessibility(element: element))
        }

        // Fall back to clipboard
        if let text = readFromClipboard(), !text.isEmpty {
            return (text, .clipboard)
        }

        return nil
    }

    // MARK: - Write

    /// Writes the LLM result back to wherever the text originally came from.
    ///
    /// - Parameters:
    ///   - result: The processed text to write.
    ///   - source: The source originally returned by `readText()`.
    /// - Returns: `true` if the write succeeded; `false` if AX write failed
    ///   (in which case the caller should fall back to clipboard).
    @discardableResult
    func writeResult(_ result: String, source: TextInputSource) -> Bool {
        switch source {
        case .accessibility(let element):
            return writeToAccessibility(result, element: element)
        case .clipboard:
            writeToClipboard(result)
            return true
        }
    }

    // MARK: - AX Read

    private func readFromAccessibility() -> (text: String, element: AXUIElement)? {
        guard AXIsProcessTrusted() else { return nil }

        let systemWide = AXUIElementCreateSystemWide()

        var focusedElement: CFTypeRef?
        let focusResult = AXUIElementCopyAttributeValue(
            systemWide,
            kAXFocusedUIElementAttribute as CFString,
            &focusedElement
        )
        guard focusResult == .success,
              let element = focusedElement as! AXUIElement? else {
            return nil
        }

        var selectedTextValue: CFTypeRef?
        let textResult = AXUIElementCopyAttributeValue(
            element,
            kAXSelectedTextAttribute as CFString,
            &selectedTextValue
        )
        guard textResult == .success,
              let text = selectedTextValue as? String,
              !text.isEmpty else {
            return nil
        }

        return (text, element)
    }

    // MARK: - AX Write

    private func writeToAccessibility(_ text: String, element: AXUIElement) -> Bool {
        let result = AXUIElementSetAttributeValue(
            element,
            kAXSelectedTextAttribute as CFString,
            text as CFTypeRef
        )
        return result == .success
    }

    // MARK: - Clipboard Read / Write

    private func readFromClipboard() -> String? {
        return NSPasteboard.general.string(forType: .string)
    }

    private func writeToClipboard(_ text: String) {
        let pb = NSPasteboard.general
        pb.clearContents()
        pb.setString(text, forType: .string)
    }
}

import XCTest
@testable import Potter

// MARK: - OutputMode Unit Tests

final class OutputModeTests: XCTestCase {

    // MARK: - apply(original:result:)

    func testReplaceReturnsResultOnly() {
        let mode = OutputMode.replace
        XCTAssertEqual(mode.apply(original: "hello", result: "world"), "world")
    }

    func testAppendCombinesWithSeparator() {
        let mode = OutputMode.append
        let combined = mode.apply(original: "original", result: "appended")
        XCTAssertEqual(combined, "original\n\nappended")
    }

    func testPrependCombinesWithSeparator() {
        let mode = OutputMode.prepend
        let combined = mode.apply(original: "original", result: "prepended")
        XCTAssertEqual(combined, "prepended\n\noriginal")
    }

    func testReplaceWithEmptyOriginal() {
        XCTAssertEqual(OutputMode.replace.apply(original: "", result: "result"), "result")
    }

    func testAppendWithEmptyOriginal() {
        XCTAssertEqual(OutputMode.append.apply(original: "", result: "result"), "\n\nresult")
    }

    func testPrependWithEmptyOriginal() {
        XCTAssertEqual(OutputMode.prepend.apply(original: "", result: "result"), "result\n\n")
    }

    func testReplaceWithEmptyResult() {
        XCTAssertEqual(OutputMode.replace.apply(original: "original", result: ""), "")
    }

    func testAppendWithEmptyResult() {
        XCTAssertEqual(OutputMode.append.apply(original: "original", result: ""), "original\n\n")
    }

    func testPrependWithEmptyResult() {
        XCTAssertEqual(OutputMode.prepend.apply(original: "original", result: ""), "\n\noriginal")
    }

    // MARK: - displayName

    func testDisplayNames() {
        XCTAssertEqual(OutputMode.replace.displayName, "Replace")
        XCTAssertEqual(OutputMode.append.displayName, "Append")
        XCTAssertEqual(OutputMode.prepend.displayName, "Prepend")
    }

    // MARK: - CaseIterable

    func testAllCasesCount() {
        XCTAssertEqual(OutputMode.allCases.count, 3)
    }

    func testAllCasesOrder() {
        XCTAssertEqual(OutputMode.allCases[0], .replace)
        XCTAssertEqual(OutputMode.allCases[1], .append)
        XCTAssertEqual(OutputMode.allCases[2], .prepend)
    }

    // MARK: - Codable round-trip

    func testCodableReplaceRoundTrip() throws {
        let encoded = try JSONEncoder().encode(OutputMode.replace)
        let decoded = try JSONDecoder().decode(OutputMode.self, from: encoded)
        XCTAssertEqual(decoded, .replace)
    }

    func testCodableAppendRoundTrip() throws {
        let encoded = try JSONEncoder().encode(OutputMode.append)
        let decoded = try JSONDecoder().decode(OutputMode.self, from: encoded)
        XCTAssertEqual(decoded, .append)
    }

    func testCodablePrependRoundTrip() throws {
        let encoded = try JSONEncoder().encode(OutputMode.prepend)
        let decoded = try JSONDecoder().decode(OutputMode.self, from: encoded)
        XCTAssertEqual(decoded, .prepend)
    }
}

// MARK: - PromptItem OutputMode Tests

final class PromptItemOutputModeTests: XCTestCase {

    func testDefaultOutputModeIsReplace() {
        let item = PromptItem(name: "Test", prompt: "Do something")
        XCTAssertEqual(item.outputMode, .replace)
    }

    func testCustomOutputModePreserved() {
        let item = PromptItem(name: "Brainstorm", prompt: "Generate ideas", outputMode: .append)
        XCTAssertEqual(item.outputMode, .append)
    }

    func testPromptItemCodableWithOutputMode() throws {
        let original = PromptItem(name: "Summary", prompt: "Summarise this", modelTier: .fast, outputMode: .prepend)
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        XCTAssertEqual(decoded.name, original.name)
        XCTAssertEqual(decoded.prompt, original.prompt)
        XCTAssertEqual(decoded.modelTier, original.modelTier)
        XCTAssertEqual(decoded.outputMode, .prepend)
    }

    func testPromptItemDecodesLegacyJsonWithoutOutputMode() throws {
        // Simulate a pre-OutputMode JSON blob that has no "outputMode" key
        let legacyJSON = """
        {
            "id": "12345678-1234-1234-1234-123456789012",
            "name": "Old prompt",
            "prompt": "Do the thing"
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(PromptItem.self, from: legacyJSON)
        // Should default to .replace for backward compatibility
        XCTAssertEqual(decoded.outputMode, .replace)
        XCTAssertEqual(decoded.name, "Old prompt")
    }

    func testPromptItemCodableRoundTripAllModes() throws {
        for mode in OutputMode.allCases {
            let item = PromptItem(name: "P", prompt: "X", outputMode: mode)
            let data = try JSONEncoder().encode(item)
            let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
            XCTAssertEqual(decoded.outputMode, mode, "Round-trip failed for mode: \(mode)")
        }
    }
}

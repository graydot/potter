import XCTest
@testable import Potter

class PromptItemTests: TestBase {

    // MARK: - Basic Construction

    func testPromptItemDefaultTierIsNil() {
        let item = PromptItem(name: "Test", prompt: "Do something")
        XCTAssertNil(item.modelTier)
    }

    func testPromptItemWithTier() {
        let item = PromptItem(name: "Fast Task", prompt: "Summarize", modelTier: .fast)
        XCTAssertEqual(item.modelTier, .fast)
    }

    // MARK: - Codable

    func testEncodeDecodeWithTier() throws {
        let item = PromptItem(name: "Thinking", prompt: "Analyze deeply", modelTier: .thinking)
        let data = try JSONEncoder().encode(item)
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        XCTAssertEqual(decoded.name, "Thinking")
        XCTAssertEqual(decoded.prompt, "Analyze deeply")
        XCTAssertEqual(decoded.modelTier, .thinking)
    }

    func testEncodeDecodeWithNilTier() throws {
        let item = PromptItem(name: "Default", prompt: "Just do it")
        let data = try JSONEncoder().encode(item)
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        XCTAssertEqual(decoded.name, "Default")
        XCTAssertNil(decoded.modelTier)
    }

    func testBackwardCompatibility() throws {
        // Simulate old JSON format without modelTier field
        let json = """
        {"id": "00000000-0000-0000-0000-000000000001", "name": "Old Prompt", "prompt": "Old text"}
        """
        let data = json.data(using: .utf8)!
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        XCTAssertEqual(decoded.name, "Old Prompt")
        XCTAssertEqual(decoded.prompt, "Old text")
        XCTAssertNil(decoded.modelTier, "Old prompts without modelTier should decode with nil")
    }

    func testBackwardCompatibilityWithoutId() throws {
        // Even older format without id
        let json = """
        {"name": "Ancient Prompt", "prompt": "Ancient text"}
        """
        let data = json.data(using: .utf8)!
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        XCTAssertEqual(decoded.name, "Ancient Prompt")
        XCTAssertNil(decoded.modelTier)
        XCTAssertNotNil(decoded.id) // Should generate a new UUID
    }

    // MARK: - Equality

    func testEqualityIgnoresTier() {
        var item1 = PromptItem(name: "Test", prompt: "Prompt", modelTier: .fast)
        var item2 = PromptItem(name: "Test", prompt: "Prompt", modelTier: .thinking)
        // Equality is based on id, not content
        XCTAssertNotEqual(item1, item2, "Different IDs should not be equal")

        // Same id should be equal regardless of tier
        item2 = item1
        item2.modelTier = .thinking
        XCTAssertEqual(item1, item2, "Same ID should be equal even with different tiers")
    }

    // MARK: - All Tiers

    func testAllTiersEncodeDecode() throws {
        for tier in ModelTier.allCases {
            let item = PromptItem(name: "Tier \(tier.displayName)", prompt: "Prompt", modelTier: tier)
            let data = try JSONEncoder().encode(item)
            let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
            XCTAssertEqual(decoded.modelTier, tier)
        }
    }
}

import XCTest
import Foundation
@testable import Potter

class PromptManagerTests: XCTestCase {
    var tempDirectoryURL: URL!
    var originalCurrentDirectory: String!
    
    override func setUp() {
        super.setUp()
        
        // Save original directory
        originalCurrentDirectory = FileManager.default.currentDirectoryPath
        
        // Create temporary directory for tests
        tempDirectoryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("PotterTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory to use config/ subdirectory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
    }
    
    override func tearDown() {
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        super.tearDown()
    }
    
    func testLoadPromptsCreatesDefaultFile_DISABLED() {
        let manager = PromptManager.shared
        let prompts = manager.loadPrompts()
        
        // Should create default prompts
        XCTAssertGreaterThan(prompts.count, 0)
        XCTAssertTrue(prompts.contains { $0.name == "summarize" })
        XCTAssertTrue(prompts.contains { $0.name == "formal" })
        XCTAssertTrue(prompts.contains { $0.name == "casual" })
        XCTAssertTrue(prompts.contains { $0.name == "friendly" })
        
        // Check file was created
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        let promptsFile = configDir.appendingPathComponent("prompts.json")
        XCTAssertTrue(FileManager.default.fileExists(atPath: promptsFile.path))
    }
    
    func testSaveAndLoadPrompts() {
        let manager = PromptManager.shared
        let testPrompts = [
            PromptItem(name: "test1", prompt: "Test prompt 1"),
            PromptItem(name: "test2", prompt: "Test prompt 2")
        ]
        
        // Save test prompts
        manager.savePrompts(testPrompts)
        
        // Load them back
        let loadedPrompts = manager.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 2)
        XCTAssertEqual(loadedPrompts[0].name, "test1")
        XCTAssertEqual(loadedPrompts[0].prompt, "Test prompt 1")
        XCTAssertEqual(loadedPrompts[1].name, "test2")
        XCTAssertEqual(loadedPrompts[1].prompt, "Test prompt 2")
    }
    
    func testPromptItemEquality() {
        let prompt1 = PromptItem(name: "test", prompt: "Test prompt")
        let prompt2 = PromptItem(name: "test", prompt: "Test prompt")
        let prompt3 = prompt1
        
        // Different instances with same content should not be equal (different UUIDs)
        XCTAssertNotEqual(prompt1, prompt2)
        
        // Same instance should be equal
        XCTAssertEqual(prompt1, prompt3)
    }
    
    func testPromptItemCodable() throws {
        let originalPrompt = PromptItem(name: "test", prompt: "Test prompt content")
        
        // Encode to JSON
        let encoder = JSONEncoder()
        let jsonData = try encoder.encode(originalPrompt)
        
        // Decode from JSON
        let decoder = JSONDecoder()
        let decodedPrompt = try decoder.decode(PromptItem.self, from: jsonData)
        
        XCTAssertEqual(originalPrompt.id, decodedPrompt.id)
        XCTAssertEqual(originalPrompt.name, decodedPrompt.name)
        XCTAssertEqual(originalPrompt.prompt, decodedPrompt.prompt)
    }
    
    func testCorruptedFileRecovery_DISABLED() throws {
        let manager = PromptManager.shared
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        try FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)
        
        let promptsFile = configDir.appendingPathComponent("prompts.json")
        
        // Write corrupted JSON
        let corruptedData = "{ invalid json".data(using: .utf8)!
        try corruptedData.write(to: promptsFile)
        
        // Should recover with defaults
        let prompts = manager.loadPrompts()
        XCTAssertGreaterThan(prompts.count, 0)
        XCTAssertTrue(prompts.contains { $0.name == "summarize" })
    }
}
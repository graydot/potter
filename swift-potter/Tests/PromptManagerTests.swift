import XCTest
import Foundation
@testable import Potter

class PromptServiceTests: TestBase {
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
        
        // Set up PromptService to use test file instead of real Application Support
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        PromptService.shared.setTestFileURL(testPromptsFile)
    }
    
    override func tearDown() {
        // Restore PromptService to use real file path
        PromptService.shared.setTestFileURL(nil)
        
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        super.tearDown()
    }
    
    func testLoadPromptsCreatesDefaultFile() {
        let manager = PromptService.shared
        let prompts = manager.getPrompts()
        
        // Should create default prompts with proper structure
        XCTAssertGreaterThan(prompts.count, 0, "Should have default prompts")
        
        // Test prompt structure and content quality
        for prompt in prompts {
            XCTAssertFalse(prompt.name.isEmpty, "Prompt names should not be empty")
            XCTAssertFalse(prompt.prompt.isEmpty, "Prompt content should not be empty")
            XCTAssertNotNil(prompt.id, "Prompt should have valid ID")
            XCTAssertGreaterThan(prompt.prompt.count, 10, "Prompts should have meaningful content")
        }
        
        // Check file was created
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        XCTAssertTrue(FileManager.default.fileExists(atPath: testPromptsFile.path))
    }
    
    func testSaveAndLoadPrompts() {
        let manager = PromptService.shared
        let testPrompts = [
            PromptItem(name: "test1", prompt: "Test prompt 1"),
            PromptItem(name: "test2", prompt: "Test prompt 2")
        ]
        
        // Save test prompts
        manager.savePrompts(testPrompts)
        
        // Load them back
        let loadedPrompts = manager.getPrompts()
        
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
    
    func testCorruptedFileRecovery() throws {
        let manager = PromptService.shared
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        
        // Write corrupted JSON directly to the test file
        let corruptedData = "{ invalid json".data(using: .utf8)!
        try corruptedData.write(to: testPromptsFile)
        
        // Clear cache and force reload to trigger recovery
        manager.clearCache()
        manager.loadPrompts()
        
        // Should recover with defaults
        let prompts = manager.getPrompts()
        XCTAssertGreaterThan(prompts.count, 0)
        XCTAssertTrue(prompts.contains { $0.name == "Summarize" })
    }
}
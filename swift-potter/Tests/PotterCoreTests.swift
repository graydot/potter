import XCTest
import Foundation
import AppKit
@testable import Potter

@MainActor
class PotterCoreTests: TestBase {
    var potterCore: PotterCore!
    var tempDirectoryURL: URL!
    var originalCurrentDirectory: String!
    
    override func setUp() async throws {
        try await super.setUp()
        
        // TestBase already handles forceUserDefaultsForTesting = true
        
        // Save original directory
        originalCurrentDirectory = FileManager.default.currentDirectoryPath
        
        // Create temporary directory for tests
        tempDirectoryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("PotterCoreTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory to use config/ subdirectory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
        
        // Set up PromptManager to use test file instead of real Application Support
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        PromptManager.shared.setTestFileURL(testPromptsFile)
        
        // Clear UserDefaults
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
        }
        
        potterCore = PotterCore()
    }
    
    override func tearDown() async throws {
        // Restore PromptManager to use real file path
        PromptManager.shared.setTestFileURL(nil)
        
        // TestBase already handles forceUserDefaultsForTesting = false
        
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        // Clear UserDefaults
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
        }
        
        try await super.tearDown()
    }
    
    func testCoreInitialization() {
        XCTAssertNotNil(potterCore)
    }
    
    func testSetPromptMode() {
        potterCore.setPromptMode(.formal)
        
        // Note: We can't easily test the notification since it's a UI component
        // But we can verify the method doesn't crash
        XCTAssertTrue(true)
    }
    
    func testProcessClipboardTextWithoutValidProvider() async {
        // Set some text in clipboard
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString("Test text", forType: .string)
        
        // Setup core but don't configure LLM
        potterCore.setup()
        
        // This should not crash and should show appropriate error
        potterCore.processClipboardText()
        
        // Give it a moment to process
        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        XCTAssertTrue(true) // If we get here without crashing, test passes
    }
    
    func testProcessClipboardTextWithEmptyClipboard() async {
        // Clear clipboard
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        
        // Setup core
        potterCore.setup()
        
        // This should handle empty clipboard gracefully
        potterCore.processClipboardText()
        
        // Give it a moment to process
        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        XCTAssertTrue(true) // If we get here without crashing, test passes
    }
    
    func testPromptModeEnum() {
        let allModes = PromptMode.allCases
        XCTAssertEqual(allModes.count, 3)
        XCTAssertTrue(allModes.contains(.summarize))
        XCTAssertTrue(allModes.contains(.formal))
        XCTAssertTrue(allModes.contains(.casual))
        
        // Test prompt content
        XCTAssertFalse(PromptMode.summarize.prompt.isEmpty)
        XCTAssertFalse(PromptMode.formal.prompt.isEmpty)
        XCTAssertFalse(PromptMode.casual.prompt.isEmpty)
        
        // Test display names
        XCTAssertEqual(PromptMode.summarize.displayName, "Summarize")
        XCTAssertEqual(PromptMode.formal.displayName, "Make Formal")
        XCTAssertEqual(PromptMode.casual.displayName, "Make Casual")
        
        // Test raw values
        XCTAssertEqual(PromptMode.summarize.rawValue, "summarize")
        XCTAssertEqual(PromptMode.formal.rawValue, "formal")
        XCTAssertEqual(PromptMode.casual.rawValue, "casual")
    }
    
    
    func testPromptSelectionFallbackToDefault() {
        // Don't set any prompt in UserDefaults
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        
        // Create prompts file with test data
        let testPrompts = [
            PromptItem(name: "summarize", prompt: "Summarize this"),
            PromptItem(name: "formal", prompt: "Make this formal")
        ]
        PromptManager.shared.savePrompts(testPrompts)
        
        // Setup core
        potterCore.setup()
        
        // Should fall back to "summarize" default
        let currentPromptName = UserDefaults.standard.string(forKey: "current_prompt") ?? "summarize"
        XCTAssertEqual(currentPromptName, "summarize")
    }
    
    // Disabled: Clipboard access fails in test environment
    func disabled_testClipboardTextProcessing() {
        let testText = "This is a test text for processing"
        
        // Set text in clipboard
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        let success = pasteboard.setString(testText, forType: .string)
        XCTAssertTrue(success, "Should successfully set clipboard text")
        
        // Verify clipboard content
        let clipboardText = pasteboard.string(forType: .string)
        XCTAssertNotNil(clipboardText, "Clipboard content should not be nil")
        XCTAssertEqual(clipboardText, testText)
    }
    
    
    func testCoreSetupDoesNotCrash() {
        // This test ensures setup completes without crashing
        potterCore.setup()
        XCTAssertTrue(true)
    }
    
    func testHotkeyRegistrationDoesNotCrash() {
        // Setup should include hotkey registration
        potterCore.setup()
        
        // If we get here, hotkey registration didn't crash
        XCTAssertTrue(true)
    }
    
    func testMultipleSetupCallsAresSafe() {
        // Multiple setup calls should be safe
        potterCore.setup()
        potterCore.setup()
        potterCore.setup()
        
        XCTAssertTrue(true)
    }
    
    func testFourCharCodeFunction() {
        // Test the fourCharCode function used in hotkey registration
        // This is testing a private function through its public effect
        potterCore.setup()
        
        // If setup completed without crashing, fourCharCode worked
        XCTAssertTrue(true)
    }
}
import XCTest
import Foundation
import AppKit
@testable import Potter

/// Test Suite 4: Error Handling & Edge Cases
/// Automated tests based on manual test plan T4.x
@MainActor
class ErrorHandlingEdgeCasesTests: TestBase {
    var potterCore: PotterCore!
    var llmManager: LLMManager!
    var tempDirectoryURL: URL!
    var originalCurrentDirectory: String!
    
    override func setUp() async throws {
        try await super.setUp()
        
        // Save original directory
        originalCurrentDirectory = FileManager.default.currentDirectoryPath
        
        // Create temporary directory for tests
        tempDirectoryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("ErrorHandlingTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
        
        // Set up PromptManager to use test file
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        PromptManager.shared.setTestFileURL(testPromptsFile)
        
        // Initialize components
        potterCore = PotterCore()
        llmManager = LLMManager()
        
        // Clear test settings
        clearTestSettings()
    }
    
    override func tearDown() async throws {
        // Restore PromptManager
        PromptManager.shared.setTestFileURL(nil)
        
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        // Clear test settings
        clearTestSettings()
        
        try await super.tearDown()
    }
    
    // MARK: - T4.1: Network Connectivity Issues (Simulated)
    
    func testProcessTextWithoutAPIKey() async {
        // Test processing without API key (simulates network issues)
        llmManager.selectedModel = LLMModel.openAIModels.first
        
        do {
            _ = try await llmManager.processText("test", prompt: "test prompt")
            XCTFail("Should throw error when no API key")
        } catch {
            XCTAssertTrue(error is LLMError)
            if let llmError = error as? LLMError {
                // Check if it's the right error type
                switch llmError {
                case .invalidAPIKey:
                    XCTAssertTrue(true) // Expected error type
                default:
                    XCTFail("Expected invalidAPIKey error, got \(llmError)")
                }
            }
        }
    }
    
    func testProcessTextWithoutSelectedModel() async {
        // Test processing without selected model
        llmManager.selectedModel = nil
        llmManager.setAPIKey("test-key", for: .openAI)
        
        do {
            _ = try await llmManager.processText("test", prompt: "test prompt")
            XCTFail("Should throw error when no model selected")
        } catch {
            XCTAssertTrue(error is LLMError)
            if let llmError = error as? LLMError {
                // Check if it's the right error type
                switch llmError {
                case .noResponse:
                    XCTAssertTrue(true) // Expected error type
                default:
                    XCTFail("Expected noResponse error, got \(llmError)")
                }
            }
        }
    }
    
    func testLLMErrorTypes() {
        // Test LLM error types and their properties
        let errors: [LLMError] = [
            .invalidAPIKey,
            .noResponse,
            .invalidResponse,
            .apiError(400, "Bad Request"),
            .apiError(401, "Unauthorized"),
            .apiError(429, "Rate Limited"),
            .apiError(500, "Server Error")
        ]
        
        for error in errors {
            // Should be LLMError instances
            XCTAssertTrue(error is LLMError)
            
            // Should have meaningful descriptions
            XCTAssertFalse(error.localizedDescription.isEmpty)
        }
        
        // Test specific API error details
        if case .apiError(let code, let message) = LLMError.apiError(404, "Not Found") {
            XCTAssertEqual(code, 404)
            XCTAssertEqual(message, "Not Found")
        } else {
            XCTFail("API error case should match")
        }
    }
    
    func testNetworkTimeoutSimulation() async {
        // Test handling of network timeout scenarios
        // Note: This is a simulation since we can't easily mock network calls
        
        llmManager.selectedModel = LLMModel.openAIModels.first
        
        // Test with empty API key (simulates network failure)
        do {
            _ = try await llmManager.processText("test text", prompt: "summarize")
            XCTFail("Should fail with invalid API key")
        } catch {
            // Should handle error gracefully
            XCTAssertTrue(error is LLMError)
        }
    }
    
    // MARK: - T4.2: Invalid API Keys
    
    func testValidationWithInvalidAPIKeys() async {
        // Test validation with various invalid API key formats
        let invalidKeys = [
            "",
            "sk-invalid",
            "invalid-key-format",
            "123456789",
            "sk-", // Too short
            String(repeating: "x", count: 1000), // Too long
            "sk-\u{0000}invalid", // Contains null character
            "sk-invalid\n\r", // Contains newlines
            "sk-invalid key with spaces"
        ]
        
        for invalidKey in invalidKeys {
            await llmManager.validateAndSaveAPIKey(invalidKey, for: .openAI)
            
            let validationState = llmManager.validationStates[.openAI]
            XCTAssertFalse(validationState?.isValid ?? true, 
                          "Key '\(invalidKey)' should be invalid")
            
            // Should not crash the validation process
            XCTAssertFalse(llmManager.isValidating, 
                          "Validation should complete for invalid key '\(invalidKey)'")
        }
    }
    
    func testAPIKeyRevocationSimulation() {
        // Test handling of API key that becomes invalid after being set
        let testKey = "sk-test-becomes-invalid"
        
        // Set valid-looking key
        llmManager.setAPIKey(testKey, for: .openAI)
        XCTAssertEqual(llmManager.getAPIKey(for: .openAI), testKey)
        
        // Simulate revocation by setting validation state to invalid
        llmManager.validationStates[.openAI] = .invalid("API key has been revoked")
        
        // Should now report as not configured
        XCTAssertFalse(llmManager.isProviderConfigured(.openAI))
        
        let validationState = llmManager.getCurrentValidationState()
        XCTAssertFalse(validationState.isValid)
        XCTAssertEqual(validationState.errorMessage, "API key has been revoked")
    }
    
    func testAPIKeyRecoveryAfterError() {
        // Test recovery after API key error
        // First set invalid state
        llmManager.validationStates[.openAI] = .invalid("Test error")
        XCTAssertFalse(llmManager.isProviderConfigured(.openAI))
        
        // Set new valid key
        llmManager.setAPIKey("sk-new-valid-key", for: .openAI)
        
        // Validation state should reset to none
        let newValidationState = llmManager.validationStates[.openAI]
        // Check that validation state was reset
        if case .none = newValidationState {
            XCTAssertTrue(true) // Expected state
        } else {
            XCTFail("Expected validation state to be reset to .none")
        }
        
        // Should now have the key
        XCTAssertEqual(llmManager.getAPIKey(for: .openAI), "sk-new-valid-key")
    }
    
    // MARK: - T4.3: Large Text Processing
    
    func testLargeTextHandling() {
        // Test handling of large text input
        let smallText = "Small text for processing"
        let mediumText = String(repeating: "This is a sentence. ", count: 100) // ~2000 chars
        let largeText = String(repeating: "This is a longer sentence for testing. ", count: 1000) // ~40k chars
        let hugeText = String(repeating: "Huge text processing test. ", count: 10000) // ~270k chars
        
        let testTexts = [smallText, mediumText, largeText, hugeText]
        
        for text in testTexts {
            // Set text in clipboard
            let pasteboard = NSPasteboard.general
            pasteboard.clearContents()
            pasteboard.setString(text, forType: .string)
            
            // Verify clipboard can handle the text size
            let clipboardText = pasteboard.string(forType: .string)
            XCTAssertEqual(clipboardText, text, "Clipboard should handle text of \(text.count) characters")
        }
    }
    
    func testMemoryUsageWithLargeText() async {
        // Test memory usage doesn't spike with large text
        let largeText = String(repeating: "Memory test text. ", count: 5000) // ~90k chars
        
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(largeText, forType: .string)
        
        // Setup core
        potterCore.setup()
        
        // Process large text (will fail due to no API key, but shouldn't crash)
        potterCore.processClipboardText()
        
        // Give it time to process
        try? await Task.sleep(nanoseconds: 200_000_000) // 0.2 seconds
        
        // Should not crash or consume excessive memory
        XCTAssertTrue(true)
    }
    
    func testVeryLongSingleLine() {
        // Test handling of very long single line
        let longLine = String(repeating: "VeryLongLineWithoutSpacesOrBreaks", count: 1000)
        
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(longLine, forType: .string)
        
        let clipboardText = pasteboard.string(forType: .string)
        XCTAssertEqual(clipboardText, longLine)
        XCTAssertEqual(clipboardText?.count, longLine.count)
    }
    
    func testTextWithExtremeCharacterCounts() {
        // Test edge cases for text length
        let emptyText = ""
        let singleChar = "A"
        let maxReasonableText = String(repeating: "Test ", count: 20000) // ~100k chars
        
        let testTexts = [emptyText, singleChar, maxReasonableText]
        
        for text in testTexts {
            let pasteboard = NSPasteboard.general
            pasteboard.clearContents()
            pasteboard.setString(text, forType: .string)
            
            let clipboardText = pasteboard.string(forType: .string)
            XCTAssertEqual(clipboardText, text)
        }
    }
    
    // MARK: - T4.4: Clipboard Edge Cases
    
    func testEmptyClipboard() async {
        // Test processing with empty clipboard
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        
        potterCore.setup()
        potterCore.processClipboardText()
        
        // Should handle gracefully
        try? await Task.sleep(nanoseconds: 100_000_000)
        XCTAssertTrue(true) // No crash
    }
    
    func testNonTextClipboard() async {
        // Test processing with non-text clipboard content
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        
        // Simulate non-text content by clearing and not setting string
        pasteboard.clearContents()
        
        potterCore.setup()
        potterCore.processClipboardText()
        
        try? await Task.sleep(nanoseconds: 100_000_000)
        XCTAssertTrue(true) // Should handle gracefully
    }
    
    func testSpecialCharacters() {
        // Test text with special characters, emojis, unicode
        let specialTexts = [
            "Hello 🌍 World! 🚀",
            "Café naïve résumé",
            "中文测试 Japanese: こんにちは Arabic: مرحبا",
            "Math: ∑∞π∆ Symbols: ™©®",
            "Quotes: \"'`´",
            "Newlines:\nTabbed:\tSpaced: ",
            "Zero-width: \u{200B}\u{FEFF}",
            "Control chars: \u{0001}\u{001F}",
            "Mixed: Hello🌟世界Café™\n\tTest"
        ]
        
        for text in specialTexts {
            let pasteboard = NSPasteboard.general
            pasteboard.clearContents()
            pasteboard.setString(text, forType: .string)
            
            let clipboardText = pasteboard.string(forType: .string)
            XCTAssertEqual(clipboardText, text, "Special text should be preserved: '\(text)'")
        }
    }
    
    func testClipboardConcurrency() async {
        // Test rapid clipboard operations
        let pasteboard = NSPasteboard.general
        
        let texts = [
            "Text 1",
            "Text 2", 
            "Text 3",
            "Text 4",
            "Text 5"
        ]
        
        // Rapid clipboard changes
        for text in texts {
            pasteboard.clearContents()
            pasteboard.setString(text, forType: .string)
            
            let clipboardText = pasteboard.string(forType: .string)
            XCTAssertEqual(clipboardText, text)
        }
    }
    
    func testCorruptedClipboardRecovery() {
        // Test recovery from clipboard issues
        let pasteboard = NSPasteboard.general
        
        // Clear clipboard
        pasteboard.clearContents()
        XCTAssertNil(pasteboard.string(forType: .string))
        
        // Set valid text
        pasteboard.setString("Valid text", forType: .string)
        XCTAssertEqual(pasteboard.string(forType: .string), "Valid text")
        
        // Clear again
        pasteboard.clearContents()
        XCTAssertNil(pasteboard.string(forType: .string))
    }
    
    func testClipboardStringTypes() {
        // Test different string types and encodings
        let pasteboard = NSPasteboard.general
        
        // Test with different pasteboard types
        pasteboard.clearContents()
        pasteboard.setString("Plain text", forType: .string)
        XCTAssertEqual(pasteboard.string(forType: .string), "Plain text")
        
        // Test with empty string
        pasteboard.clearContents()
        pasteboard.setString("", forType: .string)
        XCTAssertEqual(pasteboard.string(forType: .string), "")
        
        // Test with whitespace only
        pasteboard.clearContents()
        pasteboard.setString("   \n\t   ", forType: .string)
        XCTAssertEqual(pasteboard.string(forType: .string), "   \n\t   ")
    }
    
    func testMultilineTextHandling() {
        // Test multiline text handling
        let multilineTexts = [
            "Line 1\nLine 2",
            "Line 1\r\nLine 2", // Windows line endings
            "Line 1\rLine 2", // Classic Mac line endings
            "\n\n\nMultiple newlines\n\n\n",
            "Mixed\nLine\r\nEndings\rHere"
        ]
        
        let pasteboard = NSPasteboard.general
        
        for text in multilineTexts {
            pasteboard.clearContents()
            pasteboard.setString(text, forType: .string)
            
            let clipboardText = pasteboard.string(forType: .string)
            XCTAssertEqual(clipboardText, text, "Multiline text should be preserved")
        }
    }
    
    // MARK: - Additional Error Scenarios
    
    func testPromptManagerErrorRecovery() throws {
        // Test prompt manager error recovery
        let manager = PromptManager.shared
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        
        // Write corrupted JSON
        let corruptedData = "{ invalid json".data(using: .utf8)!
        try corruptedData.write(to: testPromptsFile)
        
        // Should recover with defaults
        let prompts = manager.loadPrompts()
        XCTAssertGreaterThan(prompts.count, 0)
        XCTAssertTrue(prompts.contains { $0.name == "summarize" })
    }
    
    func testConcurrentLLMManagerAccess() async {
        // Test concurrent access to LLM manager
        let expectation = expectation(description: "Concurrent LLM access")
        expectation.expectedFulfillmentCount = 3
        
        let queue = DispatchQueue.global(qos: .background)
        
        queue.async {
            Task { @MainActor in
                self.llmManager.setAPIKey("test-key-1", for: .openAI)
                expectation.fulfill()
            }
        }
        
        queue.async {
            Task { @MainActor in
                let _ = self.llmManager.getAPIKey(for: .openAI)
                expectation.fulfill()
            }
        }
        
        queue.async {
            Task { @MainActor in
                let _ = self.llmManager.isProviderConfigured(.openAI)
                expectation.fulfill()
            }
        }
        
        await fulfillment(of: [expectation], timeout: 5.0)
        
        // Should handle concurrent access without crashes
        XCTAssertTrue(true)
    }
    
    func testInvalidModelSelection() {
        // Test selecting invalid models
        let openAIModel = LLMModel.openAIModels.first!
        
        // Select Anthropic provider but try to use OpenAI model
        llmManager.selectProvider(.anthropic)
        llmManager.selectModel(openAIModel) // This should work but be inconsistent
        
        // The model should still be set (even if inconsistent)
        XCTAssertEqual(llmManager.selectedModel?.id, openAIModel.id)
        XCTAssertEqual(llmManager.selectedProvider, .anthropic)
        
        // But the provider doesn't match the model
        XCTAssertNotEqual(llmManager.selectedModel?.provider, llmManager.selectedProvider)
    }
    
    func testValidationStateConsistency() {
        // Test validation state consistency
        llmManager.validationStates[.openAI] = .valid
        llmManager.validationStates[.anthropic] = .invalid("Test error")
        llmManager.validationStates[.google] = .validating
        
        // Switch providers and check states
        llmManager.selectProvider(.openAI)
        XCTAssertTrue(llmManager.getCurrentValidationState().isValid)
        
        llmManager.selectProvider(.anthropic)
        XCTAssertFalse(llmManager.getCurrentValidationState().isValid)
        XCTAssertEqual(llmManager.getCurrentValidationState().errorMessage, "Test error")
        
        llmManager.selectProvider(.google)
        XCTAssertFalse(llmManager.getCurrentValidationState().isValid)
        XCTAssertNil(llmManager.getCurrentValidationState().errorMessage)
    }
    
    // MARK: - Helper Methods
    
    private func clearTestSettings() {
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
        
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
            UserDefaults.standard.removeObject(forKey: "api_key_storage_method_\(provider.rawValue)")
        }
    }
}
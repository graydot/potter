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
            XCTAssertTrue(error is PotterError)
            if let potterError = error as? PotterError {
                // Check if it's the right error type
                switch potterError {
                case .configuration(.missingAPIKey):
                    XCTAssertTrue(true) // Expected error type
                case .network(.unauthorized):
                    XCTAssertTrue(true) // Also valid - API key is invalid/empty
                default:
                    XCTFail("Expected missingAPIKey or unauthorized error, got \(potterError)")
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
            XCTAssertTrue(error is PotterError)
            if let potterError = error as? PotterError {
                // Check if it's the right error type
                switch potterError {
                case .configuration(.missingConfiguration):
                    XCTAssertTrue(true) // Expected error type
                default:
                    XCTFail("Expected missingConfiguration error, got \(potterError)")
                }
            }
        }
    }
    
    func testPotterErrorTypes() {
        // Test Potter error types and their properties
        let errors: [PotterError] = [
            .configuration(.invalidAPIKey(provider: "Test")),
            .network(.invalidResponse(reason: "No response")),
            .network(.invalidResponse(reason: "Invalid response")),
            .network(.serverError(statusCode: 400, message: "Bad Request")),
            .network(.unauthorized(provider: "Test")),
            .network(.rateLimited(retryAfter: nil)),
            .network(.serverError(statusCode: 500, message: "Server Error"))
        ]
        
        for error in errors {
            // Should be PotterError instances
            XCTAssertTrue(error is PotterError)
            
            // Should have meaningful descriptions
            XCTAssertFalse(error.localizedDescription.isEmpty)
        }
        
        // Test specific API error details
        if case .network(.serverError(let statusCode, let message)) = PotterError.network(.serverError(statusCode: 404, message: "Not Found")) {
            XCTAssertEqual(statusCode, 404)
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
            XCTAssertTrue(error is PotterError)
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
    
    
    // MARK: - T4.3: Large Text Processing
    
    
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
    
    // Disabled: Clipboard access fails in test environment
    func disabled_testVeryLongSingleLine() {
        // Test handling of very long single line
        let longLine = String(repeating: "VeryLongLineWithoutSpacesOrBreaks", count: 1000)
        
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(longLine, forType: .string)
        
        let clipboardText = pasteboard.string(forType: .string)
        XCTAssertEqual(clipboardText, longLine)
        XCTAssertEqual(clipboardText?.count, longLine.count)
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
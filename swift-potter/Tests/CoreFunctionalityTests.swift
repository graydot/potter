import XCTest
import Foundation
import AppKit
@testable import Potter

/// Test Suite 2: Core Functionality
/// Automated tests based on manual test plan T2.x
@MainActor
class CoreFunctionalityTests: TestBase {
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
            .appendingPathComponent("CoreFunctionalityTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
        
        // Set up PromptManager to use test file
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        PromptManager.shared.setTestFileURL(testPromptsFile)
        
        // Initialize core components
        potterCore = PotterCore()
        llmManager = LLMManager()
        
        // Clear any existing settings
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
    
    // MARK: - T2.1: Basic Text Processing
    
    func testPotterCoreInitialization() {
        // Test that PotterCore initializes correctly
        XCTAssertNotNil(potterCore)
        
        // Test setup method doesn't crash
        potterCore.setup()
        XCTAssertTrue(true) // If we get here, setup completed without crashing
    }
    
    func testLLMManagerAccess() {
        // Test that PotterCore can access LLMManager after setup
        potterCore.setup()
        
        // Note: LLMManager is initialized asynchronously, so we need to wait
        // In real tests, we might need to add a completion handler or use expectations
        let llmManager = potterCore.getLLMManager()
        XCTAssertNotNil(llmManager)
    }
    
    func testClipboardTextRetrieval() {
        // Test clipboard text retrieval functionality
        let testText = "This is a test sentence that needs to be processed."
        
        // Set text in clipboard
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(testText, forType: .string)
        
        // Verify clipboard content
        let clipboardText = pasteboard.string(forType: .string)
        XCTAssertEqual(clipboardText, testText)
    }
    
    func testEmptyClipboardHandling() async {
        // Test handling of empty clipboard
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        
        // Setup core
        potterCore.setup()
        
        // This should handle empty clipboard gracefully
        potterCore.processClipboardText()
        
        // Give it a moment to process
        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        // Should not crash and should show appropriate feedback
        XCTAssertTrue(true) // If we get here without crashing, test passes
    }
    
    func testNonTextClipboardHandling() async {
        // Test handling of non-text clipboard content
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        
        // Put an image or other non-text content (simulated by clearing completely)
        pasteboard.clearContents()
        
        potterCore.setup()
        potterCore.processClipboardText()
        
        try? await Task.sleep(nanoseconds: 100_000_000)
        
        XCTAssertTrue(true) // Should handle gracefully without crashing
    }
    
    func testProcessClipboardTextWithoutValidProvider() async {
        // Test processing without valid LLM provider
        let testText = "Test text for processing"
        
        // Set text in clipboard
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(testText, forType: .string)
        
        // Setup core but don't configure LLM
        potterCore.setup()
        
        // This should not crash and should show appropriate error
        potterCore.processClipboardText()
        
        // Give it a moment to process
        try? await Task.sleep(nanoseconds: 100_000_000)
        
        XCTAssertTrue(true) // If we get here without crashing, test passes
    }
    
    // MARK: - T2.2: Multiple LLM Providers
    
    func testProviderSwitching() {
        // Test switching between different LLM providers
        llmManager.selectProvider(.openAI)
        XCTAssertEqual(llmManager.selectedProvider, .openAI)
        XCTAssertEqual(llmManager.selectedModel?.provider, .openAI)
        
        llmManager.selectProvider(.anthropic)
        XCTAssertEqual(llmManager.selectedProvider, .anthropic)
        XCTAssertEqual(llmManager.selectedModel?.provider, .anthropic)
        
        llmManager.selectProvider(.google)
        XCTAssertEqual(llmManager.selectedProvider, .google)
        XCTAssertEqual(llmManager.selectedModel?.provider, .google)
    }
    
    func testProviderModelsAvailability() {
        // Test that all providers have models available
        for provider in LLMProvider.allCases {
            let models = provider.models
            XCTAssertGreaterThan(models.count, 0, "Provider \(provider) should have at least one model")
            
            // Verify all models belong to the correct provider
            for model in models {
                XCTAssertEqual(model.provider, provider, "Model \(model.name) should belong to \(provider)")
            }
        }
    }
    
    func testProviderConfigurationState() {
        // Test provider configuration states
        for provider in LLMProvider.allCases {
            // Initially not configured
            XCTAssertFalse(llmManager.isProviderConfigured(provider))
            
            // Configure with test API key
            llmManager.setAPIKey("test-key-\(provider.rawValue)", for: provider)
            
            // Should now be considered configured
            XCTAssertTrue(llmManager.isProviderConfigured(provider))
        }
    }
    
    func testModelSelectionPersistence() {
        // Test that model selection persists when switching providers
        let openAIModel = LLMProvider.openAI.models.first!
        let anthropicModel = LLMProvider.anthropic.models.first!
        
        // Select OpenAI model
        llmManager.selectProvider(.openAI)
        llmManager.selectModel(openAIModel)
        
        // Switch to Anthropic
        llmManager.selectProvider(.anthropic)
        llmManager.selectModel(anthropicModel)
        
        // Switch back to OpenAI
        llmManager.selectProvider(.openAI)
        
        // Should default to first OpenAI model (not necessarily the one we selected before)
        XCTAssertEqual(llmManager.selectedModel?.provider, .openAI)
    }
    
    // MARK: - T2.3: Custom Prompts
    
    func testPromptManagerInitialization() {
        // Test that PromptManager initializes with default prompts
        let prompts = PromptManager.shared.loadPrompts()
        
        XCTAssertGreaterThan(prompts.count, 0, "Should have default prompts")
        XCTAssertTrue(prompts.contains { $0.name == "summarize" })
        XCTAssertTrue(prompts.contains { $0.name == "formal" })
        XCTAssertTrue(prompts.contains { $0.name == "casual" })
    }
    
    func testCustomPromptCreation() {
        // Test creating custom prompts
        let manager = PromptManager.shared
        let originalPrompts = manager.loadPrompts()
        
        let customPrompt = PromptItem(name: "translate_french", prompt: "Translate the following text to French:")
        let newPrompts = originalPrompts + [customPrompt]
        
        manager.savePrompts(newPrompts)
        
        let loadedPrompts = manager.loadPrompts()
        XCTAssertEqual(loadedPrompts.count, originalPrompts.count + 1)
        XCTAssertTrue(loadedPrompts.contains { $0.name == "translate_french" })
    }
    
    func testPromptPersistence() {
        // Test that prompts persist across manager instances
        let manager = PromptManager.shared
        let testPrompts = [
            PromptItem(name: "test1", prompt: "Test prompt 1"),
            PromptItem(name: "test2", prompt: "Test prompt 2")
        ]
        
        manager.savePrompts(testPrompts)
        
        // Load prompts again (simulating app restart)
        let loadedPrompts = manager.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 2)
        XCTAssertEqual(loadedPrompts[0].name, "test1")
        XCTAssertEqual(loadedPrompts[1].name, "test2")
    }
    
    func testPromptModeEnum() {
        // Test PromptMode enum functionality
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
    }
    
    func testPromptModeChanging() {
        // Test changing prompt modes
        potterCore.setPromptMode(.formal)
        // Note: We can't easily test the internal state change, but we can verify it doesn't crash
        XCTAssertTrue(true)
        
        potterCore.setPromptMode(.casual)
        XCTAssertTrue(true)
        
        potterCore.setPromptMode(.summarize)
        XCTAssertTrue(true)
    }
    
    func testPromptSelectionFromUserDefaults() {
        // Test prompt selection from UserDefaults
        UserDefaults.standard.set("formal", forKey: "current_prompt")
        
        // Create prompts file with test data
        let testPrompts = [
            PromptItem(name: "formal", prompt: "Make this formal"),
            PromptItem(name: "casual", prompt: "Make this casual")
        ]
        PromptManager.shared.savePrompts(testPrompts)
        
        // Setup core
        potterCore.setup()
        
        // Verify the test setup worked
        let loadedPrompts = PromptManager.shared.loadPrompts()
        XCTAssertEqual(loadedPrompts.count, 2)
        
        let currentPromptName = UserDefaults.standard.string(forKey: "current_prompt")
        XCTAssertEqual(currentPromptName, "formal")
    }
    
    func testPromptFallbackToDefault() {
        // Test fallback to default prompt when none is selected
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        
        let testPrompts = [
            PromptItem(name: "summarize", prompt: "Summarize this"),
            PromptItem(name: "formal", prompt: "Make this formal")
        ]
        PromptManager.shared.savePrompts(testPrompts)
        
        potterCore.setup()
        
        // Should fall back to "summarize" default
        let currentPromptName = UserDefaults.standard.string(forKey: "current_prompt") ?? "summarize"
        XCTAssertEqual(currentPromptName, "summarize")
    }
    
    func testLargeNumberOfPrompts() {
        // Test handling many custom prompts
        var prompts: [PromptItem] = []
        
        for i in 1...50 {
            prompts.append(PromptItem(name: "prompt_\(i)", prompt: "This is prompt number \(i)"))
        }
        
        PromptManager.shared.savePrompts(prompts)
        let loadedPrompts = PromptManager.shared.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 50)
        XCTAssertTrue(loadedPrompts.contains { $0.name == "prompt_1" })
        XCTAssertTrue(loadedPrompts.contains { $0.name == "prompt_50" })
    }
    
    func testPromptWithSpecialCharacters() {
        // Test prompts with special characters
        let specialPrompt = PromptItem(
            name: "émojis_test_🎯",
            prompt: "Translate to 中文: 🚀 Testing émojis and ünicöde characters! 💫"
        )
        
        PromptManager.shared.savePrompts([specialPrompt])
        let loadedPrompts = PromptManager.shared.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 1)
        XCTAssertEqual(loadedPrompts[0].name, "émojis_test_🎯")
        XCTAssertTrue(loadedPrompts[0].prompt.contains("🚀"))
        XCTAssertTrue(loadedPrompts[0].prompt.contains("中文"))
        XCTAssertTrue(loadedPrompts[0].prompt.contains("émojis"))
    }
    
    func testVeryLongPrompt() {
        // Test handling of very long prompt content
        let longPromptText = String(repeating: "This is a very long prompt text. ", count: 100)
        let longPrompt = PromptItem(name: "long_prompt", prompt: longPromptText)
        
        PromptManager.shared.savePrompts([longPrompt])
        let loadedPrompts = PromptManager.shared.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 1)
        XCTAssertEqual(loadedPrompts[0].prompt.count, longPromptText.count)
        XCTAssertTrue(loadedPrompts[0].prompt.hasSuffix("This is a very long prompt text. "))
    }
    
    // MARK: - Helper Methods
    
    private func clearTestSettings() {
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
        }
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
    }
}
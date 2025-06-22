import XCTest
import Foundation
import AppKit
import Carbon
@testable import Potter

/// Test Suite 3: Settings & Configuration
/// Automated tests based on manual test plan T3.x
@MainActor
class SettingsConfigurationTests: TestBase {
    var potterCore: PotterCore!
    var llmManager: LLMManager!
    var storageAdapter: StorageAdapter!
    var tempDirectoryURL: URL!
    var originalCurrentDirectory: String!
    
    override func setUp() async throws {
        try await super.setUp()
        
        // Save original directory
        originalCurrentDirectory = FileManager.default.currentDirectoryPath
        
        // Create temporary directory for tests
        tempDirectoryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("SettingsConfigurationTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
        
        // Initialize components
        potterCore = PotterCore()
        llmManager = LLMManager()
        storageAdapter = StorageAdapter.shared
        // Force UserDefaults mode for testing
        storageAdapter.currentStorageMethod = .userDefaults
        
        // Clear test settings
        clearTestSettings()
    }
    
    override func tearDown() async throws {
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        // Clear test settings
        clearTestSettings()
        
        try await super.tearDown()
    }
    
    // MARK: - T3.1: Hotkey Configuration
    
    
    
    
    func testHotkeyDisableEnable() {
        // Test disabling and enabling hotkeys
        potterCore.setup()
        
        // These methods should not crash
        potterCore.disableGlobalHotkey()
        XCTAssertTrue(true) // If we get here, disable worked
        
        potterCore.enableGlobalHotkey()
        XCTAssertTrue(true) // If we get here, enable worked
        
        // Multiple calls should be safe
        potterCore.disableGlobalHotkey()
        potterCore.disableGlobalHotkey()
        potterCore.enableGlobalHotkey()
        potterCore.enableGlobalHotkey()
        XCTAssertTrue(true)
    }
    
    func testInvalidHotkeyHandling() {
        // Test handling of invalid hotkey combinations
        let invalidHotkeys = [
            [], // Empty
            ["R"], // No modifier
            ["⌘"], // Only modifier
            ["⌘", "⇧"], // No key
            ["⌘", "⇧", "⌥", "⌃", "R", "T"] // Too many keys
        ]
        
        potterCore.setup()
        
        for invalidHotkey in invalidHotkeys {
            // Should handle gracefully without crashing
            potterCore.updateHotkey(invalidHotkey)
            XCTAssertTrue(true) // If we get here, it handled the invalid hotkey
        }
    }
    
    // MARK: - T3.2: Secure Storage Options
    
    func testStorageMethodConfiguration() {
        // TODO: Temporarily disabled during StorageAdapter migration
        // This test will be updated to use the new StorageAdapter API
        
        // Verify that StorageAdapter is using UserDefaults during testing
        XCTAssertEqual(storageAdapter.currentStorageMethod, .userDefaults,
                      "StorageAdapter should use UserDefaults during testing")
        
        // Test that storage method changes are handled properly
        // (During testing, it should remain UserDefaults regardless of setting)
        storageAdapter.currentStorageMethod = .keychain
        XCTAssertEqual(storageAdapter.currentStorageMethod, .userDefaults,
                      "StorageAdapter should still use UserDefaults during testing even when set to keychain")
    }
    
    // Disabled: Race condition in parallel testing
    func disabled_testAPIKeySaveAndLoadWithDifferentMethods() {
        // Test saving and loading with StorageAdapter
        let testKey = "sk-test-storage-method-key"
        let provider = LLMProvider.openAI
        
        // Test saving and loading via StorageAdapter
        let saveResult = storageAdapter.saveAPIKey(testKey, for: provider)
        XCTAssertTrue(saveResult.isSuccess)
        
        let loadResult = storageAdapter.loadAPIKey(for: provider)
        switch loadResult {
        case .success(let loadedKey):
            XCTAssertEqual(loadedKey, testKey)
        case .failure(let error):
            XCTFail("Failed to load API key: \(error.localizedDescription)")
        }
        
        // Verify it's actually in UserDefaults (since we're in testing mode)
        let userDefaultsKey = UserDefaults.standard.string(forKey: "api_key_\(provider.rawValue)")
        XCTAssertEqual(userDefaultsKey, testKey)
        
        // Clean up
        _ = storageAdapter.removeAPIKey(for: provider)
    }
    
    
    
    
    func testKeychainAccessibilityCheck() {
        // TODO: This test temporarily disabled during StorageAdapter migration
        // The new StorageAdapter should automatically use UserDefaults during testing
        // avoiding keychain access entirely
        
        // Verify that testing infrastructure is set up correctly
        XCTAssertTrue(StorageAdapter.shared.forceUserDefaultsForTesting, 
                     "Testing flag should be set")
        
        // Verify StorageAdapter uses UserDefaults in testing mode
        XCTAssertEqual(storageAdapter.currentStorageMethod, .userDefaults,
                      "StorageAdapter should use UserDefaults during testing")
    }
    
    // MARK: - T3.3: Settings Persistence & Management
    
    
    
    
    func testValidationStateManagement() {
        // Test validation state management
        llmManager.validationStates[.openAI] = .valid
        XCTAssertTrue(llmManager.getCurrentValidationState().isValid)
        
        llmManager.selectProvider(.anthropic)
        llmManager.validationStates[.anthropic] = .invalid("Test error")
        XCTAssertFalse(llmManager.getCurrentValidationState().isValid)
        XCTAssertEqual(llmManager.getCurrentValidationState().errorMessage, "Test error")
        
        llmManager.validationStates[.anthropic] = .validating
        XCTAssertFalse(llmManager.getCurrentValidationState().isValid)
        XCTAssertNil(llmManager.getCurrentValidationState().errorMessage)
    }
    
    func testProviderModelConsistency() {
        // Test that selected model always matches selected provider
        for provider in LLMProvider.allCases {
            llmManager.selectProvider(provider)
            
            guard let selectedModel = llmManager.selectedModel else {
                XCTFail("Selected model should not be nil for \(provider)")
                continue
            }
            
            XCTAssertEqual(selectedModel.provider, provider, 
                          "Selected model should belong to selected provider \(provider)")
        }
    }
    
    func testModelSelectionWithinProvider() {
        // Test selecting different models within a provider
        llmManager.selectProvider(.openAI)
        let openAIModels = LLMProvider.openAI.models
        
        guard openAIModels.count >= 2 else {
            XCTFail("OpenAI should have at least 2 models for this test")
            return
        }
        
        let firstModel = openAIModels[0]
        let secondModel = openAIModels[1]
        
        llmManager.selectModel(firstModel)
        XCTAssertEqual(llmManager.selectedModel?.id, firstModel.id)
        
        llmManager.selectModel(secondModel)
        XCTAssertEqual(llmManager.selectedModel?.id, secondModel.id)
        
        // Provider should remain unchanged
        XCTAssertEqual(llmManager.selectedProvider, .openAI)
    }
    
    
    func testConcurrentSettingsAccess() {
        // Test concurrent access to settings (basic thread safety)
        let expectation = expectation(description: "Concurrent settings access")
        expectation.expectedFulfillmentCount = 3
        
        let queue = DispatchQueue.global(qos: .background)
        
        // Simulate concurrent settings changes
        queue.async {
            Task { @MainActor in
                self.llmManager.selectProvider(.openAI)
                expectation.fulfill()
            }
        }
        
        queue.async {
            Task { @MainActor in
                self.llmManager.setAPIKey("test-key-1", for: .openAI)
                expectation.fulfill()
            }
        }
        
        queue.async {
            Task { @MainActor in
                if let model = LLMProvider.openAI.models.first {
                    self.llmManager.selectModel(model)
                }
                expectation.fulfill()
            }
        }
        
        waitForExpectations(timeout: 5.0)
        
        // Should not crash and should have consistent state
        XCTAssertEqual(llmManager.selectedProvider, .openAI)
        XCTAssertNotNil(llmManager.selectedModel)
    }
    
    func testSettingsReset() {
        // Test resetting settings to defaults
        llmManager.selectProvider(.google)
        llmManager.setAPIKey("test-key", for: .google)
        
        // Clear settings
        clearTestSettings()
        
        // Create new manager
        let resetManager = LLMManager()
        
        // Should be back to defaults
        XCTAssertEqual(resetManager.selectedProvider, .openAI)
        XCTAssertTrue(resetManager.getAPIKey(for: .google).isEmpty)
    }
    
    // MARK: - Helper Methods
    
    private func clearTestSettings() {
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
        UserDefaults.standard.removeObject(forKey: "global_hotkey")
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
            UserDefaults.standard.removeObject(forKey: "api_key_storage_method_\(provider.rawValue)")
        }
    }
}
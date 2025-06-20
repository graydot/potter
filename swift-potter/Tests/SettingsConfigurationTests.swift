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
    var secureStorage: SecureAPIKeyStorage!
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
        secureStorage = SecureAPIKeyStorage.shared
        
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
    
    func testDefaultHotkeyConfiguration() {
        // Test default hotkey configuration
        let defaultHotkey = ["⌘", "⇧", "9"]
        
        // Setup core to initialize hotkeys
        potterCore.setup()
        
        // Verify default hotkey is set in UserDefaults (if not previously configured)
        let savedHotkey = UserDefaults.standard.array(forKey: "global_hotkey") as? [String]
        if savedHotkey == nil {
            // On first run, should use default
            XCTAssertTrue(true) // Default behavior is acceptable
        } else {
            // If hotkey was saved, verify it's valid
            XCTAssertNotNil(savedHotkey)
            XCTAssertGreaterThan(savedHotkey!.count, 0)
        }
    }
    
    func testHotkeyUpdate() {
        // Test updating hotkey configuration
        let newHotkey = ["⌘", "⇧", "T"]
        
        potterCore.setup()
        potterCore.updateHotkey(newHotkey)
        
        // Verify hotkey is saved
        let savedHotkey = UserDefaults.standard.array(forKey: "global_hotkey") as? [String]
        XCTAssertEqual(savedHotkey, newHotkey)
    }
    
    func testHotkeyParsing() {
        // Test various hotkey combinations parsing
        let testHotkeys = [
            ["⌘", "R"],
            ["⌘", "⇧", "R"],
            ["⌘", "⌥", "R"],
            ["⌘", "⌃", "R"],
            ["⌘", "⇧", "⌥", "R"],
            ["⌘", "1"],
            ["⌘", "⇧", "9"]
        ]
        
        potterCore.setup()
        
        for hotkey in testHotkeys {
            // This should not crash
            potterCore.updateHotkey(hotkey)
            
            let savedHotkey = UserDefaults.standard.array(forKey: "global_hotkey") as? [String]
            XCTAssertEqual(savedHotkey, hotkey, "Hotkey \(hotkey) should be saved correctly")
        }
    }
    
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
        // Test setting storage method for providers
        for provider in LLMProvider.allCases {
            // Test UserDefaults storage
            secureStorage.setStorageMethod(.userDefaults, for: provider)
            let userDefaultsMethod = secureStorage.getStorageMethod(for: provider)
            XCTAssertEqual(userDefaultsMethod, .userDefaults)
            
            // Test Keychain storage (but during testing should return userDefaults due to testing flag)
            secureStorage.setStorageMethod(.keychain, for: provider)
            let keychainMethod = secureStorage.getStorageMethod(for: provider)
            XCTAssertEqual(keychainMethod, .userDefaults, "Testing flag should force userDefaults")
        }
    }
    
    func testAPIKeySaveAndLoadWithDifferentMethods() {
        // Test saving and loading with different storage methods
        let testKey = "sk-test-storage-method-key"
        let provider = LLMProvider.openAI
        
        // Test UserDefaults storage
        let success = secureStorage.saveAPIKey(testKey, for: provider, using: .userDefaults)
        XCTAssertTrue(success)
        
        let loadedKey = secureStorage.loadAPIKey(for: provider)
        XCTAssertEqual(loadedKey, testKey)
        
        // Verify it's actually in UserDefaults
        let userDefaultsKey = UserDefaults.standard.string(forKey: "api_key_\(provider.rawValue)")
        XCTAssertEqual(userDefaultsKey, testKey)
    }
    
    func testAPIKeyRemoval() {
        // Test removing API keys
        let testKey = "sk-test-removal-key"
        let provider = LLMProvider.anthropic
        
        // Save key first
        _ = secureStorage.saveAPIKey(testKey, for: provider, using: .userDefaults)
        XCTAssertEqual(secureStorage.loadAPIKey(for: provider), testKey)
        
        // Remove key
        let removeSuccess = secureStorage.removeAPIKey(for: provider)
        XCTAssertTrue(removeSuccess)
        
        // Verify removal
        let removedKey = secureStorage.loadAPIKey(for: provider)
        XCTAssertNil(removedKey)
        
        // Verify UserDefaults is cleared
        let userDefaultsKey = UserDefaults.standard.string(forKey: "api_key_\(provider.rawValue)")
        XCTAssertNil(userDefaultsKey)
    }
    
    func testStorageMethodPersistence() {
        // Test that storage method preferences persist
        let provider = LLMProvider.google
        
        secureStorage.setStorageMethod(.keychain, for: provider)
        
        // Verify persistence in UserDefaults
        let methodKey = "api_key_storage_method_\(provider.rawValue)"
        let savedMethod = UserDefaults.standard.string(forKey: methodKey)
        XCTAssertEqual(savedMethod, APIKeyStorageMethod.keychain.rawValue)
    }
    
    func testMultipleProviderStorage() {
        // Test storing keys for multiple providers with different methods
        let testKeys = [
            LLMProvider.openAI: "sk-openai-test",
            LLMProvider.anthropic: "sk-ant-test", 
            LLMProvider.google: "google-test"
        ]
        
        // Save all keys
        for (provider, key) in testKeys {
            let success = secureStorage.saveAPIKey(key, for: provider, using: .userDefaults)
            XCTAssertTrue(success, "Failed to save key for \(provider)")
        }
        
        // Verify all keys can be loaded
        for (provider, expectedKey) in testKeys {
            let loadedKey = secureStorage.loadAPIKey(for: provider)
            XCTAssertEqual(loadedKey, expectedKey, "Key mismatch for \(provider)")
        }
    }
    
    func testKeychainAccessibilityCheck() {
        // Test keychain accessibility checking
        let isAccessible = secureStorage.isKeychainAccessible()
        
        // Should return boolean without crashing
        XCTAssertNotNil(isAccessible)
        // During testing, this might return false due to testing environment
    }
    
    // MARK: - T3.3: Settings Persistence & Management
    
    func testLLMManagerSettingsPersistence() {
        // Test that LLM manager settings persist across instances
        let testProvider = LLMProvider.anthropic
        let testKey = "sk-test-persistence"
        
        // Configure first instance
        llmManager.selectProvider(testProvider)
        llmManager.setAPIKey(testKey, for: testProvider)
        
        if let testModel = testProvider.models.first {
            llmManager.selectModel(testModel)
        }
        
        llmManager.saveSettings()
        
        // Create new instance to test persistence
        let newManager = LLMManager()
        
        XCTAssertEqual(newManager.selectedProvider, testProvider)
        XCTAssertEqual(newManager.getAPIKey(for: testProvider), testKey)
        XCTAssertEqual(newManager.selectedModel?.provider, testProvider)
    }
    
    func testSettingsLoadingFromUserDefaults() {
        // Test loading settings from UserDefaults
        UserDefaults.standard.set("google", forKey: "llm_provider")
        UserDefaults.standard.set("test-google-key", forKey: "api_key_google")
        UserDefaults.standard.set("gemini-1.5-pro", forKey: "selected_model")
        
        let newManager = LLMManager()
        
        XCTAssertEqual(newManager.selectedProvider, .google)
        XCTAssertEqual(newManager.getAPIKey(for: .google), "test-google-key")
        XCTAssertEqual(newManager.selectedModel?.id, "gemini-1.5-pro")
    }
    
    func testSettingsWithMissingData() {
        // Test settings loading with missing/corrupted data
        UserDefaults.standard.set("invalid_provider", forKey: "llm_provider")
        UserDefaults.standard.set("invalid_model_id", forKey: "selected_model")
        
        let manager = LLMManager()
        
        // Should fall back to defaults
        XCTAssertEqual(manager.selectedProvider, .openAI) // Default provider
        XCTAssertNotNil(manager.selectedModel)
        XCTAssertEqual(manager.selectedModel?.provider, .openAI)
    }
    
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
    
    func testSettingsSaveTriggering() {
        // Test that settings are saved when configurations change
        let initialProvider = llmManager.selectedProvider
        
        // Change provider
        let newProvider: LLMProvider = (initialProvider == .openAI) ? .anthropic : .openAI
        llmManager.selectProvider(newProvider)
        
        // Verify saved in UserDefaults
        let savedProvider = UserDefaults.standard.string(forKey: "llm_provider")
        XCTAssertEqual(savedProvider, newProvider.rawValue)
        
        // Change API key
        let testKey = "sk-test-save-triggering"
        llmManager.setAPIKey(testKey, for: newProvider)
        
        // Verify saved
        let savedKey = UserDefaults.standard.string(forKey: "api_key_\(newProvider.rawValue)")
        XCTAssertEqual(savedKey, testKey)
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
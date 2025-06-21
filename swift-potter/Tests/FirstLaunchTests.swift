import XCTest
import Foundation
import AppKit
@testable import Potter

/// Test Suite 1: First Launch & Initial Setup
/// Automated tests based on manual test plan T1.x
@MainActor
class FirstLaunchTests: TestBase {
    var permissionManager: PermissionManager!
    var llmManager: LLMManager!
    
    override func setUp() async throws {
        try await super.setUp()
        
        permissionManager = PermissionManager.shared
        llmManager = LLMManager()
        
        // Clear any existing configuration to simulate first launch
        clearAllConfiguration()
    }
    
    override func tearDown() async throws {
        // Clean up test configuration
        clearAllConfiguration()
        
        try await super.tearDown()
    }
    
    // MARK: - T1.1: Clean First Launch
    
    func testCleanFirstLaunchInitialization() {
        // Verify app can initialize without crashes on clean system
        XCTAssertNotNil(llmManager)
        XCTAssertNotNil(permissionManager)
        
        // Verify default state
        XCTAssertEqual(llmManager.selectedProvider, .openAI)
        XCTAssertNotNil(llmManager.selectedModel)
        XCTAssertFalse(llmManager.hasValidProvider())
    }
    
    func testFirstLaunchNoAPIKeysConfigured() {
        // Simulate clean first launch - no API keys should be configured
        // First ensure all keys are cleared
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
        }
        UserDefaults.standard.synchronize()
        
        // Create a fresh LLMManager to ensure clean state
        let freshLLMManager = LLMManager()
        
        for provider in LLMProvider.allCases {
            let apiKey = freshLLMManager.getAPIKey(for: provider)
            XCTAssertTrue(apiKey.isEmpty, "Provider \(provider) should not have API key on first launch")
            XCTAssertFalse(freshLLMManager.isProviderConfigured(provider), "Provider \(provider) should not be configured on first launch")
        }
    }
    
    func testDefaultSettingsOnFirstLaunch() {
        // Verify default settings are properly initialized
        XCTAssertEqual(llmManager.selectedProvider, .openAI)
        XCTAssertNotNil(llmManager.selectedModel)
        XCTAssertEqual(llmManager.selectedModel?.provider, .openAI)
        
        // Check default prompt is available
        let currentPrompt = UserDefaults.standard.string(forKey: "current_prompt") ?? "summarize"
        XCTAssertFalse(currentPrompt.isEmpty)
    }
    
    // MARK: - T1.2: Permission Handling
    
    func testInitialPermissionStates() {
        // Test initial permission states
        XCTAssertNotNil(permissionManager.accessibilityStatus)
        XCTAssertNotNil(permissionManager.notificationsStatus)
        XCTAssertFalse(permissionManager.isCheckingPermissions)
        
        // Verify permission types
        let accessibilityStatus = permissionManager.getPermissionStatus(for: .accessibility)
        let notificationsStatus = permissionManager.getPermissionStatus(for: .notifications)
        
        let validStatuses: [PermissionStatus] = [.granted, .denied, .notDetermined, .unknown]
        XCTAssertTrue(validStatuses.contains(accessibilityStatus))
        XCTAssertTrue(validStatuses.contains(notificationsStatus))
    }
    
    
    func testPermissionCheckingDoesNotCrash() {
        // Test that permission checking doesn't crash
        permissionManager.checkAllPermissions()
        XCTAssertTrue(true) // If we get here, no crash occurred
        
        // Test multiple rapid calls
        for _ in 0..<5 {
            permissionManager.checkAllPermissions()
        }
        XCTAssertTrue(true)
    }
    
    // Disabled: This test opens system settings which is disruptive during testing
    // func testOpenSystemSettingsDoesNotCrash() {
    //     // Test that opening system settings doesn't crash (even if it can't actually open)
    //     permissionManager.openSystemSettings(for: .accessibility)
    //     permissionManager.openSystemSettings(for: .notifications)
    //     XCTAssertTrue(true)
    // }
    
    // MARK: - T1.3: API Key Configuration
    
    func testAPIKeyValidationWithEmptyKey() async {
        // Test validation with empty API key
        await llmManager.validateAndSaveAPIKey("", for: .openAI)
        
        let validationState = llmManager.validationStates[.openAI]
        XCTAssertFalse(validationState?.isValid ?? true)
        XCTAssertEqual(validationState?.errorMessage, "API key cannot be empty")
        XCTAssertFalse(llmManager.isValidating)
    }
    
    func testAPIKeyValidationWithInvalidKey() async {
        // Test validation with invalid API key format
        let invalidKeys = [
            "sk-invalid",
            "invalid-key",
            "123456",
            "not-an-api-key"
        ]
        
        for invalidKey in invalidKeys {
            await llmManager.validateAndSaveAPIKey(invalidKey, for: .openAI)
            
            let validationState = llmManager.validationStates[.openAI]
            XCTAssertFalse(validationState?.isValid ?? true, "Key '\(invalidKey)' should be invalid")
        }
    }
    
    
    func testAPIKeyStorageMethodConfiguration() {
        // Test that storage method can be configured
        let storage = SecureAPIKeyStorage.shared
        
        // During testing, should always return userDefaults
        for provider in LLMProvider.allCases {
            let method = storage.getStorageMethod(for: provider)
            XCTAssertEqual(method, .userDefaults, "Testing should use UserDefaults storage")
        }
    }
    
    func testMultipleProviderConfiguration() {
        // Test configuring multiple providers
        let testKeys = [
            LLMProvider.openAI: "sk-openai-test-key",
            LLMProvider.anthropic: "sk-ant-test-key",
            LLMProvider.google: "google-test-key"
        ]
        
        // Set API keys for all providers
        for (provider, key) in testKeys {
            llmManager.setAPIKey(key, for: provider)
        }
        
        // Verify all keys are stored correctly
        for (provider, expectedKey) in testKeys {
            let retrievedKey = llmManager.getAPIKey(for: provider)
            XCTAssertEqual(retrievedKey, expectedKey, "Key for \(provider) should match")
        }
    }
    
    func testProviderSwitching() {
        // Test switching between providers
        llmManager.selectProvider(.anthropic)
        XCTAssertEqual(llmManager.selectedProvider, .anthropic)
        XCTAssertEqual(llmManager.selectedModel?.provider, .anthropic)
        
        llmManager.selectProvider(.google)
        XCTAssertEqual(llmManager.selectedProvider, .google)
        XCTAssertEqual(llmManager.selectedModel?.provider, .google)
        
        llmManager.selectProvider(.openAI)
        XCTAssertEqual(llmManager.selectedProvider, .openAI)
        XCTAssertEqual(llmManager.selectedModel?.provider, .openAI)
    }
    
    func testModelSelection() {
        // Test model selection within provider
        let openAIModels = LLMProvider.openAI.models
        guard let firstModel = openAIModels.first,
              let secondModel = openAIModels.dropFirst().first else {
            XCTFail("OpenAI should have at least 2 models")
            return
        }
        
        llmManager.selectModel(firstModel)
        XCTAssertEqual(llmManager.selectedModel?.id, firstModel.id)
        
        llmManager.selectModel(secondModel)
        XCTAssertEqual(llmManager.selectedModel?.id, secondModel.id)
    }
    
    
    // MARK: - Helper Methods
    
    private func clearAllConfiguration() {
        // Clear UserDefaults
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
            UserDefaults.standard.removeObject(forKey: "api_key_storage_method_\(provider.rawValue)")
        }
        
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        UserDefaults.standard.removeObject(forKey: "global_hotkey")
        UserDefaults.standard.removeObject(forKey: "notifications_enabled")
        
        // Reset validation states
        if llmManager != nil {
            for provider in LLMProvider.allCases {
                llmManager.validationStates[provider] = .none
            }
        }
    }
}
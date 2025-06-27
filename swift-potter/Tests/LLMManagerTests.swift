import XCTest
import Foundation
@testable import Potter

@MainActor
class LLMManagerTests: TestBase {
    var llmManager: LLMManager!
    
    override func setUp() async throws {
        try await super.setUp()
        
        // TestBase already handles forceUserDefaultsForTesting = true
        
        // Clear any existing settings first
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
        }
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
        
        // Clear keychain storage for all providers
        for provider in LLMProvider.allCases {
            _ = StorageAdapter.shared.removeAPIKey(for: provider)
        }
        
        llmManager = LLMManager()
    }
    
    override func tearDown() async throws {
        // Clean up UserDefaults
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
        }
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
        
        try await super.tearDown()
        
        // TestBase already handles forceUserDefaultsForTesting = false
    }
    
    func testInitialState() {
        XCTAssertEqual(llmManager.selectedProvider, .openAI)
        XCTAssertNotNil(llmManager.selectedModel)
        XCTAssertEqual(llmManager.selectedModel?.provider, .openAI)
        XCTAssertFalse(llmManager.isValidating)
        XCTAssertFalse(llmManager.hasValidProvider())
    }
    
    
    
    
    func testValidationStates() {
        // Initial state should not be valid
        XCTAssertFalse(llmManager.validationStates[.openAI]?.isValid ?? true)
        
        // Test validation state properties (now using APIKeyService ValidationState)
        let validState = ValidationState.valid
        let invalidState = ValidationState.invalid("Test error")
        let validatingState = ValidationState.validating
        let notValidatedState = ValidationState.notValidated
        
        XCTAssertTrue(validState.isValid)
        XCTAssertFalse(invalidState.isValid)
        XCTAssertFalse(validatingState.isValid)
        XCTAssertFalse(notValidatedState.isValid)
        
        XCTAssertNil(validState.errorMessage)
        XCTAssertEqual(invalidState.errorMessage, "Test error")
        XCTAssertNil(validatingState.errorMessage)
        XCTAssertNil(notValidatedState.errorMessage)
    }
    
    func testHasValidProvider() {
        // Ensure no API keys are stored for selected provider
        llmManager.setAPIKey("", for: .openAI)
        
        // Initially no valid provider
        XCTAssertFalse(llmManager.hasValidProvider())
        
        // Set one provider as valid
        APIKeyService.shared.setValidationStateForTesting(.valid, for: .openAI)
        XCTAssertTrue(llmManager.hasValidProvider())
        
        // Set to invalid - this should make hasValidProvider false
        // even if there's a stored API key, because validation state is explicitly invalid
        APIKeyService.shared.setValidationStateForTesting(.invalid("Test error"), for: .openAI)
        XCTAssertFalse(llmManager.hasValidProvider())
    }
    
    func testIsProviderConfigured() {
        // Initially not configured
        XCTAssertFalse(llmManager.isProviderConfigured(.openAI))
        
        // Set as valid
        APIKeyService.shared.setValidationStateForTesting(.valid, for: .openAI)
        XCTAssertTrue(llmManager.isProviderConfigured(.openAI))
        
        // Set as invalid
        APIKeyService.shared.setValidationStateForTesting(.invalid("Test error"), for: .openAI)
        XCTAssertFalse(llmManager.isProviderConfigured(.openAI))
    }
    
    func testGetCurrentValidationState() {
        llmManager.selectedProvider = .anthropic
        APIKeyService.shared.setValidationStateForTesting(.validating, for: .anthropic)
        
        let state = llmManager.getCurrentValidationState()
        XCTAssertFalse(state.isValid) // validating state should not be valid
    }
    
    
    func testProcessTextWithoutValidProvider() async {
        do {
            _ = try await llmManager.processText("test", prompt: "test prompt")
            XCTFail("Should throw error when no valid provider")
        } catch {
            XCTAssertTrue(error is PotterError)
        }
    }
    
    func testProcessTextWithoutAPIKey() async {
        llmManager.selectedModel = LLMModel.openAIModels.first
        
        do {
            _ = try await llmManager.processText("test", prompt: "test prompt")
            XCTFail("Should throw error when no API key")
        } catch {
            XCTAssertTrue(error is PotterError)
        }
    }
    
    func testProcessTextWithoutSelectedModel() async {
        llmManager.selectedModel = nil
        llmManager.setAPIKey("test-key", for: .openAI)
        
        do {
            _ = try await llmManager.processText("test", prompt: "test prompt")
            XCTFail("Should throw error when no model selected")
        } catch {
            XCTAssertTrue(error is PotterError)
        }
    }
    
    func testValidateEmptyAPIKey() async {
        await llmManager.validateAndSaveAPIKey("", for: .openAI)
        
        let state = llmManager.validationStates[.openAI]
        XCTAssertFalse(state?.isValid ?? true)
        XCTAssertEqual(state?.errorMessage, "API key cannot be empty")
        XCTAssertFalse(llmManager.isValidating)
    }
    
}
import XCTest
import Foundation
@testable import Potter

@MainActor
class LLMManagerTests: TestBase {
    var llmManager: LLMManager!
    
    override func setUp() async throws {
        try await super.setUp()
        
        // TestBase already handles forceUserDefaultsForTesting = true
        
        llmManager = LLMManager()
        
        // Clear any existing settings
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
        }
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
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
        
        // Test validation state properties
        let validState = LLMManager.ValidationState.valid
        let invalidState = LLMManager.ValidationState.invalid("Test error")
        let validatingState = LLMManager.ValidationState.validating
        let noneState = LLMManager.ValidationState.none
        
        XCTAssertTrue(validState.isValid)
        XCTAssertFalse(invalidState.isValid)
        XCTAssertFalse(validatingState.isValid)
        XCTAssertFalse(noneState.isValid)
        
        XCTAssertNil(validState.errorMessage)
        XCTAssertEqual(invalidState.errorMessage, "Test error")
        XCTAssertNil(validatingState.errorMessage)
        XCTAssertNil(noneState.errorMessage)
    }
    
    func testHasValidProvider() {
        // Initially no valid provider
        XCTAssertFalse(llmManager.hasValidProvider())
        
        // Set one provider as valid
        llmManager.validationStates[.openAI] = .valid
        XCTAssertTrue(llmManager.hasValidProvider())
        
        // Set to invalid
        llmManager.validationStates[.openAI] = .invalid("Test error")
        XCTAssertFalse(llmManager.hasValidProvider())
    }
    
    func testIsProviderConfigured() {
        // Initially not configured
        XCTAssertFalse(llmManager.isProviderConfigured(.openAI))
        
        // Set as valid
        llmManager.validationStates[.openAI] = .valid
        XCTAssertTrue(llmManager.isProviderConfigured(.openAI))
        
        // Set as invalid
        llmManager.validationStates[.openAI] = .invalid("Test error")
        XCTAssertFalse(llmManager.isProviderConfigured(.openAI))
    }
    
    func testGetCurrentValidationState() {
        llmManager.selectedProvider = .anthropic
        llmManager.validationStates[.anthropic] = .validating
        
        let state = llmManager.getCurrentValidationState()
        XCTAssertFalse(state.isValid) // validating state should not be valid
    }
    
    
    func testProcessTextWithoutValidProvider() async {
        do {
            _ = try await llmManager.processText("test", prompt: "test prompt")
            XCTFail("Should throw error when no valid provider")
        } catch {
            XCTAssertTrue(error is LLMError)
        }
    }
    
    func testProcessTextWithoutAPIKey() async {
        llmManager.selectedModel = LLMModel.openAIModels.first
        
        do {
            _ = try await llmManager.processText("test", prompt: "test prompt")
            XCTFail("Should throw error when no API key")
        } catch {
            XCTAssertTrue(error is LLMError)
        }
    }
    
    func testProcessTextWithoutSelectedModel() async {
        llmManager.selectedModel = nil
        llmManager.setAPIKey("test-key", for: .openAI)
        
        do {
            _ = try await llmManager.processText("test", prompt: "test prompt")
            XCTFail("Should throw error when no model selected")
        } catch {
            XCTAssertTrue(error is LLMError)
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
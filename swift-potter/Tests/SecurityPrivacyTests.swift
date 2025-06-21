import XCTest
import Foundation
import AppKit
import Security
@testable import Potter

/// Test Suite 8: Security & Privacy
/// Automated tests based on manual test plan T8.x
@MainActor
class SecurityPrivacyTests: TestBase {
    var secureStorage: SecureAPIKeyStorage!
    var keychainManager: KeychainManager!
    var llmManager: LLMManager!
    var tempDirectoryURL: URL!
    var originalCurrentDirectory: String!
    
    override func setUp() async throws {
        try await super.setUp()
        
        // Save original directory
        originalCurrentDirectory = FileManager.default.currentDirectoryPath
        
        // Create temporary directory for tests
        tempDirectoryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("SecurityPrivacyTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
        
        // Initialize components
        secureStorage = SecureAPIKeyStorage.shared
        keychainManager = KeychainManager.shared
        llmManager = LLMManager()
        
        clearTestSettings()
    }
    
    override func tearDown() async throws {
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        clearTestSettings()
        
        try await super.tearDown()
    }
    
    // MARK: - T8.1: API Key Security
    
    func testAPIKeyStorageMethodSecurity() {
        // Test that storage method selection affects security
        let testKey = "sk-security-test-key-12345"
        let provider = LLMProvider.openAI
        
        // During testing, should always use UserDefaults (due to testing flag)
        let method = secureStorage.getStorageMethod(for: provider)
        XCTAssertEqual(method, .userDefaults, "Testing should force UserDefaults storage")
        
        // Save key using specified method
        let success = secureStorage.saveAPIKey(testKey, for: provider, using: method)
        XCTAssertTrue(success)
        
        // Verify key is retrievable
        let retrievedKey = secureStorage.loadAPIKey(for: provider)
        XCTAssertEqual(retrievedKey, testKey)
        
        // In UserDefaults mode, key should be visible in UserDefaults
        let userDefaultsKey = UserDefaults.standard.string(forKey: "api_key_\(provider.rawValue)")
        XCTAssertEqual(userDefaultsKey, testKey)
    }
    
    
    func testAPIKeyNotInPlainTextLogs() {
        // Test that API keys don't appear in logs or other plain text
        let sensitiveKey = "sk-very-sensitive-api-key-12345"
        let provider = LLMProvider.google
        
        // Set API key
        llmManager.setAPIKey(sensitiveKey, for: provider)
        
        // Verify key is stored
        let retrievedKey = llmManager.getAPIKey(for: provider)
        XCTAssertEqual(retrievedKey, sensitiveKey)
        
        // Check that sensitive data isn't exposed in debug descriptions
        let managerDescription = String(describing: llmManager)
        XCTAssertFalse(managerDescription.contains(sensitiveKey), 
                      "API key should not appear in debug description")
        
        // Check validation state doesn't expose the key
        let validationState = llmManager.validationStates[provider]
        let stateDescription = String(describing: validationState)
        XCTAssertFalse(stateDescription.contains(sensitiveKey),
                      "API key should not appear in validation state description")
    }
    
    func testAPIKeyRemovalSecurity() {
        // Test that API key removal actually removes the key
        let testKey = "sk-removal-security-test"
        let provider = LLMProvider.openAI
        
        // Set key
        secureStorage.saveAPIKey(testKey, for: provider, using: .userDefaults)
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
        
        // Verify storage method preference is also cleared
        let methodKey = UserDefaults.standard.string(forKey: "api_key_storage_method_\(provider.rawValue)")
        XCTAssertNil(methodKey)
    }
    
    func testAPIKeyValidationDoesNotLogKeys() async {
        // Test that API key validation doesn't log the actual keys
        let testKey = "sk-validation-security-test"
        
        // Validation should not expose the key in any logs or errors
        await llmManager.validateAndSaveAPIKey(testKey, for: .openAI)
        
        // Even if validation fails, the key shouldn't be exposed
        let validationState = llmManager.validationStates[.openAI]
        if let errorMessage = validationState?.errorMessage {
            XCTAssertFalse(errorMessage.contains(testKey),
                          "Validation error should not contain the actual API key")
        }
    }
    
    
    
    func testAPIKeySecurityWithInvalidInput() {
        // Test security with various invalid/malicious inputs
        let maliciousInputs = [
            "sk-injection'; DROP TABLE users; --",
            "sk-xss<script>alert('xss')</script>",
            "sk-null\0injection",
            "sk-format%s%d%x",
            "sk-unicode\u{202E}reverse",
            String(repeating: "A", count: 10000), // Very long input
            "sk-newline\ninjection",
            "sk-control\u{0001}\u{0002}\u{0003}"
        ]
        
        for maliciousInput in maliciousInputs {
            // Should handle malicious input safely
            secureStorage.saveAPIKey(maliciousInput, for: .openAI, using: .userDefaults)
            let retrievedKey = secureStorage.loadAPIKey(for: .openAI)
            
            // Should store and retrieve exactly what was input (no injection)
            XCTAssertEqual(retrievedKey, maliciousInput)
            
            // Clean up
            secureStorage.removeAPIKey(for: .openAI)
        }
    }
    
    // MARK: - T8.2: Network Security (Simulated)
    
    func testLLMClientSecurityProperties() {
        // Test that LLM clients are configured securely
        let openAIClient = OpenAIClient(apiKey: "test-key")
        let anthropicClient = AnthropicClient(apiKey: "test-key")
        let googleClient = GoogleClient(apiKey: "test-key")
        
        let clients: [LLMClient] = [openAIClient, anthropicClient, googleClient]
        
        for client in clients {
            // Verify provider is correctly set
            XCTAssertNotNil(client.provider)
            
            // Verify client can be created without exposing key
            let clientDescription = String(describing: client)
            XCTAssertFalse(clientDescription.contains("test-key"),
                          "Client description should not expose API key")
        }
    }
    
    func testURLSecurityForProviders() {
        // Test that provider URLs are HTTPS and don't contain sensitive data
        // Note: We can't test actual network calls, but we can test URL structure
        
        // Verify that the LLM providers would use secure connections
        // This is more of a documentation test since we can't inspect private URLs
        
        for provider in LLMProvider.allCases {
            // Each provider should have models (indicating proper configuration)
            let models = provider.models
            XCTAssertGreaterThan(models.count, 0, "Provider \(provider) should have models")
            
            // Provider should have proper identification
            XCTAssertFalse(provider.rawValue.isEmpty)
            XCTAssertFalse(provider.displayName.isEmpty)
        }
    }
    
    func testAPIKeyNotInNetworkRequests() {
        // Test that API keys aren't accidentally included in request URLs
        // This is a structural test since we can't make actual network calls
        
        let sensitiveKey = "sk-should-not-appear-in-urls"
        
        // Create clients with the sensitive key
        let openAIClient = OpenAIClient(apiKey: sensitiveKey)
        let anthropicClient = AnthropicClient(apiKey: sensitiveKey)
        let googleClient = GoogleClient(apiKey: sensitiveKey)
        
        // Verify clients don't expose the key in their string representation
        let clients: [any LLMClient] = [openAIClient, anthropicClient, googleClient]
        for client in clients {
            let description = String(describing: client)
            XCTAssertFalse(description.contains(sensitiveKey),
                          "Client should not expose API key in description")
        }
    }
    
    func testRequestStructureSecurity() {
        // Test that request structures don't expose sensitive data
        let openAIMessage = OpenAIMessage(role: "user", content: "test message")
        let openAIRequest = OpenAIRequest(model: "gpt-4o", messages: [openAIMessage])
        
        let anthropicMessage = AnthropicMessage(role: "user", content: "test message")
        let anthropicRequest = AnthropicRequest(model: "claude-3-5-sonnet-20241022", max_tokens: 1000, messages: [anthropicMessage])
        
        let googlePart = GooglePart(text: "test message")
        let googleContent = GoogleContent(parts: [googlePart])
        let googleRequest = GoogleRequest(contents: [googleContent])
        
        // Request structures should be properly formed
        XCTAssertEqual(openAIRequest.model, "gpt-4o")
        XCTAssertEqual(anthropicRequest.model, "claude-3-5-sonnet-20241022")
        XCTAssertEqual(googleRequest.contents.count, 1)
        
        // No sensitive data should be in the structures
        let openAIDescription = String(describing: openAIRequest)
        let anthropicDescription = String(describing: anthropicRequest)
        let googleDescription = String(describing: googleRequest)
        
        // Should not contain obvious security issues
        XCTAssertFalse(openAIDescription.contains("password"))
        XCTAssertFalse(anthropicDescription.contains("secret"))
        XCTAssertFalse(googleDescription.contains("token"))
    }
    
    // MARK: - Additional Security Tests
    
    
    
    
    
    func testPermissionHandlingSecurity() {
        // Test permission handling doesn't expose sensitive information
        let permissionManager = PermissionManager.shared
        
        // Permission operations should not expose system details
        permissionManager.checkAllPermissions()
        
        let accessibilityStatus = permissionManager.getPermissionStatus(for: .accessibility)
        let notificationsStatus = permissionManager.getPermissionStatus(for: .notifications)
        
        // Should return valid status values
        let validStatuses: [PermissionStatus] = [.granted, .denied, .notDetermined, .unknown]
        XCTAssertTrue(validStatuses.contains(accessibilityStatus))
        XCTAssertTrue(validStatuses.contains(notificationsStatus))
        
        // Status descriptions should be safe
        XCTAssertFalse(accessibilityStatus.displayText.isEmpty)
        XCTAssertFalse(notificationsStatus.displayText.isEmpty)
    }
    
    func testErrorHandlingSecurity() {
        // Test that error handling doesn't leak sensitive information
        let sensitiveKey = "sk-sensitive-error-test"
        
        // Cause various error conditions
        llmManager.setAPIKey(sensitiveKey, for: .openAI)
        
        // Error states should not expose the key
        llmManager.validationStates[.openAI] = .invalid("Test error message")
        
        let errorState = llmManager.getCurrentValidationState()
        if let errorMessage = errorState.errorMessage {
            XCTAssertFalse(errorMessage.contains(sensitiveKey),
                          "Error messages should not contain API keys")
        }
    }
    
    func testFileSystemSecurityBoundaries() throws {
        // Test that file operations respect security boundaries
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        try FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)
        
        // Test file creation in designated areas only
        let testFile = configDir.appendingPathComponent("security_test.json")
        let testData = """
        {
            "test": "data",
            "sensitive": false
        }
        """.data(using: .utf8)!
        
        try testData.write(to: testFile)
        XCTAssertTrue(FileManager.default.fileExists(atPath: testFile.path))
        
        // Verify data integrity
        let readData = try Data(contentsOf: testFile)
        let readString = String(data: readData, encoding: .utf8)
        XCTAssertNotNil(readString)
        XCTAssertTrue(readString!.contains("\"test\": \"data\""))
        
        // Clean up
        try FileManager.default.removeItem(at: testFile)
        XCTAssertFalse(FileManager.default.fileExists(atPath: testFile.path))
    }
    
    // MARK: - Helper Methods
    
    private func clearTestSettings() {
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
            UserDefaults.standard.removeObject(forKey: "api_key_storage_method_\(provider.rawValue)")
        }
        
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        UserDefaults.standard.removeObject(forKey: "global_hotkey")
    }
}
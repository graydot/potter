import XCTest
@testable import Potter

/// Base test class that automatically configures secure storage for testing
/// All test classes should inherit from this to avoid keychain access during tests
class TestBase: XCTestCase {
    
    override class func setUp() {
        super.setUp()
        
        // Set the testing flag as early as possible
        SecureAPIKeyStorage.shared.forceUserDefaultsForTesting = true
    }
    
    override func setUp() {
        super.setUp()
        
        // Ensure the testing flag is set
        SecureAPIKeyStorage.shared.forceUserDefaultsForTesting = true
        
        // Clear any existing test data from UserDefaults
        clearTestUserDefaults()
    }
    
    override func tearDown() {
        // Reset testing mode
        SecureAPIKeyStorage.shared.forceUserDefaultsForTesting = false
        
        // Clean up test data
        clearTestUserDefaults()
        
        super.tearDown()
    }
    
    /// Clear UserDefaults keys that might be set during testing
    private func clearTestUserDefaults() {
        // Clear API keys
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
            UserDefaults.standard.removeObject(forKey: "api_key_storage_method_\(provider.rawValue)")
        }
        
        // Clear other settings
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        UserDefaults.standard.removeObject(forKey: "global_hotkey")
        UserDefaults.standard.removeObject(forKey: "notifications_enabled")
    }
}
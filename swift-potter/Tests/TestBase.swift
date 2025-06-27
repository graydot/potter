import XCTest
@testable import Potter

/// Base test class that automatically configures StorageAdapter for testing
/// All test classes should inherit from this to avoid keychain access during tests
class TestBase: XCTestCase {
    
    override class func setUp() {
        super.setUp()
        
        // Set the testing flag as early as possible to avoid keychain access
        StorageAdapter.shared.forceUserDefaultsForTesting = true
    }
    
    override func setUp() {
        super.setUp()
        
        // Ensure the testing flag is set to force UserDefaults usage
        StorageAdapter.shared.forceUserDefaultsForTesting = true
        
        // Create a unique UserDefaults suite for this test instance
        let testId = UUID().uuidString
        StorageAdapter.shared.testUserDefaults = UserDefaults(suiteName: "com.potter.tests.\(testId)")
        
        // Clear any existing test data from UserDefaults
        clearTestUserDefaults()
    }
    
    override func tearDown() {
        // Clean up test data before resetting
        clearTestUserDefaults()
        
        // Reset testing mode
        StorageAdapter.shared.forceUserDefaultsForTesting = false
        StorageAdapter.shared.testUserDefaults = nil
        
        super.tearDown()
    }
    
    /// Clear UserDefaults keys that might be set during testing
    private func clearTestUserDefaults() {
        let testDefaults = StorageAdapter.shared.testUserDefaults ?? UserDefaults.standard
        
        // Clear API keys
        for provider in LLMProvider.allCases {
            testDefaults.removeObject(forKey: "api_key_\(provider.rawValue)")
            testDefaults.removeObject(forKey: "api_key_storage_method_\(provider.rawValue)")
            testDefaults.removeObject(forKey: "has_api_key_\(provider.rawValue)")
        }
        
        // Clear other settings
        testDefaults.removeObject(forKey: "llm_provider")
        testDefaults.removeObject(forKey: "selected_model")
        testDefaults.removeObject(forKey: "current_prompt")
        testDefaults.removeObject(forKey: "global_hotkey")
        testDefaults.removeObject(forKey: "storage_method")
        
        // Force synchronization to ensure changes are persisted
        testDefaults.synchronize()
    }
}
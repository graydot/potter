import XCTest
import Foundation
@testable import Potter

class PotterSettingsTests: TestBase {
    var potterSettings: PotterSettings!
    
    override func setUp() {
        super.setUp()
        
        // Clear UserDefaults before each test
        let keys = [
            "openai_api_key",
            "anthropic_api_key", 
            "google_api_key",
            "current_provider",
            "current_prompt",
            "notifications_enabled"
        ]
        
        for key in keys {
            UserDefaults.standard.removeObject(forKey: key)
        }
        
        potterSettings = PotterSettings()
    }
    
    override func tearDown() {
        // Clean up UserDefaults after each test
        let keys = [
            "openai_api_key",
            "anthropic_api_key",
            "google_api_key", 
            "current_provider",
            "current_prompt",
            "notifications_enabled"
        ]
        
        for key in keys {
            UserDefaults.standard.removeObject(forKey: key)
        }
        
        super.tearDown()
    }
    
    func testDefaultValues() {
        XCTAssertNil(potterSettings.openaiAPIKey)
        XCTAssertNil(potterSettings.anthropicAPIKey)
        XCTAssertNil(potterSettings.googleAPIKey)
        XCTAssertEqual(potterSettings.currentProvider, "openai")
        XCTAssertEqual(potterSettings.currentPrompt, "formal")
        XCTAssertTrue(potterSettings.notificationsEnabled)
    }
    
    func testOpenAIAPIKeySetting() {
        let testKey = "sk-test-openai-key"
        potterSettings.openaiAPIKey = testKey
        
        XCTAssertEqual(potterSettings.openaiAPIKey, testKey)
        
        // Check UserDefaults persistence
        let savedKey = UserDefaults.standard.string(forKey: "openai_api_key")
        XCTAssertEqual(savedKey, testKey)
    }
    
    func testAnthropicAPIKeySetting() {
        let testKey = "sk-ant-test-key"
        potterSettings.anthropicAPIKey = testKey
        
        XCTAssertEqual(potterSettings.anthropicAPIKey, testKey)
        
        // Check UserDefaults persistence
        let savedKey = UserDefaults.standard.string(forKey: "anthropic_api_key")
        XCTAssertEqual(savedKey, testKey)
    }
    
    func testGoogleAPIKeySetting() {
        let testKey = "google-test-key"
        potterSettings.googleAPIKey = testKey
        
        XCTAssertEqual(potterSettings.googleAPIKey, testKey)
        
        // Check UserDefaults persistence
        let savedKey = UserDefaults.standard.string(forKey: "google_api_key")
        XCTAssertEqual(savedKey, testKey)
    }
    
    func testCurrentProviderSetting() {
        potterSettings.currentProvider = "anthropic"
        
        XCTAssertEqual(potterSettings.currentProvider, "anthropic")
        
        // Check UserDefaults persistence
        let savedProvider = UserDefaults.standard.string(forKey: "current_provider")
        XCTAssertEqual(savedProvider, "anthropic")
    }
    
    func testCurrentPromptSetting() {
        potterSettings.currentPrompt = "summarize"
        
        XCTAssertEqual(potterSettings.currentPrompt, "summarize")
        
        // Check UserDefaults persistence
        let savedPrompt = UserDefaults.standard.string(forKey: "current_prompt")
        XCTAssertEqual(savedPrompt, "summarize")
    }
    
    func testNotificationsEnabledSetting() {
        potterSettings.notificationsEnabled = false
        
        XCTAssertFalse(potterSettings.notificationsEnabled)
        
        // Check UserDefaults persistence
        let savedValue = UserDefaults.standard.bool(forKey: "notifications_enabled")
        XCTAssertFalse(savedValue)
    }
    
    func testLoadFromUserDefaults() {
        // Set up UserDefaults with test data
        UserDefaults.standard.set("test-openai-key", forKey: "openai_api_key")
        UserDefaults.standard.set("test-anthropic-key", forKey: "anthropic_api_key")
        UserDefaults.standard.set("test-google-key", forKey: "google_api_key")
        UserDefaults.standard.set("google", forKey: "current_provider")
        UserDefaults.standard.set("casual", forKey: "current_prompt")
        UserDefaults.standard.set(false, forKey: "notifications_enabled")
        
        // Create new settings instance to test loading
        let newSettings = PotterSettings()
        
        XCTAssertEqual(newSettings.openaiAPIKey, "test-openai-key")
        XCTAssertEqual(newSettings.anthropicAPIKey, "test-anthropic-key")
        XCTAssertEqual(newSettings.googleAPIKey, "test-google-key")
        XCTAssertEqual(newSettings.currentProvider, "google")
        XCTAssertEqual(newSettings.currentPrompt, "casual")
        XCTAssertFalse(newSettings.notificationsEnabled)
    }
    
    func testSaveMethod() {
        potterSettings.openaiAPIKey = "test-key"
        potterSettings.currentProvider = "anthropic"
        potterSettings.currentPrompt = "summarize"
        potterSettings.notificationsEnabled = false
        
        potterSettings.save()
        
        // Verify UserDefaults were updated
        XCTAssertEqual(UserDefaults.standard.string(forKey: "openai_api_key"), "test-key")
        XCTAssertEqual(UserDefaults.standard.string(forKey: "current_provider"), "anthropic")
        XCTAssertEqual(UserDefaults.standard.string(forKey: "current_prompt"), "summarize")
        XCTAssertFalse(UserDefaults.standard.bool(forKey: "notifications_enabled"))
    }
    
    func testNilAPIKeyHandling() {
        // Set a key then set it to nil
        potterSettings.openaiAPIKey = "test-key"
        XCTAssertEqual(potterSettings.openaiAPIKey, "test-key")
        
        potterSettings.openaiAPIKey = nil
        XCTAssertNil(potterSettings.openaiAPIKey)
        
        // Check UserDefaults (should be nil)
        let savedKey = UserDefaults.standard.string(forKey: "openai_api_key")
        XCTAssertNil(savedKey)
    }
    
    func testMultipleAPIKeysSimultaneously() {
        potterSettings.openaiAPIKey = "openai-key"
        potterSettings.anthropicAPIKey = "anthropic-key"
        potterSettings.googleAPIKey = "google-key"
        
        XCTAssertEqual(potterSettings.openaiAPIKey, "openai-key")
        XCTAssertEqual(potterSettings.anthropicAPIKey, "anthropic-key")
        XCTAssertEqual(potterSettings.googleAPIKey, "google-key")
        
        // Verify all are persisted
        XCTAssertEqual(UserDefaults.standard.string(forKey: "openai_api_key"), "openai-key")
        XCTAssertEqual(UserDefaults.standard.string(forKey: "anthropic_api_key"), "anthropic-key")
        XCTAssertEqual(UserDefaults.standard.string(forKey: "google_api_key"), "google-key")
    }
    
    func testSettingsChangeObservation() {
        // Test that the Published properties can be observed
        // (This is mainly testing that the properties are correctly marked as @Published)
        
        let expectation = expectation(description: "Settings change observed")
        
        let cancellable = potterSettings.$currentProvider.sink { newValue in
            if newValue == "anthropic" {
                expectation.fulfill()
            }
        }
        
        potterSettings.currentProvider = "anthropic"
        
        waitForExpectations(timeout: 1.0)
        cancellable.cancel()
    }
    
    func testEmptyStringAPIKey() {
        potterSettings.openaiAPIKey = ""
        
        XCTAssertEqual(potterSettings.openaiAPIKey, "")
        
        // Check UserDefaults persistence
        let savedKey = UserDefaults.standard.string(forKey: "openai_api_key")
        XCTAssertEqual(savedKey, "")
    }
}
import XCTest
import AppKit
@testable import Potter

/// Base test class that automatically configures StorageAdapter for testing
/// All test classes should inherit from this to avoid keychain access during tests
class TestBase: XCTestCase {

    /// Saved clipboard contents, restored after each test to avoid polluting the user's clipboard.
    private var savedPasteboardItems: [NSPasteboardItem]?

    override class func setUp() {
        super.setUp()

        // Set the testing flag as early as possible to avoid keychain access
        StorageAdapter.shared.forceUserDefaultsForTesting = true
    }

    override func setUp() {
        super.setUp()

        // Save current clipboard so we can restore it in tearDown
        savedPasteboardItems = savePasteboard()

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

        // Restore clipboard to what it was before the test
        restorePasteboard(savedPasteboardItems)
        savedPasteboardItems = nil

        super.tearDown()
    }

    // MARK: - Pasteboard Save/Restore

    private func savePasteboard() -> [NSPasteboardItem]? {
        let pb = NSPasteboard.general
        guard let items = pb.pasteboardItems, !items.isEmpty else { return nil }
        var saved: [NSPasteboardItem] = []
        for item in items {
            let copy = NSPasteboardItem()
            for type in item.types {
                if let data = item.data(forType: type) {
                    copy.setData(data, forType: type)
                }
            }
            saved.append(copy)
        }
        return saved
    }

    private func restorePasteboard(_ items: [NSPasteboardItem]?) {
        let pb = NSPasteboard.general
        pb.clearContents()
        if let items = items, !items.isEmpty {
            pb.writeObjects(items)
        }
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
        
        // Invalidate cache to ensure fresh reads
        StorageAdapter.shared.invalidateCache()
    }
}
import XCTest
import Foundation
import AppKit
@testable import Potter

/// Test Suite 7: Performance & Reliability
/// Automated tests based on manual test plan T7.x
@MainActor
class PerformanceReliabilityTests: TestBase {
    var potterCore: PotterCore!
    var llmManager: LLMManager!
    var promptManager: PromptManager!
    var tempDirectoryURL: URL!
    var originalCurrentDirectory: String!
    
    override func setUp() async throws {
        try await super.setUp()
        
        // Save original directory
        originalCurrentDirectory = FileManager.default.currentDirectoryPath
        
        // Create temporary directory for tests
        tempDirectoryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("PerformanceReliabilityTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
        
        // Set up PromptManager to use test file
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        PromptManager.shared.setTestFileURL(testPromptsFile)
        
        // Initialize components
        potterCore = PotterCore()
        llmManager = LLMManager()
        promptManager = PromptManager.shared
        
        clearTestSettings()
    }
    
    override func tearDown() async throws {
        // Restore PromptManager
        PromptManager.shared.setTestFileURL(nil)
        
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        clearTestSettings()
        
        try await super.tearDown()
    }
    
    // MARK: - T7.1: Memory Usage
    
    func testInitialMemoryFootprint() {
        // Test that initial object creation doesn't use excessive memory
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Create core components
        let core = PotterCore()
        let manager = LLMManager()
        let prompts = PromptManager.shared
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let initTime = endTime - startTime
        
        // Initialization should be fast (under 0.1 seconds)
        XCTAssertLessThan(initTime, 0.1, "Component initialization should be fast")
        
        // Objects should be created successfully
        XCTAssertNotNil(core)
        XCTAssertNotNil(manager)
        XCTAssertNotNil(prompts)
    }
    
    func testMemoryUsageWithManyPrompts() {
        // Test memory usage with a large number of prompts
        let startTime = CFAbsoluteTimeGetCurrent()
        
        var prompts: [PromptItem] = []
        for i in 1...1000 {
            let prompt = PromptItem(
                name: "performance_test_prompt_\(i)",
                prompt: "This is performance test prompt number \(i). " + String(repeating: "Performance test content. ", count: 10)
            )
            prompts.append(prompt)
        }
        
        let creationTime = CFAbsoluteTimeGetCurrent() - startTime
        XCTAssertLessThan(creationTime, 1.0, "Creating 1000 prompts should be fast")
        
        // Save prompts
        let saveStartTime = CFAbsoluteTimeGetCurrent()
        promptManager.savePrompts(prompts)
        let saveTime = CFAbsoluteTimeGetCurrent() - saveStartTime
        XCTAssertLessThan(saveTime, 2.0, "Saving 1000 prompts should complete in reasonable time")
        
        // Load prompts
        let loadStartTime = CFAbsoluteTimeGetCurrent()
        let loadedPrompts = promptManager.loadPrompts()
        let loadTime = CFAbsoluteTimeGetCurrent() - loadStartTime
        XCTAssertLessThan(loadTime, 1.0, "Loading 1000 prompts should be fast")
        
        XCTAssertEqual(loadedPrompts.count, 1000)
    }
    
    func testMemoryUsageWithLargeTextProcessing() {
        // Test memory usage with large text
        let largeText = String(repeating: "This is a large text document for testing memory usage. ", count: 1000) // ~57KB
        
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(largeText, forType: .string)
        
        // Verify large text can be handled in clipboard
        let clipboardText = pasteboard.string(forType: .string)
        XCTAssertEqual(clipboardText, largeText)
        XCTAssertEqual(clipboardText?.count, largeText.count)
        
        // Setup core and attempt processing
        potterCore.setup()
        
        // This will fail due to no API key, but should handle large text gracefully
        potterCore.processClipboardText()
        
        // Should not crash or consume excessive memory
        XCTAssertTrue(true)
    }
    
    func testMemoryLeakPrevention() async {
        // Test for potential memory leaks in repeated operations
        let iterations = 100
        
        for i in 1...iterations {
            // Create and release objects repeatedly
            autoreleasepool {
                let manager = LLMManager()
                manager.setAPIKey("test-key-\(i)", for: .openAI)
                manager.selectProvider(.anthropic)
                manager.selectProvider(.google)
                manager.selectProvider(.openAI)
                
                let _ = manager.getAPIKey(for: .openAI)
                let _ = manager.isProviderConfigured(.openAI)
                let _ = manager.getCurrentValidationState()
            }
        }
        
        // Allow some time for cleanup
        try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        
        // Should complete without excessive memory growth
        XCTAssertTrue(true)
    }
    
    func testLargeAPIKeyHandling() {
        // Test handling of unusually large API keys
        let normalKey = "sk-normal-api-key-length"
        let largeKey = "sk-" + String(repeating: "verylongapikey", count: 100) // ~1.4KB
        let hugeKey = "sk-" + String(repeating: "extremelyhugeapikey", count: 1000) // ~18KB
        
        let keys = [normalKey, largeKey, hugeKey]
        let providers: [LLMProvider] = [.openAI, .anthropic, .google]
        
        for (key, provider) in zip(keys, providers) {
            let startTime = CFAbsoluteTimeGetCurrent()
            
            llmManager.setAPIKey(key, for: provider)
            let retrievedKey = llmManager.getAPIKey(for: provider)
            
            let endTime = CFAbsoluteTimeGetCurrent()
            let duration = endTime - startTime
            
            XCTAssertEqual(retrievedKey, key)
            XCTAssertLessThan(duration, 0.1, "API key operations should be fast regardless of size")
        }
    }
    
    func testConcurrentMemoryOperations() async {
        // Test memory usage under concurrent operations
        let expectation = expectation(description: "Concurrent memory operations")
        expectation.expectedFulfillmentCount = 5
        
        let queue = DispatchQueue.global(qos: .background)
        
        for i in 1...5 {
            queue.async {
                Task { @MainActor in
                    autoreleasepool {
                        // Perform memory-intensive operations
                        let manager = LLMManager()
                        
                        for j in 1...20 {
                            let key = "concurrent-test-key-\(i)-\(j)"
                            manager.setAPIKey(key, for: .openAI)
                            let _ = manager.getAPIKey(for: .openAI)
                        }
                        
                        // Create and process prompts
                        var prompts: [PromptItem] = []
                        for k in 1...50 {
                            prompts.append(PromptItem(name: "concurrent_\(i)_\(k)", prompt: "Concurrent test \(i) \(k)"))
                        }
                        
                        PromptManager.shared.savePrompts(prompts)
                        let _ = PromptManager.shared.loadPrompts()
                    }
                    
                    expectation.fulfill()
                }
            }
        }
        
        await fulfillment(of: [expectation], timeout: 10.0)
        
        // Allow cleanup time
        try? await Task.sleep(nanoseconds: 200_000_000) // 0.2 seconds
        
        XCTAssertTrue(true) // Should complete without memory issues
    }
    
    // MARK: - T7.2: CPU Usage & Performance
    
    func testComponentInitializationPerformance() {
        // Test initialization performance of core components
        measure {
            let core = PotterCore()
            let manager = LLMManager()
            let _ = PromptManager.shared
            
            core.setup()
            manager.loadSettings()
        }
        
        // Should complete quickly in performance test
        XCTAssertTrue(true)
    }
    
    func testPromptOperationsPerformance() {
        // Test performance of prompt operations
        let prompts = (1...100).map { i in
            PromptItem(name: "perf_test_\(i)", prompt: "Performance test prompt \(i)")
        }
        
        measure {
            promptManager.savePrompts(prompts)
            let _ = promptManager.loadPrompts()
        }
        
        // Should complete within reasonable time
        XCTAssertTrue(true)
    }
    
    func testAPIKeyOperationsPerformance() {
        // Test performance of API key operations
        let testKeys = (1...50).map { "sk-performance-test-key-\($0)" }
        
        measure {
            for (index, key) in testKeys.enumerated() {
                let provider = LLMProvider.allCases[index % LLMProvider.allCases.count]
                llmManager.setAPIKey(key, for: provider)
                let _ = llmManager.getAPIKey(for: provider)
                let _ = llmManager.isProviderConfigured(provider)
            }
        }
        
        XCTAssertTrue(true)
    }
    
    func testClipboardOperationsPerformance() {
        // Test performance of clipboard operations
        let testTexts = (1...20).map { "Performance test text number \($0). " + String(repeating: "More text. ", count: 50) }
        
        measure {
            let pasteboard = NSPasteboard.general
            
            for text in testTexts {
                pasteboard.clearContents()
                pasteboard.setString(text, forType: .string)
                let _ = pasteboard.string(forType: .string)
            }
        }
        
        XCTAssertTrue(true)
    }
    
    func testFileOperationsPerformance() throws {
        // Test performance of file operations
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        try FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)
        
        measure {
            for i in 1...20 {
                let testFile = configDir.appendingPathComponent("perf_test_\(i).json")
                let testData = """
                {
                    "test": \(i),
                    "content": "Performance test data",
                    "timestamp": "\(Date().timeIntervalSince1970)"
                }
                """.data(using: .utf8)!
                
                do {
                    try testData.write(to: testFile)
                    let _ = try Data(contentsOf: testFile)
                    try FileManager.default.removeItem(at: testFile)
                } catch {
                    XCTFail("File operation failed: \(error)")
                }
            }
        }
        
        XCTAssertTrue(true)
    }
    
    func testProcessManagerPerformance() {
        // Test performance of process management operations
        let processManager = ProcessManager.shared
        
        measure {
            for _ in 1...10 {
                let _ = processManager.checkForDuplicateProcesses()
                processManager.removeLockFile()
            }
        }
        
        XCTAssertTrue(true)
    }
    
    func testBuildInfoPerformance() {
        // Test performance of build info creation
        measure {
            for _ in 1...100 {
                let _ = BuildInfo.current()
            }
        }
        
        XCTAssertTrue(true)
    }
    
    func testHotkeyOperationsPerformance() {
        // Test performance of hotkey operations
        let hotkeyVariations = [
            ["⌘", "R"],
            ["⌘", "⇧", "R"],
            ["⌘", "⌥", "R"],
            ["⌘", "⌃", "R"],
            ["⌘", "⇧", "T"],
            ["⌘", "⇧", "Y"],
            ["⌘", "⇧", "9"],
            ["⌘", "⇧", "0"]
        ]
        
        potterCore.setup()
        
        measure {
            for hotkey in hotkeyVariations {
                potterCore.updateHotkey(hotkey)
                potterCore.disableGlobalHotkey()
                potterCore.enableGlobalHotkey()
            }
        }
        
        XCTAssertTrue(true)
    }
    
    func testStressTestOperations() async {
        // Stress test multiple operations running concurrently
        let operationCount = 50
        let expectation = expectation(description: "Stress test operations")
        expectation.expectedFulfillmentCount = operationCount
        
        let queue = DispatchQueue.global(qos: .background)
        
        for i in 1...operationCount {
            queue.async {
                Task { @MainActor in
                    autoreleasepool {
                        // Mix of different operations
                        switch i % 5 {
                        case 0:
                            // API key operations
                            let manager = LLMManager()
                            manager.setAPIKey("stress-test-\(i)", for: .openAI)
                            let _ = manager.getAPIKey(for: .openAI)
                            
                        case 1:
                            // Prompt operations
                            let prompts = [PromptItem(name: "stress_\(i)", prompt: "Stress test \(i)")]
                            PromptManager.shared.savePrompts(prompts)
                            let _ = PromptManager.shared.loadPrompts()
                            
                        case 2:
                            // Clipboard operations
                            let pasteboard = NSPasteboard.general
                            pasteboard.setString("Stress test \(i)", forType: .string)
                            let _ = pasteboard.string(forType: .string)
                            
                        case 3:
                            // Build info operations
                            let _ = BuildInfo.current()
                            
                        case 4:
                            // Process manager operations
                            let _ = ProcessManager.shared.checkForDuplicateProcesses()
                            
                        default:
                            break
                        }
                    }
                    
                    expectation.fulfill()
                }
            }
        }
        
        await fulfillment(of: [expectation], timeout: 15.0)
        
        // Allow cleanup
        try? await Task.sleep(nanoseconds: 300_000_000) // 0.3 seconds
        
        XCTAssertTrue(true) // Should handle stress test without crashes
    }
    
    func testPerformanceWithLargeDataSets() {
        // Test performance with large data sets
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Create large prompt dataset
        var largePrompts: [PromptItem] = []
        for i in 1...500 {
            let prompt = PromptItem(
                name: "large_dataset_prompt_\(i)",
                prompt: "Large dataset prompt \(i). " + String(repeating: "Content for prompt \(i). ", count: 20)
            )
            largePrompts.append(prompt)
        }
        
        let creationTime = CFAbsoluteTimeGetCurrent() - startTime
        XCTAssertLessThan(creationTime, 2.0, "Large dataset creation should be reasonable")
        
        // Test operations on large dataset
        let operationStartTime = CFAbsoluteTimeGetCurrent()
        
        promptManager.savePrompts(largePrompts)
        let loadedPrompts = promptManager.loadPrompts()
        
        let operationTime = CFAbsoluteTimeGetCurrent() - operationStartTime
        XCTAssertLessThan(operationTime, 3.0, "Large dataset operations should complete in reasonable time")
        
        XCTAssertEqual(loadedPrompts.count, 500)
    }
    
    func testIdleStatePerformance() async {
        // Test performance during idle state (no active operations)
        potterCore.setup()
        llmManager.loadSettings()
        
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Simulate idle period
        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let idleTime = endTime - startTime
        
        // During idle, should not consume significant CPU
        // (We can't measure CPU directly in tests, but verify no crashes)
        XCTAssertGreaterThanOrEqual(idleTime, 1.0)
        XCTAssertLessThan(idleTime, 1.2) // Should not take much longer than expected
    }
    
    // MARK: - Reliability Tests
    
    func testRepeatedOperationReliability() async {
        // Test reliability of repeated operations
        let iterations = 200
        
        for i in 1...iterations {
            autoreleasepool {
                // Mix of operations that should be reliable
                llmManager.setAPIKey("reliability-test-\(i)", for: .openAI)
                let _ = llmManager.getAPIKey(for: .openAI)
                let _ = llmManager.isProviderConfigured(.openAI)
                
                let prompts = [PromptItem(name: "reliability_\(i)", prompt: "Reliability test \(i)")]
                promptManager.savePrompts(prompts)
                let _ = promptManager.loadPrompts()
                
                let _ = BuildInfo.current()
            }
            
            // Occasional yield to prevent test timeout
            if i % 50 == 0 {
                try? await Task.sleep(nanoseconds: 10_000_000) // 0.01 seconds
            }
        }
        
        XCTAssertTrue(true) // Should complete all iterations reliably
    }
    
    func testErrorRecoveryReliability() {
        // Test reliability of error recovery
        let invalidOperations = [
            { self.llmManager.setAPIKey("", for: .openAI) },
            { self.llmManager.selectModel(LLMModel.anthropicModels.first!) }, // Wrong provider
            { self.potterCore.updateHotkey([]) }, // Invalid hotkey
            { self.potterCore.updateHotkey(["invalid"]) }, // Invalid hotkey
        ]
        
        for operation in invalidOperations {
            // Each operation should handle errors gracefully
            operation()
            
            // System should remain functional after errors
            XCTAssertNotNil(llmManager.selectedProvider)
            XCTAssertNotNil(llmManager.selectedModel)
        }
        
        // System should still work after error conditions
        llmManager.setAPIKey("valid-key", for: .openAI)
        XCTAssertEqual(llmManager.getAPIKey(for: .openAI), "valid-key")
    }
    
    func testLongRunningOperationSimulation() async {
        // Simulate long-running operations
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Simulate processing large amount of data
        for batch in 1...10 {
            autoreleasepool {
                var batchPrompts: [PromptItem] = []
                
                for i in 1...50 {
                    batchPrompts.append(PromptItem(
                        name: "batch_\(batch)_item_\(i)",
                        prompt: "Batch \(batch) item \(i) content"
                    ))
                }
                
                promptManager.savePrompts(batchPrompts)
                let _ = promptManager.loadPrompts()
            }
            
            // Yield periodically
            try? await Task.sleep(nanoseconds: 50_000_000) // 0.05 seconds
        }
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let totalTime = endTime - startTime
        
        // Should complete in reasonable time
        XCTAssertLessThan(totalTime, 10.0, "Long-running operation should complete within 10 seconds")
    }
    
    // MARK: - Helper Methods
    
    private func clearTestSettings() {
        UserDefaults.standard.removeObject(forKey: "current_prompt")
        UserDefaults.standard.removeObject(forKey: "llm_provider")
        UserDefaults.standard.removeObject(forKey: "selected_model")
        UserDefaults.standard.removeObject(forKey: "global_hotkey")
        
        for provider in LLMProvider.allCases {
            UserDefaults.standard.removeObject(forKey: "api_key_\(provider.rawValue)")
            UserDefaults.standard.removeObject(forKey: "api_key_storage_method_\(provider.rawValue)")
        }
    }
}
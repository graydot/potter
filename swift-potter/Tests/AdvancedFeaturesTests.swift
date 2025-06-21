import XCTest
import Foundation
import AppKit
@testable import Potter

/// Test Suite 6: Advanced Features
/// Automated tests based on manual test plan T6.x
@MainActor
class AdvancedFeaturesTests: TestBase {
    var promptManager: PromptManager!
    var tempDirectoryURL: URL!
    var originalCurrentDirectory: String!
    
    override func setUp() async throws {
        try await super.setUp()
        
        // Save original directory
        originalCurrentDirectory = FileManager.default.currentDirectoryPath
        
        // Create temporary directory for tests
        tempDirectoryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("AdvancedFeaturesTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
        
        // Set up PromptManager to use test file
        let testPromptsFile = tempDirectoryURL.appendingPathComponent("test_prompts.json")
        PromptManager.shared.setTestFileURL(testPromptsFile)
        
        promptManager = PromptManager.shared
    }
    
    override func tearDown() async throws {
        // Restore PromptManager
        PromptManager.shared.setTestFileURL(nil)
        
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        try await super.tearDown()
    }
    
    // MARK: - T6.1: Prompt Management
    
    func testCreateManyCustomPrompts() {
        // Test creating 20+ custom prompts
        var prompts: [PromptItem] = []
        
        for i in 1...25 {
            let prompt = PromptItem(
                name: "custom_prompt_\(i)",
                prompt: "This is custom prompt number \(i). Please process the text accordingly."
            )
            prompts.append(prompt)
        }
        
        promptManager.savePrompts(prompts)
        let loadedPrompts = promptManager.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 25)
        
        // Verify all prompts are saved correctly
        for i in 1...25 {
            let expectedName = "custom_prompt_\(i)"
            XCTAssertTrue(loadedPrompts.contains { $0.name == expectedName },
                         "Should contain prompt '\(expectedName)'")
        }
    }
    
    func testEditExistingPrompts() {
        // Test editing existing prompts
        let originalPrompts = [
            PromptItem(name: "original1", prompt: "Original prompt 1"),
            PromptItem(name: "original2", prompt: "Original prompt 2"),
            PromptItem(name: "original3", prompt: "Original prompt 3")
        ]
        
        promptManager.savePrompts(originalPrompts)
        
        // Edit prompts
        var editedPrompts = promptManager.loadPrompts()
        editedPrompts[0] = PromptItem(name: "edited1", prompt: "Edited prompt 1")
        editedPrompts[1] = PromptItem(name: editedPrompts[1].name, prompt: "Edited prompt 2 content")
        
        promptManager.savePrompts(editedPrompts)
        let finalPrompts = promptManager.loadPrompts()
        
        XCTAssertEqual(finalPrompts.count, 3)
        XCTAssertEqual(finalPrompts[0].name, "edited1")
        XCTAssertEqual(finalPrompts[0].prompt, "Edited prompt 1")
        XCTAssertEqual(finalPrompts[1].name, "original2")
        XCTAssertEqual(finalPrompts[1].prompt, "Edited prompt 2 content")
        XCTAssertEqual(finalPrompts[2].name, "original3")
    }
    
    func testDeletePrompts() {
        // Test deleting prompts
        let originalPrompts = [
            PromptItem(name: "keep1", prompt: "Keep this prompt"),
            PromptItem(name: "delete1", prompt: "Delete this prompt"),
            PromptItem(name: "keep2", prompt: "Keep this too"),
            PromptItem(name: "delete2", prompt: "Delete this too")
        ]
        
        promptManager.savePrompts(originalPrompts)
        
        // Delete specific prompts (keep only the "keep" ones)
        let filteredPrompts = originalPrompts.filter { $0.name.hasPrefix("keep") }
        promptManager.savePrompts(filteredPrompts)
        
        let remainingPrompts = promptManager.loadPrompts()
        
        XCTAssertEqual(remainingPrompts.count, 2)
        XCTAssertTrue(remainingPrompts.contains { $0.name == "keep1" })
        XCTAssertTrue(remainingPrompts.contains { $0.name == "keep2" })
        XCTAssertFalse(remainingPrompts.contains { $0.name == "delete1" })
        XCTAssertFalse(remainingPrompts.contains { $0.name == "delete2" })
    }
    
    func testPromptsWithInvalidCharacters() {
        // Test prompts with various special characters
        let specialCharacterPrompts = [
            PromptItem(name: "emoji_test", prompt: "🚀 Process this with emojis! 🎯✨"),
            PromptItem(name: "unicode_test", prompt: "Unicode: café naïve résumé 中文 العربية"),
            PromptItem(name: "symbols_test", prompt: "Symbols: @#$%^&*()_+-=[]{}|;':\",./<>?"),
            PromptItem(name: "newlines_test", prompt: "Line 1\nLine 2\r\nLine 3\rLine 4"),
            PromptItem(name: "quotes_test", prompt: "Quote test: \"hello\" 'world' `code` ´accent"),
            PromptItem(name: "control_test", prompt: "Control\tchars\\vand\\fwhitespace   "),
        ]
        
        promptManager.savePrompts(specialCharacterPrompts)
        let loadedPrompts = promptManager.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, specialCharacterPrompts.count)
        
        for (original, loaded) in zip(specialCharacterPrompts, loadedPrompts) {
            XCTAssertEqual(loaded.name, original.name)
            XCTAssertEqual(loaded.prompt, original.prompt)
        }
    }
    
    func testVeryLongPromptNames() {
        // Test very long prompt names and content
        let longName = String(repeating: "VeryLongPromptName", count: 10) // 180+ chars
        let longContent = String(repeating: "This is a very long prompt content that tests the system's ability to handle large amounts of text. ", count: 50) // 5000+ chars
        
        let longPrompt = PromptItem(name: longName, prompt: longContent)
        promptManager.savePrompts([longPrompt])
        
        let loadedPrompts = promptManager.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 1)
        XCTAssertEqual(loadedPrompts[0].name, longName)
        XCTAssertEqual(loadedPrompts[0].prompt, longContent)
        XCTAssertEqual(loadedPrompts[0].prompt.count, longContent.count)
    }
    
    func testPromptOrdering() {
        // Test prompt ordering and organization
        let orderedPrompts = [
            PromptItem(name: "A_first", prompt: "First prompt"),
            PromptItem(name: "B_second", prompt: "Second prompt"),
            PromptItem(name: "C_third", prompt: "Third prompt"),
            PromptItem(name: "Z_last", prompt: "Last prompt")
        ]
        
        promptManager.savePrompts(orderedPrompts)
        let loadedPrompts = promptManager.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 4)
        
        // Check that prompts maintain their order
        XCTAssertEqual(loadedPrompts[0].name, "A_first")
        XCTAssertEqual(loadedPrompts[1].name, "B_second")
        XCTAssertEqual(loadedPrompts[2].name, "C_third")
        XCTAssertEqual(loadedPrompts[3].name, "Z_last")
    }
    
    func testPromptDuplicateHandling() {
        // Test handling of prompts with duplicate names
        let promptsWithDuplicates = [
            PromptItem(name: "duplicate", prompt: "First version"),
            PromptItem(name: "unique", prompt: "Unique prompt"),
            PromptItem(name: "duplicate", prompt: "Second version"),
            PromptItem(name: "another_unique", prompt: "Another unique")
        ]
        
        promptManager.savePrompts(promptsWithDuplicates)
        let loadedPrompts = promptManager.loadPrompts()
        
        // All prompts should be saved (even with duplicate names, since they have different IDs)
        XCTAssertEqual(loadedPrompts.count, 4)
        
        // But we should have two prompts with the same name but different IDs
        let duplicatePrompts = loadedPrompts.filter { $0.name == "duplicate" }
        XCTAssertEqual(duplicatePrompts.count, 2)
        XCTAssertNotEqual(duplicatePrompts[0].id, duplicatePrompts[1].id)
    }
    
    func testPromptBatchOperations() {
        // Test batch operations on prompts
        var batchPrompts: [PromptItem] = []
        
        // Create a large batch
        for category in ["translate", "summarize", "format", "analyze"] {
            for i in 1...10 {
                let prompt = PromptItem(
                    name: "\(category)_\(i)",
                    prompt: "This is a \(category) prompt number \(i)"
                )
                batchPrompts.append(prompt)
            }
        }
        
        // Save batch
        promptManager.savePrompts(batchPrompts)
        let loadedBatch = promptManager.loadPrompts()
        
        XCTAssertEqual(loadedBatch.count, 40)
        
        // Test filtering by category
        let translatePrompts = loadedBatch.filter { $0.name.hasPrefix("translate") }
        XCTAssertEqual(translatePrompts.count, 10)
        
        let summarizePrompts = loadedBatch.filter { $0.name.hasPrefix("summarize") }
        XCTAssertEqual(summarizePrompts.count, 10)
    }
    
    func testPromptValidation() {
        // Test prompt validation scenarios
        let validationPrompts = [
            PromptItem(name: "", prompt: "Empty name"),
            PromptItem(name: "empty_content", prompt: ""),
            PromptItem(name: "whitespace_only", prompt: "   \n\t   "),
            PromptItem(name: "normal", prompt: "Normal prompt"),
            PromptItem(name: "single_char", prompt: "a"),
            PromptItem(name: "just_whitespace_name", prompt: "Good content")
        ]
        
        promptManager.savePrompts(validationPrompts)
        let loadedPrompts = promptManager.loadPrompts()
        
        // All prompts should be saved (validation is UI responsibility)
        XCTAssertEqual(loadedPrompts.count, validationPrompts.count)
        
        // Verify edge cases are preserved
        let emptyNamePrompt = loadedPrompts.first { $0.name == "" }
        XCTAssertNotNil(emptyNamePrompt)
        XCTAssertEqual(emptyNamePrompt?.prompt, "Empty name")
        
        let emptyContentPrompt = loadedPrompts.first { $0.name == "empty_content" }
        XCTAssertNotNil(emptyContentPrompt)
        XCTAssertEqual(emptyContentPrompt?.prompt, "")
    }
    
    // MARK: - T6.2: Build Information & Diagnostics
    
    func testBuildInformationAccuracy() {
        // Test BuildInfo provides accurate information
        let buildInfo = BuildInfo.current()
        
        // Build ID should follow expected format
        XCTAssertFalse(buildInfo.buildId.isEmpty)
        XCTAssertTrue(buildInfo.buildId.contains("-"))
        XCTAssertTrue(buildInfo.buildId.hasSuffix("-DEV"))
        
        // Version should be valid
        XCTAssertFalse(buildInfo.version.isEmpty)
        XCTAssertTrue(buildInfo.version.contains("."))
        XCTAssertEqual(buildInfo.version, "2.0.0-dev")
        
        // Build date should be formatted correctly
        XCTAssertFalse(buildInfo.buildDate.isEmpty)
        XCTAssertTrue(buildInfo.buildDate.contains("-"))
        XCTAssertTrue(buildInfo.buildDate.contains(":"))
        
        // Process ID should be current process
        XCTAssertEqual(buildInfo.processId, getpid())
        
        // Build date should be formatted correctly
        XCTAssertFalse(buildInfo.buildDate.isEmpty)
        XCTAssertTrue(buildInfo.buildDate.contains("-"))
        XCTAssertTrue(buildInfo.buildDate.contains(":"))
    }
    
    func testBuildIdUniqueness() {
        // Test that build IDs have consistent structure across instances
        let buildInfo1 = BuildInfo.current()
        let buildInfo2 = BuildInfo.current()
        
        // Build IDs should be different due to UUID generation
        XCTAssertNotEqual(buildInfo1.buildId, buildInfo2.buildId, "Build IDs should be unique due to UUID generation")
        
        // But both should follow the same format
        XCTAssertTrue(buildInfo1.buildId.hasSuffix("-DEV"))
        XCTAssertTrue(buildInfo2.buildId.hasSuffix("-DEV"))
        
        // Other properties should be the same for current build
        XCTAssertEqual(buildInfo1.version, buildInfo2.version)
        XCTAssertEqual(buildInfo1.processId, buildInfo2.processId)
    }
    
    func testVersionNumberConsistency() {
        // Test version numbers are consistent across different components
        let buildInfo = BuildInfo.current()
        
        // Version should match expected development version
        XCTAssertEqual(buildInfo.version, "2.0.0-dev")
        
        // Build ID should contain version-related info
        XCTAssertTrue(buildInfo.buildId.contains("-DEV"))
    }
    
    func testDiagnosticInformationFormat() {
        // Test diagnostic information is properly formatted
        let buildInfo = BuildInfo.current()
        
        // Test that all fields are non-empty
        XCTAssertFalse(buildInfo.buildId.isEmpty)
        XCTAssertFalse(buildInfo.version.isEmpty)
        XCTAssertFalse(buildInfo.buildDate.isEmpty)
        XCTAssertFalse(buildInfo.buildDate.isEmpty)
        
        // Test that numeric fields are valid
        XCTAssertGreaterThan(buildInfo.processId, 0)
        
        // Test string format validity
        XCTAssertFalse(buildInfo.buildId.contains(" "))
        XCTAssertFalse(buildInfo.version.contains(" "))
    }
    
    func testBuildInfoSerialization() {
        // Test BuildInfo structure consistency
        let originalBuildInfo = BuildInfo.current()
        let secondBuildInfo = BuildInfo.current()
        
        // Test that build info has consistent structure
        XCTAssertEqual(originalBuildInfo.version, secondBuildInfo.version)
        XCTAssertEqual(originalBuildInfo.processId, secondBuildInfo.processId)
        
        // Build IDs might be different due to UUID generation
        XCTAssertTrue(originalBuildInfo.buildId.hasSuffix("-DEV"))
        XCTAssertTrue(secondBuildInfo.buildId.hasSuffix("-DEV"))
    }
    
    func testProcessManagerDiagnostics() {
        // Test ProcessManager provides useful diagnostic info
        let processManager = ProcessManager.shared
        
        // Test getting current build info
        let buildInfo = BuildInfo.current()
        XCTAssertNotNil(buildInfo)
        
        // Test process detection functionality
        let result = processManager.checkForDuplicateProcesses()
        XCTAssertNotNil(result)
        
        // Should either find no duplicates or handle them appropriately
        switch result {
        case .noDuplicates:
            XCTAssertTrue(true) // Expected for clean test environment
        case .foundDuplicates(let processes):
            XCTAssertGreaterThan(processes.count, 0)
            for process in processes {
                XCTAssertGreaterThan(process.pid, 0)
                XCTAssertNotNil(process.buildInfo)
            }
        }
    }
    
    func testDiagnosticDataCollection() {
        // Test collecting various diagnostic data points
        let buildInfo = BuildInfo.current()
        let processManager = ProcessManager.shared
        
        // Collect diagnostic information
        let diagnosticData: [String: Any] = [
            "buildId": buildInfo.buildId,
            "version": buildInfo.version,
            "processId": buildInfo.processId,
            "buildDate": buildInfo.buildDate,
            "hasLockFile": FileManager.default.fileExists(atPath: tempDirectoryURL.appendingPathComponent("config/potter.lock").path)
        ]
        
        // Verify diagnostic data
        XCTAssertFalse((diagnosticData["buildId"] as? String)?.isEmpty ?? true)
        XCTAssertFalse((diagnosticData["version"] as? String)?.isEmpty ?? true)
        XCTAssertGreaterThan(diagnosticData["processId"] as? Int32 ?? 0, 0)
        XCTAssertNotNil(diagnosticData["hasLockFile"] as? Bool)
    }
    
    func testSystemEnvironmentDiagnostics() {
        // Test system environment diagnostic information
        let fileManager = FileManager.default
        
        // Test working directory access
        let currentDirectory = fileManager.currentDirectoryPath
        XCTAssertFalse(currentDirectory.isEmpty)
        
        // Test temporary directory access
        let tempDirectory = fileManager.temporaryDirectory
        XCTAssertTrue(fileManager.fileExists(atPath: tempDirectory.path))
        
        // Test UserDefaults access
        UserDefaults.standard.set("diagnostic_test", forKey: "test_diagnostic_key")
        let testValue = UserDefaults.standard.string(forKey: "test_diagnostic_key")
        XCTAssertEqual(testValue, "diagnostic_test")
        UserDefaults.standard.removeObject(forKey: "test_diagnostic_key")
    }
    
    func testErrorDiagnostics() {
        // Test diagnostic information during error scenarios
        let promptManager = PromptManager.shared
        
        // Create a scenario that might cause issues
        let problematicPrompts = [
            PromptItem(name: String(repeating: "x", count: 1000), prompt: "Very long name"),
            PromptItem(name: "normal", prompt: String(repeating: "Very long content. ", count: 1000))
        ]
        
        // This should not crash, even with problematic data
        promptManager.savePrompts(problematicPrompts)
        let loadedPrompts = promptManager.loadPrompts()
        
        XCTAssertEqual(loadedPrompts.count, 2)
        
        // Verify the system handled the edge cases
        XCTAssertTrue(loadedPrompts[0].name.count >= 1000)
        XCTAssertTrue(loadedPrompts[1].prompt.count >= 10000)
    }
    
    func testPerformanceDiagnostics() {
        // Test performance-related diagnostics
        let startTime = CFAbsoluteTimeGetCurrent()
        
        // Perform some operations that should be fast
        let buildInfo = BuildInfo.current()
        let _ = promptManager.loadPrompts()
        let processManager = ProcessManager.shared
        let _ = processManager.checkForDuplicateProcesses()
        
        let endTime = CFAbsoluteTimeGetCurrent()
        let duration = endTime - startTime
        
        // These operations should complete quickly (under 1 second)
        XCTAssertLessThan(duration, 1.0, "Diagnostic operations should be fast")
        
        // Verify operations completed successfully
        XCTAssertNotNil(buildInfo)
    }
}
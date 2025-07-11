import XCTest
import Foundation
@testable import Potter

class ProcessManagerTests: TestBase {
    var tempDirectoryURL: URL!
    var originalCurrentDirectory: String!
    
    override func setUp() {
        super.setUp()
        
        // Save original directory
        originalCurrentDirectory = FileManager.default.currentDirectoryPath
        
        // Create temporary directory for tests
        tempDirectoryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("PotterProcessTests")
            .appendingPathComponent(UUID().uuidString)
        
        try! FileManager.default.createDirectory(at: tempDirectoryURL, withIntermediateDirectories: true)
        
        // Change to temp directory to use config/ subdirectory
        FileManager.default.changeCurrentDirectoryPath(tempDirectoryURL.path)
    }
    
    override func tearDown() {
        // Clean up any lock files
        ProcessManager.shared.removeLockFile()
        
        // Restore original directory
        FileManager.default.changeCurrentDirectoryPath(originalCurrentDirectory)
        
        // Clean up temp directory
        try? FileManager.default.removeItem(at: tempDirectoryURL)
        
        super.tearDown()
    }
    
    func testBuildInfoCreation() {
        let buildInfo = BuildInfo.current()
        
        XCTAssertFalse(buildInfo.buildId.isEmpty)
        // Build ID is now the same as build name, so test for build name format
        // Should contain a # followed by numbers (build number format)
        XCTAssertTrue(buildInfo.buildId.contains("#"), "buildId '\(buildInfo.buildId)' should contain '#'")
        // Should have at least 3 parts: adjective, noun, #number
        let parts = buildInfo.buildId.split(separator: " ")
        XCTAssertGreaterThanOrEqual(parts.count, 3, "buildId should have at least 3 parts (adjective noun #number)")
        
        // Version should come from Info.plist, not be hardcoded
        let expectedVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
        XCTAssertEqual(buildInfo.version, expectedVersion)
        
        XCTAssertFalse(buildInfo.buildDate.isEmpty)
        XCTAssertEqual(buildInfo.processId, getpid())
    }
    
    func testRunningPotterProcessStructure() {
        let buildInfo = BuildInfo.current()
        let process = RunningPotterProcess(
            pid: 12345,
            buildInfo: buildInfo,
            launchPath: "/test/path"
        )
        
        XCTAssertEqual(process.pid, 12345)
        XCTAssertEqual(process.buildInfo?.processId, buildInfo.processId)
        XCTAssertEqual(process.launchPath, "/test/path")
    }
    
    func testDuplicateProcessActionEnum() {
        let action1: DuplicateProcessAction = .killOthersAndContinue
        let action2: DuplicateProcessAction = .exitThisProcess
        
        switch action1 {
        case .killOthersAndContinue:
            XCTAssertTrue(true)
        case .exitThisProcess:
            XCTFail("Should be killOthersAndContinue")
        }
        
        switch action2 {
        case .killOthersAndContinue:
            XCTFail("Should be exitThisProcess")
        case .exitThisProcess:
            XCTAssertTrue(true)
        }
    }
    
}
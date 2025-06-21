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
        XCTAssertTrue(buildInfo.buildId.hasSuffix("-DEV"))
        XCTAssertEqual(buildInfo.version, "2.0.0-dev")
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
    
    func testCorruptedLockFileHandling() throws {
        let manager = ProcessManager.shared
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        try FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)
        
        let lockFile = configDir.appendingPathComponent("potter.lock")
        
        // Write corrupted JSON
        let corruptedData = "{ invalid json".data(using: .utf8)!
        try corruptedData.write(to: lockFile)
        
        // Should handle corrupted file gracefully
        let result = manager.checkForDuplicateProcesses()
        
        switch result {
        case .noDuplicates:
            XCTAssertTrue(true, "Should recover from corrupted lock file")
        case .foundDuplicates:
            XCTFail("Should not find duplicates with corrupted lock file")
        }
    }
}
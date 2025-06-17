import XCTest
import Foundation
@testable import Potter

class ProcessManagerTests: XCTestCase {
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
    
    func testCheckForDuplicateProcessesNoDuplicates() {
        let manager = ProcessManager.shared
        
        // Remove any existing lock file
        manager.removeLockFile()
        
        let result = manager.checkForDuplicateProcesses()
        
        switch result {
        case .noDuplicates:
            XCTAssertTrue(true, "Should detect no duplicates when no lock file exists")
        case .foundDuplicates:
            XCTFail("Should not find duplicates when no lock file exists")
        }
        
        // Should have created lock file
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        let lockFile = configDir.appendingPathComponent("potter.lock")
        XCTAssertTrue(FileManager.default.fileExists(atPath: lockFile.path))
    }
    
    func testCheckForDuplicateProcessesWithRunningProcess() throws {
        let manager = ProcessManager.shared
        
        // Create a lock file with current PID (simulating running process)
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        try FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)
        
        let lockFile = configDir.appendingPathComponent("potter.lock")
        let currentPid = getpid()
        
        let lockData = """
        {
            "buildId": "TEST-BUILD",
            "version": "1.0.0-test",
            "buildDate": "2025-01-01 12:00:00",
            "processId": \(currentPid),
            "timestamp": "2025-01-01T12:00:00Z"
        }
        """.data(using: .utf8)!
        
        try lockData.write(to: lockFile)
        
        let result = manager.checkForDuplicateProcesses()
        
        switch result {
        case .noDuplicates:
            XCTFail("Should find duplicate when lock file exists with running PID")
        case .foundDuplicates(let processes):
            XCTAssertEqual(processes.count, 1)
            XCTAssertEqual(processes[0].pid, currentPid)
            XCTAssertEqual(processes[0].buildInfo?.version, "1.0.0-test")
        }
    }
    
    func testCheckForDuplicateProcessesWithDeadProcess() throws {
        let manager = ProcessManager.shared
        
        // Create a lock file with a PID that doesn't exist
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        try FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)
        
        let lockFile = configDir.appendingPathComponent("potter.lock")
        let deadPid: Int32 = 99999 // Very unlikely to exist
        
        let lockData = """
        {
            "buildId": "TEST-BUILD",
            "version": "1.0.0-test",
            "buildDate": "2025-01-01 12:00:00",
            "processId": \(deadPid),
            "timestamp": "2025-01-01T12:00:00Z"
        }
        """.data(using: .utf8)!
        
        try lockData.write(to: lockFile)
        
        let result = manager.checkForDuplicateProcesses()
        
        switch result {
        case .noDuplicates:
            XCTAssertTrue(true, "Should detect no duplicates when lock file contains dead PID")
            // Should have removed old lock file and created new one
            XCTAssertTrue(FileManager.default.fileExists(atPath: lockFile.path))
        case .foundDuplicates:
            XCTFail("Should not find duplicates when PID is dead")
        }
    }
    
    func testLockFileCreationAndRemoval() {
        let manager = ProcessManager.shared
        let configDir = tempDirectoryURL.appendingPathComponent("config")
        let lockFile = configDir.appendingPathComponent("potter.lock")
        
        // Ensure no lock file exists
        manager.removeLockFile()
        XCTAssertFalse(FileManager.default.fileExists(atPath: lockFile.path))
        
        // Check for duplicates should create lock file
        _ = manager.checkForDuplicateProcesses()
        XCTAssertTrue(FileManager.default.fileExists(atPath: lockFile.path))
        
        // Remove lock file
        manager.removeLockFile()
        XCTAssertFalse(FileManager.default.fileExists(atPath: lockFile.path))
    }
    
    func testBuildInfoCreation() {
        let buildInfo = BuildInfo.current()
        
        XCTAssertFalse(buildInfo.buildId.isEmpty)
        XCTAssertTrue(buildInfo.buildId.hasSuffix("-DEV"))
        XCTAssertEqual(buildInfo.version, "1.0.0-dev")
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
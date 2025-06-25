import XCTest
import Foundation
@testable import Potter

@MainActor
class PermissionManagerTests: XCTestCase {
    var permissionManager: PermissionManager!
    
    override func setUp() async throws {
        try await super.setUp()
        permissionManager = PermissionManager.shared
    }
    
    override func tearDown() async throws {
        try await super.tearDown()
    }
    
    func testPermissionTypeEnum() {
        let allTypes = PermissionType.allCases
        XCTAssertEqual(allTypes.count, 1)
        XCTAssertTrue(allTypes.contains(.accessibility))
        
        // Test display names
        XCTAssertEqual(PermissionType.accessibility.displayName, "Accessibility")
        
        // Test raw values
        XCTAssertEqual(PermissionType.accessibility.rawValue, "accessibility")
    }
    
    
    func testSingletonPattern() {
        let manager1 = PermissionManager.shared
        let manager2 = PermissionManager.shared
        
        XCTAssertTrue(manager1 === manager2)
    }
    
    func testInitialPermissionStates() {
        // Initially should have some default states
        XCTAssertNotNil(permissionManager.accessibilityStatus)
        
        // Allow a small delay for any background permission checks to complete
        // This prevents test isolation issues when tests run in parallel
        let expectation = expectation(description: "Permission check completion")
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            XCTAssertFalse(self.permissionManager.isCheckingPermissions)
            expectation.fulfill()
        }
        
        waitForExpectations(timeout: 1.0)
    }
    
    func testCheckAllPermissions() {
        // This method should not crash
        permissionManager.checkAllPermissions()
        XCTAssertTrue(true)
    }
    
    func testGetPermissionStatus() {
        let accessibilityStatus = permissionManager.getPermissionStatus(for: .accessibility)
        
        // Should return valid status values
        let validStatuses: [PermissionStatus] = [.granted, .denied, .notDetermined, .unknown]
        XCTAssertTrue(validStatuses.contains(accessibilityStatus))
    }
    
    func testPermissionStatusUpdate() {
        let originalAccessibilityStatus = permissionManager.accessibilityStatus
        
        // Update accessibility status
        permissionManager.accessibilityStatus = .denied
        XCTAssertEqual(permissionManager.accessibilityStatus, .denied)
        
        
        // Restore original statuses
        permissionManager.accessibilityStatus = originalAccessibilityStatus
    }
    
    
    // Disabled: This test opens system settings which is disruptive during testing
    // func testOpenSystemSettingsDoesNotCrash() {
    //     // These methods should not crash even if they can't actually open settings
    //     permissionManager.openSystemSettings(for: .accessibility)
    //     
    //     XCTAssertTrue(true)
    // }
    
    func testPermissionTypeIdentifiable() {
        let accessibilityType = PermissionType.accessibility
        
        XCTAssertEqual(accessibilityType.rawValue, "accessibility")
    }
    
    func testPermissionStatusDisplayProperties() {
        let grantedStatus = PermissionStatus.granted
        let deniedStatus = PermissionStatus.denied
        
        XCTAssertEqual(grantedStatus.displayText, "Granted")
        XCTAssertEqual(deniedStatus.displayText, "Denied")
        XCTAssertFalse(grantedStatus.iconName.isEmpty)
        XCTAssertFalse(deniedStatus.iconName.isEmpty)
    }
    
    func testPermissionCheckingDoesNotCrash() {
        // checkAllPermissions should not crash (individual methods are private)
        permissionManager.checkAllPermissions()
        
        XCTAssertTrue(true)
    }
    
    func testObservableObjectConformance() {
        // Test that PermissionManager conforms to ObservableObject
        // This is mainly testing that the properties are correctly marked as @Published
        
        let expectation = expectation(description: "Permission status change observed")
        var fulfillCount = 0
        
        let cancellable = permissionManager.$accessibilityStatus.sink { newValue in
            if newValue == .denied && fulfillCount == 0 {
                fulfillCount += 1
                expectation.fulfill()
            }
        }
        
        permissionManager.accessibilityStatus = .denied
        
        waitForExpectations(timeout: 1.0)
        cancellable.cancel()
    }
    
    func testPermissionManagerPublishedProperties() {
        // Test that all expected properties are marked as @Published
        XCTAssertNotNil(permissionManager.$accessibilityStatus)
        XCTAssertNotNil(permissionManager.$isCheckingPermissions)
    }
    
    func testMultiplePermissionChecks() {
        // Multiple calls to check permissions should be safe
        permissionManager.checkAllPermissions()
        permissionManager.checkAllPermissions()
        permissionManager.checkAllPermissions()
        
        XCTAssertTrue(true)
    }
    
    func testPermissionTypeHashable() {
        let accessibilityType = PermissionType.accessibility
        
        let set: Set<PermissionType> = [accessibilityType, accessibilityType]
        XCTAssertEqual(set.count, 1) // Should be deduplicated
    }
    
    func testPermissionStatusHashable() {
        let grantedStatus = PermissionStatus.granted
        let deniedStatus = PermissionStatus.denied
        
        let set: Set<PermissionStatus> = [grantedStatus, deniedStatus, grantedStatus]
        XCTAssertEqual(set.count, 2) // Should be deduplicated
    }
}
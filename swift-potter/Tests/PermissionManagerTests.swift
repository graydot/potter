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
        XCTAssertEqual(allTypes.count, 2)
        XCTAssertTrue(allTypes.contains(.accessibility))
        XCTAssertTrue(allTypes.contains(.notifications))
        
        // Test display names
        XCTAssertEqual(PermissionType.accessibility.displayName, "Accessibility")
        XCTAssertEqual(PermissionType.notifications.displayName, "Notifications")
        
        // Test raw values
        XCTAssertEqual(PermissionType.accessibility.rawValue, "accessibility")
        XCTAssertEqual(PermissionType.notifications.rawValue, "notifications")
    }
    
    func testPermissionStatusEnum() {
        let statuses: [PermissionStatus] = [.granted, .denied, .notDetermined, .unknown]
        
        // Test display text
        XCTAssertEqual(PermissionStatus.granted.displayText, "Granted")
        XCTAssertEqual(PermissionStatus.denied.displayText, "Denied")
        XCTAssertEqual(PermissionStatus.notDetermined.displayText, "Not Determined")
        XCTAssertEqual(PermissionStatus.unknown.displayText, "Unknown")
        
        // Test that enum values exist
        let _: PermissionStatus = .granted
        let _: PermissionStatus = .denied
        let _: PermissionStatus = .notDetermined
        let _: PermissionStatus = .unknown
    }
    
    func testSingletonPattern() {
        let manager1 = PermissionManager.shared
        let manager2 = PermissionManager.shared
        
        XCTAssertTrue(manager1 === manager2)
    }
    
    func testInitialPermissionStates() {
        // Initially should have some default states
        XCTAssertNotNil(permissionManager.accessibilityStatus)
        XCTAssertNotNil(permissionManager.notificationsStatus)
        XCTAssertFalse(permissionManager.isCheckingPermissions)
    }
    
    func testCheckAllPermissions() {
        // This method should not crash
        permissionManager.checkAllPermissions()
        XCTAssertTrue(true)
    }
    
    func testGetPermissionStatus() {
        let accessibilityStatus = permissionManager.getPermissionStatus(for: .accessibility)
        let notificationsStatus = permissionManager.getPermissionStatus(for: .notifications)
        
        // Should return valid status values
        let validStatuses: [PermissionStatus] = [.granted, .denied, .notDetermined, .unknown]
        XCTAssertTrue(validStatuses.contains(accessibilityStatus))
        XCTAssertTrue(validStatuses.contains(notificationsStatus))
    }
    
    func testPermissionStatusUpdate() {
        let originalAccessibilityStatus = permissionManager.accessibilityStatus
        let originalNotificationsStatus = permissionManager.notificationsStatus
        
        // Update accessibility status
        permissionManager.accessibilityStatus = .denied
        XCTAssertEqual(permissionManager.accessibilityStatus, .denied)
        
        // Update notifications status  
        permissionManager.notificationsStatus = .granted
        XCTAssertEqual(permissionManager.notificationsStatus, .granted)
        
        // Restore original statuses
        permissionManager.accessibilityStatus = originalAccessibilityStatus
        permissionManager.notificationsStatus = originalNotificationsStatus
    }
    
    
    func testOpenSystemSettingsDoesNotCrash() {
        // These methods should not crash even if they can't actually open settings
        permissionManager.openSystemSettings(for: .accessibility)
        permissionManager.openSystemSettings(for: .notifications)
        
        XCTAssertTrue(true)
    }
    
    func testPermissionTypeIdentifiable() {
        let accessibilityType = PermissionType.accessibility
        let notificationsType = PermissionType.notifications
        
        XCTAssertEqual(accessibilityType.rawValue, "accessibility")
        XCTAssertEqual(notificationsType.rawValue, "notifications")
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
        
        let cancellable = permissionManager.$accessibilityStatus.sink { newValue in
            if newValue == .denied {
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
        XCTAssertNotNil(permissionManager.$notificationsStatus)
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
        let notificationsType = PermissionType.notifications
        
        let set: Set<PermissionType> = [accessibilityType, notificationsType, accessibilityType]
        XCTAssertEqual(set.count, 2) // Should be deduplicated
    }
    
    func testPermissionStatusHashable() {
        let grantedStatus = PermissionStatus.granted
        let deniedStatus = PermissionStatus.denied
        
        let set: Set<PermissionStatus> = [grantedStatus, deniedStatus, grantedStatus]
        XCTAssertEqual(set.count, 2) // Should be deduplicated
    }
}
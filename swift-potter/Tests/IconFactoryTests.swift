import XCTest
import AppKit
@testable import Potter

class IconFactoryTests: TestBase {

    // MARK: - Icon Creation Tests

    func testCreateNormalIcon() {
        let icon = IconFactory.createIcon(for: .normal)
        XCTAssertNotNil(icon, "Normal icon should not be nil")
    }

    func testCreateProcessingIcons() {
        let frames = IconFactory.createSpinnerFrames()
        XCTAssertGreaterThanOrEqual(frames.count, 8, "Spinner should have at least 8 frames")
        for frame in frames {
            XCTAssertNotNil(frame, "Each spinner frame should be a valid NSImage")
        }
    }

    func testCreateSuccessIcon() {
        let icon = IconFactory.createIcon(for: .success)
        XCTAssertNotNil(icon, "Success icon should not be nil")
    }

    func testCreateErrorIcon() {
        let icon = IconFactory.createIcon(for: .error)
        XCTAssertNotNil(icon, "Error icon should not be nil")
    }

    func testIconSize() {
        let states: [MenuBarIconState] = [.normal, .success, .error]
        for state in states {
            let icon = IconFactory.createIcon(for: state)
            XCTAssertEqual(icon.size.width, 18, "Icon width should be 18 for state \(state)")
            XCTAssertEqual(icon.size.height, 18, "Icon height should be 18 for state \(state)")
        }

        let spinnerFrames = IconFactory.createSpinnerFrames()
        for (index, frame) in spinnerFrames.enumerated() {
            XCTAssertEqual(frame.size.width, 18, "Spinner frame \(index) width should be 18")
            XCTAssertEqual(frame.size.height, 18, "Spinner frame \(index) height should be 18")
        }
    }

    func testSpinnerFrameCount() {
        let frames = IconFactory.createSpinnerFrames()
        XCTAssertEqual(frames.count, 8, "Spinner should have exactly 8 frames")
    }
}

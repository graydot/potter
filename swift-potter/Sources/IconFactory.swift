import AppKit
import Foundation

// MARK: - MenuBarIconState

enum MenuBarIconState {
    case normal
    case processing
    case success
    case error
}

// MARK: - IconFactory

/// Creates menu bar icons for different states.
/// Extracted from MenuBarManager to separate icon drawing concerns.
struct IconFactory {

    private static let iconSize = NSSize(width: 18, height: 18)

    // MARK: - Public API

    /// Create an icon for the given menu bar state.
    static func createIcon(for state: MenuBarIconState) -> NSImage {
        switch state {
        case .normal:
            return createMenuBarIcon()
        case .processing:
            // For a static processing icon, return the first spinner frame
            return createSpinnerFrame(rotation: 0)
        case .success:
            return createTintedIcon(color: NSColor.systemGreen)
        case .error:
            return createTintedIcon(color: NSColor.systemRed)
        }
    }

    /// Create all spinner animation frames (one per segment position).
    static func createSpinnerFrames() -> [NSImage] {
        return (0..<8).map { i in
            let rotation = CGFloat(i) * 45.0 // 360 / 8 = 45 degrees per frame
            return createSpinnerFrame(rotation: rotation)
        }
    }

    /// Create a spinner icon at a specific rotation angle (degrees).
    static func createSpinnerFrame(rotation degrees: CGFloat) -> NSImage {
        let image = NSImage(size: iconSize)
        image.lockFocus()

        let context = NSGraphicsContext.current?.cgContext
        context?.saveGState()

        let center = NSPoint(x: iconSize.width / 2, y: iconSize.height / 2)
        context?.translateBy(x: center.x, y: center.y)
        context?.rotate(by: -degrees * .pi / 180)
        context?.translateBy(x: -center.x, y: -center.y)

        drawSpinner()

        context?.restoreGState()

        image.unlockFocus()
        return image
    }

    // MARK: - Private Drawing Methods

    private static func createMenuBarIcon() -> NSImage {
        guard let templateIcon = Bundle.potterResources.image(forResource: "menubar-icon-template") else {
            fatalError("menubar-icon-template.png not found in Resources")
        }

        let icon = templateIcon.copy() as! NSImage
        icon.size = iconSize
        icon.isTemplate = true
        return icon
    }

    private static func createTintedIcon(color: NSColor) -> NSImage {
        guard let templateIcon = Bundle.potterResources.image(forResource: "menubar-icon-template") else {
            fatalError("menubar-icon-template.png not found in Resources")
        }

        let tintedIcon = NSImage(size: iconSize)
        tintedIcon.lockFocus()

        // Fill with the color
        color.set()
        NSRect(origin: .zero, size: iconSize).fill()

        // Use the original icon as a mask
        templateIcon.draw(
            in: NSRect(origin: .zero, size: iconSize),
            from: NSRect(origin: .zero, size: templateIcon.size),
            operation: .destinationIn,
            fraction: 1.0
        )

        tintedIcon.unlockFocus()
        return tintedIcon
    }

    private static func drawSpinner() {
        let center = NSPoint(x: 9, y: 9)
        let radius: CGFloat = 6
        let lineWidth: CGFloat = 2

        // Draw spinner segments with varying opacity
        for i in 0..<8 {
            let angle = Double(i) * .pi / 4
            let startPoint = NSPoint(
                x: center.x + CGFloat(cos(angle)) * (radius - lineWidth),
                y: center.y + CGFloat(sin(angle)) * (radius - lineWidth)
            )
            let endPoint = NSPoint(
                x: center.x + CGFloat(cos(angle)) * radius,
                y: center.y + CGFloat(sin(angle)) * radius
            )

            let opacity = 0.2 + (0.8 * Double(7 - i) / 7.0)
            NSColor.white.withAlphaComponent(opacity).setStroke()

            let path = NSBezierPath()
            path.move(to: startPoint)
            path.line(to: endPoint)
            path.lineWidth = lineWidth
            path.stroke()
        }
    }
}

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
        let icon = NSImage(size: iconSize)
        icon.lockFocus()
        drawWandIcon(color: .black)
        icon.unlockFocus()
        icon.isTemplate = true
        return icon
    }

    private static func createTintedIcon(color: NSColor) -> NSImage {
        let tintedIcon = NSImage(size: iconSize)
        tintedIcon.lockFocus()
        drawWandIcon(color: color)
        tintedIcon.unlockFocus()
        return tintedIcon
    }

    /// Draws a magic wand with sparkles — clean and readable at 18px.
    private static func drawWandIcon(color: NSColor) {
        color.setStroke()
        color.setFill()

        // Wand: diagonal line from bottom-left to upper-right
        let wand = NSBezierPath()
        wand.move(to: NSPoint(x: 3, y: 3))
        wand.line(to: NSPoint(x: 12, y: 12))
        wand.lineWidth = 2.0
        wand.lineCapStyle = .round
        wand.stroke()

        // Wand tip (small diamond)
        let tip = NSBezierPath()
        tip.move(to: NSPoint(x: 12, y: 13.5))
        tip.line(to: NSPoint(x: 13.5, y: 12))
        tip.line(to: NSPoint(x: 12, y: 10.5))
        tip.line(to: NSPoint(x: 10.5, y: 12))
        tip.close()
        tip.fill()

        // Sparkle 1 (top-right, larger)
        drawSparkle(center: NSPoint(x: 15, y: 15), size: 2.5, color: color)

        // Sparkle 2 (right of wand)
        drawSparkle(center: NSPoint(x: 16, y: 9), size: 1.5, color: color)

        // Sparkle 3 (above wand)
        drawSparkle(center: NSPoint(x: 8, y: 16), size: 1.5, color: color)
    }

    /// Draws a 4-point star sparkle.
    private static func drawSparkle(center: NSPoint, size: CGFloat, color: NSColor) {
        color.setFill()
        let sparkle = NSBezierPath()
        sparkle.move(to: NSPoint(x: center.x, y: center.y + size))
        sparkle.line(to: NSPoint(x: center.x + size * 0.3, y: center.y + size * 0.3))
        sparkle.line(to: NSPoint(x: center.x + size, y: center.y))
        sparkle.line(to: NSPoint(x: center.x + size * 0.3, y: center.y - size * 0.3))
        sparkle.line(to: NSPoint(x: center.x, y: center.y - size))
        sparkle.line(to: NSPoint(x: center.x - size * 0.3, y: center.y - size * 0.3))
        sparkle.line(to: NSPoint(x: center.x - size, y: center.y))
        sparkle.line(to: NSPoint(x: center.x - size * 0.3, y: center.y + size * 0.3))
        sparkle.close()
        sparkle.fill()
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

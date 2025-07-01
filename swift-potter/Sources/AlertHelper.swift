import AppKit
import Foundation

extension NSAlert {
    /// Apply the Potter icon to this alert
    func applyPotterIcon() {
        if let iconURL = Bundle.potterResources.url(forResource: "potter-alert-icon", withExtension: "png", subdirectory: "Resources/AppIcon"),
           let alertIcon = NSImage(contentsOf: iconURL) {
            self.icon = alertIcon
        }
    }
    
    /// Create a Potter-branded alert with custom icon
    static func potterAlert(title: String, message: String, buttons: [String] = ["OK"]) -> NSAlert {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        
        for buttonTitle in buttons {
            alert.addButton(withTitle: buttonTitle)
        }
        
        alert.applyPotterIcon()
        return alert
    }
}
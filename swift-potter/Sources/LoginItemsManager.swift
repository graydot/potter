import Foundation
import ServiceManagement
import AppKit

class LoginItemsManager: ObservableObject {
    static let shared = LoginItemsManager()
    
    @Published var isEnabled: Bool = false
    
    private init() {
        checkCurrentStatus()
    }
    
    func checkCurrentStatus() {
        let service = SMAppService.mainApp
        isEnabled = service.status == .enabled
        PotterLogger.shared.debug("login_items", "📋 Login items status checked: \(isEnabled)")
    }
    
    func toggle() {
        if isEnabled {
            disable()
        } else {
            enable()
        }
    }
    
    func enable() {
        let service = SMAppService.mainApp
        do {
            try service.register()
            isEnabled = true
            PotterLogger.shared.info("login_items", "✅ Successfully enabled start at login")
        } catch {
            PotterLogger.shared.error("login_items", "❌ Failed to enable start at login: \(error.localizedDescription)")
            showError("Failed to enable start at login: \(error.localizedDescription)")
        }
    }
    
    func disable() {
        let service = SMAppService.mainApp
        do {
            try service.unregister()
            isEnabled = false
            PotterLogger.shared.info("login_items", "✅ Successfully disabled start at login")
        } catch {
            PotterLogger.shared.error("login_items", "❌ Failed to disable start at login: \(error.localizedDescription)")
            showError("Failed to disable start at login: \(error.localizedDescription)")
        }
    }
    
    private func showError(_ message: String) {
        DispatchQueue.main.async {
            let alert = NSAlert()
            alert.messageText = "Login Items Error"
            alert.informativeText = message
            alert.addButton(withTitle: "OK")
            alert.addButton(withTitle: "Open System Settings")
            
            // Add custom Potter icon
            if let iconURL = Bundle.module.url(forResource: "potter-alert-icon", withExtension: "png", subdirectory: "Resources/AppIcon"),
               let alertIcon = NSImage(contentsOf: iconURL) {
                alert.icon = alertIcon
            }
            
            let response = alert.runModal()
            if response == .alertSecondButtonReturn {
                self.openSystemSettingsLoginItems()
            }
        }
    }
    
    func openSystemSettingsLoginItems() {
        // Open the System Settings app to Login Items
        if let url = URL(string: "x-apple.systempreferences:com.apple.LoginItems-Settings.extension") {
            NSWorkspace.shared.open(url)
        }
    }
}
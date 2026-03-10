import AppKit

enum SettingsHelpers {
    static func notifyMenuUpdate() {
        Task { @MainActor in
            if let appDelegate = NSApplication.shared.delegate as? AppDelegate {
                appDelegate.menuBarManager?.updateMenu()
            }
        }
    }

    static func showErrorAlert(message: String) {
        let alert = NSAlert()
        alert.messageText = "Error"
        alert.informativeText = message
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }

    static func initializeFreshState(promptService: PromptService, settings: PotterSettings) {
        promptService.resetToDefaults()

        let bundleId = Bundle.main.bundleIdentifier ?? "com.graydot.potter"
        UserDefaults.standard.removePersistentDomain(forName: bundleId)
        UserDefaults.standard.synchronize()

        switch StorageAdapter.shared.clearAllAPIKeys() {
        case .success:
            break
        case .failure(let error):
            PotterLogger.shared.error("settings", "❌ Failed to clear API keys: \(error.localizedDescription)")
        }

        settings.resetToDefaults()

        UserDefaults.standard.set(HotkeyConstants.defaultHotkey, forKey: HotkeyConstants.userDefaultsKey)

        if let appDelegate = NSApplication.shared.delegate as? AppDelegate {
            Task { @MainActor in
                appDelegate.potterCore?.updateHotkey(HotkeyConstants.defaultHotkey)
            }
        }
    }
}

import AppKit
import Foundation

// MARK: - MenuBuilder

/// Builds NSMenu instances for the menu bar.
/// Extracted from MenuBarManager to separate menu construction concerns.
struct MenuBuilder {

    /// Build the complete menu bar menu.
    ///
    /// - Parameters:
    ///   - prompts: List of available prompt names
    ///   - currentPrompt: The currently selected prompt name
    ///   - hotkeyDisplay: The hotkey string to display (e.g. "⌘⇧9")
    ///   - target: The target for menu item actions
    ///   - promptAction: Selector called when a prompt is selected
    ///   - settingsAction: Selector called when Preferences is selected
    /// - Returns: A fully constructed NSMenu
    static func buildMenu(
        prompts: [String],
        currentPrompt: String,
        hotkeyDisplay: String,
        target: AnyObject,
        promptAction: Selector,
        settingsAction: Selector
    ) -> NSMenu {
        let menu = NSMenu()

        // Process Text item
        let processTitle = "Process Text (\(hotkeyDisplay))"
        let processItem = NSMenuItem(title: processTitle, action: nil, keyEquivalent: "")
        processItem.target = target
        menu.addItem(processItem)

        menu.addItem(NSMenuItem.separator())

        // Prompts section
        addPrompts(to: menu, prompts: prompts, currentPrompt: currentPrompt, target: target, action: promptAction)

        menu.addItem(NSMenuItem.separator())

        // Preferences
        let preferencesItem = NSMenuItem(title: "Preferences...", action: settingsAction, keyEquivalent: "")
        preferencesItem.target = target
        menu.addItem(preferencesItem)

        // Quit
        let quitItem = NSMenuItem(title: "Quit Potter", action: nil, keyEquivalent: "")
        quitItem.target = target
        menu.addItem(quitItem)

        return menu
    }

    // MARK: - Private

    private static func addPrompts(
        to menu: NSMenu,
        prompts: [String],
        currentPrompt: String,
        target: AnyObject,
        action: Selector
    ) {
        guard !prompts.isEmpty else {
            let noPromptsItem = NSMenuItem(title: "No prompts available", action: nil, keyEquivalent: "")
            noPromptsItem.isEnabled = false
            menu.addItem(noPromptsItem)
            return
        }

        for promptName in prompts {
            let menuItem = NSMenuItem(title: promptName, action: action, keyEquivalent: "")
            menuItem.target = target
            menuItem.representedObject = promptName

            if promptName == currentPrompt {
                menuItem.state = .on
            }

            menu.addItem(menuItem)
        }
    }
}

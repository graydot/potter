import SwiftUI
import AppKit

@available(macOS 14.0, *)
struct HotkeyConfigurationView: View {
    @State private var isCapturingHotkey = false
    @State private var capturedKeys: [String] = []
    @State private var currentHotkey = HotkeyConstants.defaultHotkey
    @State private var previousHotkey = HotkeyConstants.defaultHotkey
    @State private var warningMessage = ""
    @FocusState private var isKeyCaptureFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Global Hotkey:")
                    .fontWeight(.medium)

                HStack(spacing: 6) {
                    if isCapturingHotkey {
                        ForEach(capturedKeys.indices, id: \.self) { index in
                            hotkeyPill(capturedKeys[index], isActive: true)
                        }

                        if capturedKeys.isEmpty {
                            hotkeyPill("?", isActive: false)
                        }
                    } else {
                        ForEach(currentHotkey.indices, id: \.self) { index in
                            hotkeyPill(currentHotkey[index], isActive: false)
                                .onTapGesture {
                                    startHotkeyCapture()
                                }
                        }
                    }
                }

                Spacer()

                Button("Reset") {
                    resetToDefault()
                }
                .buttonStyle(.bordered)
                .disabled(isCapturingHotkey)
            }

            if !warningMessage.isEmpty {
                Text(warningMessage)
                    .foregroundColor(.orange)
                    .font(.caption)
                    .fontWeight(.medium)
            }

            if isCapturingHotkey {
                Text("Press your desired key combination (modifier + key) or ESC to cancel")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }
        }
        .background(
            TextField("", text: .constant(""))
                .opacity(0)
                .focused($isKeyCaptureFocused)
                .onKeyPress { keyPress in
                    if isCapturingHotkey {
                        return handleKeyPress(keyPress)
                    }
                    return .ignored
                }
        )
        .onAppear {
            loadSavedHotkey()
        }
    }

    // MARK: - Hotkey Pill

    private func hotkeyPill(_ text: String, isActive: Bool, isDisabled: Bool = false) -> some View {
        Text(text)
            .font(.system(.body, design: .monospaced))
            .fontWeight(.medium)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(
                        isActive ? Color.accentColor :
                        isDisabled ? Color.secondary.opacity(0.1) :
                        Color.secondary.opacity(0.2)
                    )
            )
            .foregroundColor(
                isActive ? .white :
                isDisabled ? .secondary :
                .primary
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(
                        isActive ? Color.accentColor :
                        isDisabled ? Color.secondary.opacity(0.2) :
                        Color.secondary.opacity(0.4),
                        lineWidth: 1
                    )
            )
    }

    // MARK: - Key Handling

    private func loadSavedHotkey() {
        if let savedHotkey = UserDefaults.standard.array(forKey: UserDefaultsKeys.globalHotkey) as? [String] {
            currentHotkey = savedHotkey
            previousHotkey = savedHotkey
            PotterLogger.shared.debug("settings", "🎹 Loaded saved hotkey: \(savedHotkey.joined(separator: "+"))")
        }
    }

    private func getBaseCharacter(from character: Character) -> String {
        let shiftedCharacterMap: [Character: String] = [
            "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
            "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
            "_": "-", "+": "=", "{": "[", "}": "]", "|": "\\",
            ":": ";", "\"": "'", "<": ",", ">": ".", "?": "/",
            "~": "`"
        ]

        if let baseChar = shiftedCharacterMap[character] {
            return baseChar
        }

        return String(character).uppercased()
    }

    private func startHotkeyCapture() {
        previousHotkey = currentHotkey
        isCapturingHotkey = true
        capturedKeys.removeAll()
        warningMessage = ""
        isKeyCaptureFocused = true

        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore?.disableGlobalHotkey()
        }

        PotterLogger.shared.debug("settings", "🎹 Started hotkey capture mode")
    }

    private func handleKeyPress(_ keyPress: KeyPress) -> KeyPress.Result {
        let key = keyPress.key

        if key == .escape {
            cancelHotkeyCapture()
            return .handled
        }

        capturedKeys.removeAll()

        if keyPress.modifiers.contains(.command) {
            capturedKeys.append("⌘")
        }
        if keyPress.modifiers.contains(.shift) {
            capturedKeys.append("⇧")
        }
        if keyPress.modifiers.contains(.option) {
            capturedKeys.append("⌥")
        }
        if keyPress.modifiers.contains(.control) {
            capturedKeys.append("⌃")
        }

        var regularKey = ""
        switch key {
        case KeyEquivalent.space:
            regularKey = "Space"
        case KeyEquivalent.tab:
            regularKey = "Tab"
        case KeyEquivalent.return:
            regularKey = "Return"
        case KeyEquivalent.delete:
            regularKey = "Delete"
        case KeyEquivalent.upArrow:
            regularKey = "↑"
        case KeyEquivalent.downArrow:
            regularKey = "↓"
        case KeyEquivalent.leftArrow:
            regularKey = "←"
        case KeyEquivalent.rightArrow:
            regularKey = "→"
        default:
            let char = key.character
            regularKey = getBaseCharacter(from: char)
        }

        if !regularKey.isEmpty && !["⌘", "⇧", "⌥", "⌃"].contains(regularKey) {
            capturedKeys.append(regularKey)
        }

        validateKeyCombo()

        return .handled
    }

    private func validateKeyCombo() {
        let modifiers = capturedKeys.filter { HotkeyKeyMapping.modifierSymbols.contains($0) }
        let regularKeys = capturedKeys.filter { !HotkeyKeyMapping.modifierSymbols.contains($0) }

        if modifiers.isEmpty || regularKeys.isEmpty {
            warningMessage = "Need at least one modifier (⌘⇧⌥⌃) and one key"
        } else {
            let conflictMessage = checkForShortcutConflicts(capturedKeys)
            if !conflictMessage.isEmpty {
                warningMessage = conflictMessage
            } else {
                warningMessage = ""
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
                    if isCapturingHotkey && !capturedKeys.isEmpty {
                        applyNewHotkey()
                    }
                }
            }
        }
    }

    private func checkForShortcutConflicts(_ keys: [String]) -> String {
        let combo = keys.joined(separator: "+")

        let systemShortcuts: [String: String] = [
            "⌘+Q": "Quit Application",
            "⌘+W": "Close Window",
            "⌘+N": "New Window",
            "⌘+T": "New Tab",
            "⌘+S": "Save",
            "⌘+O": "Open",
            "⌘+P": "Print",
            "⌘+Z": "Undo",
            "⌘+⇧+Z": "Redo",
            "⌘+C": "Copy",
            "⌘+V": "Paste",
            "⌘+X": "Cut",
            "⌘+A": "Select All",
            "⌘+F": "Find",
            "⌘+G": "Find Next",
            "⌘+H": "Hide Application",
            "⌘+M": "Minimize Window",
            "⌘+R": "Refresh/Reload",
            "⌘+,": "Preferences",
            "⌘+Space": "Spotlight Search",
            "⌘+Tab": "Application Switcher",
            "⌘+⇧+3": "Screenshot",
            "⌘+⇧+4": "Screenshot Selection",
            "⌘+⇧+5": "Screenshot Options",
            "⌘+⌃+Space": "Emoji Picker",
            "⌘+⇧+A": "Applications Folder",
            "⌘+⇧+U": "Utilities Folder",
            "⌘+⇧+H": "Home Folder",
            "⌘+⇧+D": "Desktop Folder",
            "⌘+⇧+O": "Documents Folder",
            "⌘+⇧+G": "Go to Folder",
            "⌘+⇧+Delete": "Empty Trash",
            "⌘+⌥+ESC": "Force Quit Applications"
        ]

        if let conflictName = systemShortcuts[combo] {
            return "⚠️ Conflicts with system shortcut: \(conflictName)"
        }

        let commonAppShortcuts: [String: String] = [
            "⌘+⇧+I": "Inspector/DevTools",
            "⌘+⇧+C": "Color Picker",
            "⌘+⇧+L": "Location/Library",
            "⌘+⇧+K": "Clear/Clean",
            "⌘+⇧+E": "Export",
            "⌘+⇧+P": "Private/Incognito",
            "⌘+⌥+I": "Developer Tools"
        ]

        if let conflictName = commonAppShortcuts[combo] {
            return "⚠️ May conflict with app shortcut: \(conflictName)"
        }

        return ""
    }

    private func applyNewHotkey() {
        currentHotkey = capturedKeys
        isCapturingHotkey = false
        isKeyCaptureFocused = false
        warningMessage = ""

        UserDefaults.standard.set(currentHotkey, forKey: UserDefaultsKeys.globalHotkey)

        PotterLogger.shared.info("settings", "🎹 Applied new hotkey: \(currentHotkey.joined(separator: "+"))")

        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore?.updateHotkey(currentHotkey)
        }
    }

    private func cancelHotkeyCapture() {
        currentHotkey = previousHotkey
        isCapturingHotkey = false
        isKeyCaptureFocused = false
        capturedKeys.removeAll()
        warningMessage = ""

        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore?.enableGlobalHotkey()
        }

        PotterLogger.shared.debug("settings", "🎹 Cancelled hotkey capture - restored previous combo")
    }

    private func resetToDefault() {
        currentHotkey = HotkeyConstants.defaultHotkey
        previousHotkey = HotkeyConstants.defaultHotkey
        warningMessage = ""
        capturedKeys.removeAll()
        isCapturingHotkey = false
        isKeyCaptureFocused = false

        UserDefaults.standard.set(currentHotkey, forKey: UserDefaultsKeys.globalHotkey)

        PotterLogger.shared.info("settings", "🎹 Reset hotkey to default: \(currentHotkey.joined(separator: "+"))")

        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore?.updateHotkey(currentHotkey)
        }
    }
}

import Foundation
import AppKit
import Carbon

// MARK: - Hotkey Constants
struct HotkeyConstants {
    static let defaultHotkey: [String] = ["⌘", "⇧", "9"]
    static let userDefaultsKey = "global_hotkey"
}

// Protocol for menu bar icon updates
protocol IconStateDelegate: AnyObject {
    func setProcessingState()
    func setSuccessState()
    func setNormalState()
    func setErrorState(message: String)
}

enum PromptMode: String, CaseIterable {
    case summarize = "summarize"
    case formal = "formal"
    case casual = "casual"
    
    var prompt: String {
        switch self {
        case .summarize:
            return "Please provide a concise summary of the following text."
        case .formal:
            return "Please rewrite the following text in a formal, professional tone."
        case .casual:
            return "Please rewrite the following text in a casual, relaxed tone."
        }
    }
    
    var displayName: String {
        switch self {
        case .summarize: return "Summarize"
        case .formal: return "Make Formal"
        case .casual: return "Make Casual"
        }
    }
}

class PotterCore {
    private var currentMode: PromptMode = .formal
    private var settings: PotterSettings
    private var llmManager: LLMManager?
    private var hotkeyEventHandler: EventHotKeyRef?
    private var currentHotkeyCombo: [String] = HotkeyConstants.defaultHotkey
    
    // Icon state delegate
    weak var iconDelegate: IconStateDelegate?
    
    init() {
        self.settings = PotterSettings()
    }
    
    func setup() {
        PotterLogger.shared.info("core", "🚀 Starting Potter Core...")
        
        // Initialize LLM manager on main actor
        Task { @MainActor in
            self.llmManager = LLMManager()
        }
        
        setupGlobalHotkey()
        PotterLogger.shared.info("core", "✅ Potter Core initialized")
    }
    
    private func setupGlobalHotkey() {
        // Load saved hotkey or use default
        if let savedHotkey = UserDefaults.standard.array(forKey: HotkeyConstants.userDefaultsKey) as? [String] {
            currentHotkeyCombo = savedHotkey
        }
        
        // Install event handler for hotkey events
        var eventTypes = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        InstallEventHandler(
            GetApplicationEventTarget(),
            { (nextHandler, theEvent, userData) -> OSStatus in
                let potter = Unmanaged<PotterCore>.fromOpaque(userData!).takeUnretainedValue()
                potter.handleHotkey()
                return noErr
            },
            1,
            &eventTypes,
            Unmanaged.passUnretained(self).toOpaque(),
            nil
        )
        
        // Register the current hotkey
        registerHotkey(currentHotkeyCombo)
    }
    
    @objc private func handleHotkey() {
        PotterLogger.shared.info("hotkey", "🎯 Global hotkey callback triggered")
        DispatchQueue.main.async {
            self.processClipboardText()
        }
    }
    
    func processClipboardText() {
        PotterLogger.shared.info("text_processor", "🔄 Processing clipboard text...")
        
        // Check on main actor
        Task { @MainActor in
            guard let llmManager = self.llmManager, llmManager.hasValidProvider() else {
                PotterLogger.shared.error("text_processor", "❌ No valid LLM provider configured")
                // Configuration error handled by icon state
                self.iconDelegate?.setErrorState(message: "No API key configured")
                return
            }
            
            self.performTextProcessing(with: llmManager)
        }
    }
    
    @MainActor
    private func performTextProcessing(with llmManager: LLMManager) {
        // Get clipboard text
        let pasteboard = NSPasteboard.general
        guard let text = pasteboard.string(forType: .string), !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            PotterLogger.shared.warning("text_processor", "⚠️ No text found in clipboard")
            // Put helpful message in clipboard instead of showing alert
            pasteboard.clearContents()
            pasteboard.setString("No text was in clipboard", forType: .string)
            // No text in clipboard handled by icon state
            iconDelegate?.setErrorState(message: "No text in clipboard")
            return
        }
        
        // Check if the clipboard contains our own "no text" message and ignore it
        let trimmedText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedText == "No text was in clipboard" {
            PotterLogger.shared.warning("text_processor", "⚠️ Ignoring our own 'no text' message")
            // Still no text handled by icon state
            iconDelegate?.setErrorState(message: "Still no text in clipboard")
            return
        }
        
        PotterLogger.shared.info("text_processor", "📝 Processing \(trimmedText.count) characters")
        // Processing state handled by spinner icon
        
        // Update menu bar icon to show processing state
        iconDelegate?.setProcessingState()
        
        // Process with LLM
        Task {
            do {
                // Get current prompt from UserDefaults and prompt manager
                let currentPromptName = UserDefaults.standard.string(forKey: "current_prompt") ?? "summarize"
                let selectedPrompt = PromptService.shared.getPrompt(named: currentPromptName)
                let promptText = selectedPrompt?.prompt ?? currentMode.prompt
                
                PotterLogger.shared.info("text_processor", "🤖 Using prompt: \(currentPromptName)")
                PotterLogger.shared.info("text_processor", "📝 Text being sent to LLM:")
                PotterLogger.shared.info("text_processor", "||||| \(trimmedText) |||||")
                PotterLogger.shared.info("text_processor", "🔄 Calling LLM API...")
                
                let processedText = try await llmManager.processText(trimmedText, prompt: promptText)
                
                PotterLogger.shared.info("text_processor", "✅ LLM processing complete")
                PotterLogger.shared.info("text_processor", "📝 Text returned from LLM:")
                PotterLogger.shared.info("text_processor", "||||| \(processedText) |||||")
                PotterLogger.shared.info("text_processor", "📋 Result copied to clipboard (\(processedText.count) characters)")
                
                await MainActor.run {
                    // Put result back in clipboard
                    pasteboard.clearContents()
                    pasteboard.setString(processedText, forType: .string)
                    
                    // Update menu bar icon to show success state
                    self.iconDelegate?.setSuccessState()
                    
                    // Success state handled by icon
                }
            } catch {
                let potterError: PotterError
                if let existingPotterError = error as? PotterError {
                    potterError = existingPotterError
                } else {
                    // Convert unknown errors to system errors
                    potterError = PotterError.system(.systemCallFailed(call: "text_processing", errno: 0))
                }
                
                await MainActor.run {
                    GlobalErrorHandler.handle(potterError, context: "text_processing", showUser: false)
                    
                    // Set error state with user-friendly message
                    self.iconDelegate?.setErrorState(message: potterError.localizedDescription)
                    
                    // Error state handled by icon
                }
            }
        }
    }
    
    func setPromptMode(_ mode: PromptMode) {
        currentMode = mode
        PotterLogger.shared.info("core", "🎯 Mode changed to: \(mode.displayName)")
        // Mode change logged only
    }
    
    func getLLMManager() -> LLMManager? {
        return llmManager
    }
    
    // MARK: - Hotkey Management
    func updateHotkey(_ newHotkey: [String]) {
        // Unregister current hotkey
        if let currentHandler = hotkeyEventHandler {
            UnregisterEventHotKey(currentHandler)
            hotkeyEventHandler = nil
        }
        
        currentHotkeyCombo = newHotkey
        
        // Register new hotkey
        registerHotkey(newHotkey)
        
        // Save to settings
        UserDefaults.standard.set(newHotkey, forKey: HotkeyConstants.userDefaultsKey)
        PotterLogger.shared.info("hotkeys", "🔄 Updated hotkey to: \(newHotkey.joined(separator: "+"))")
        
        // Notify icon delegate to update menu with new hotkey
        DispatchQueue.main.async {
            if let appDelegate = NSApplication.shared.delegate as? IconStateDelegate {
                // Force menu update through AppDelegate
                if let mainAppDelegate = appDelegate as? AppDelegate {
                    Task { @MainActor in
                        mainAppDelegate.updateMenuForHotkeyChange()
                    }
                }
            }
        }
    }
    
    func disableGlobalHotkey() {
        if let currentHandler = hotkeyEventHandler {
            UnregisterEventHotKey(currentHandler)
            hotkeyEventHandler = nil
            PotterLogger.shared.debug("hotkeys", "⏸️ Temporarily disabled global hotkey")
        }
    }
    
    func enableGlobalHotkey() {
        // Only re-register if we don't already have a handler
        if hotkeyEventHandler == nil {
            registerHotkey(currentHotkeyCombo)
            PotterLogger.shared.debug("hotkeys", "▶️ Re-enabled global hotkey")
        }
    }
    
    private func registerHotkey(_ hotkeyCombo: [String]) {
        // Parse the hotkey combination
        let (keyCode, modifiers) = parseHotkeyCombo(hotkeyCombo)
        
        var eventHotKeyRef: EventHotKeyRef?
        let hotKeyID = EventHotKeyID(signature: fourCharCode("POTR"), id: UInt32(1))
        
        let status = RegisterEventHotKey(
            keyCode,
            modifiers,
            hotKeyID,
            GetApplicationEventTarget(),
            0,
            &eventHotKeyRef
        )
        
        if status == noErr {
            self.hotkeyEventHandler = eventHotKeyRef
            PotterLogger.shared.info("hotkeys", "✅ Registered hotkey: \(hotkeyCombo.joined(separator: "+"))")
        } else {
            PotterLogger.shared.error("hotkeys", "❌ Failed to register hotkey: \(hotkeyCombo.joined(separator: "+"))")
        }
    }
    
    private func parseHotkeyCombo(_ combo: [String]) -> (UInt32, UInt32) {
        var modifiers: UInt32 = 0
        var keyCode: UInt32 = UInt32(kVK_ANSI_9) // Default to 9
        
        for key in combo {
            switch key {
            case "⌘":
                modifiers |= UInt32(cmdKey)
            case "⌥":
                modifiers |= UInt32(optionKey)
            case "⌃":
                modifiers |= UInt32(controlKey)
            case "⇧":
                modifiers |= UInt32(shiftKey)
            case "R":
                keyCode = UInt32(kVK_ANSI_R)
            case "T":
                keyCode = UInt32(kVK_ANSI_T)
            case "Y":
                keyCode = UInt32(kVK_ANSI_Y)
            case "U":
                keyCode = UInt32(kVK_ANSI_U)
            case "I":
                keyCode = UInt32(kVK_ANSI_I)
            case "O":
                keyCode = UInt32(kVK_ANSI_O)
            case "P":
                keyCode = UInt32(kVK_ANSI_P)
            case "A":
                keyCode = UInt32(kVK_ANSI_A)
            case "S":
                keyCode = UInt32(kVK_ANSI_S)
            case "D":
                keyCode = UInt32(kVK_ANSI_D)
            case "F":
                keyCode = UInt32(kVK_ANSI_F)
            case "G":
                keyCode = UInt32(kVK_ANSI_G)
            case "H":
                keyCode = UInt32(kVK_ANSI_H)
            case "J":
                keyCode = UInt32(kVK_ANSI_J)
            case "K":
                keyCode = UInt32(kVK_ANSI_K)
            case "L":
                keyCode = UInt32(kVK_ANSI_L)
            case "Z":
                keyCode = UInt32(kVK_ANSI_Z)
            case "X":
                keyCode = UInt32(kVK_ANSI_X)
            case "C":
                keyCode = UInt32(kVK_ANSI_C)
            case "V":
                keyCode = UInt32(kVK_ANSI_V)
            case "B":
                keyCode = UInt32(kVK_ANSI_B)
            case "N":
                keyCode = UInt32(kVK_ANSI_N)
            case "M":
                keyCode = UInt32(kVK_ANSI_M)
            case "9":
                keyCode = UInt32(kVK_ANSI_9)
            case "8":
                keyCode = UInt32(kVK_ANSI_8)
            case "7":
                keyCode = UInt32(kVK_ANSI_7)
            case "6":
                keyCode = UInt32(kVK_ANSI_6)
            case "5":
                keyCode = UInt32(kVK_ANSI_5)
            case "4":
                keyCode = UInt32(kVK_ANSI_4)
            case "3":
                keyCode = UInt32(kVK_ANSI_3)
            case "2":
                keyCode = UInt32(kVK_ANSI_2)
            case "1":
                keyCode = UInt32(kVK_ANSI_1)
            case "0":
                keyCode = UInt32(kVK_ANSI_0)
            default:
                break
            }
        }
        
        return (keyCode, modifiers)
    }
    
}

// Convert string to FourCharCode
private func fourCharCode(_ string: String) -> UInt32 {
    let chars = Array(string.utf8)
    return chars.indices.reduce(0) { acc, i in
        acc + (UInt32(chars[i]) << (8 * (3 - i)))
    }
}
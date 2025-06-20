import Foundation
import AppKit
import Carbon
import UserNotifications

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
    private var llmManager: LLMManager!
    private var hotkeyEventHandler: EventHotKeyRef?
    private var currentHotkeyCombo: [String] = ["⌘", "⇧", "R"] // Default hotkey
    
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
        if let savedHotkey = UserDefaults.standard.array(forKey: "global_hotkey") as? [String] {
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
                self.showNotification(title: "Configuration Error", message: "Please configure an API key in Settings")
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
            showNotification(title: "No Text", message: "No text was in clipboard - message copied to clipboard")
            iconDelegate?.setErrorState(message: "No text in clipboard")
            return
        }
        
        // Check if the clipboard contains our own "no text" message and ignore it
        let trimmedText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedText == "No text was in clipboard" {
            PotterLogger.shared.warning("text_processor", "⚠️ Ignoring our own 'no text' message")
            showNotification(title: "No Text", message: "Still no text in clipboard")
            iconDelegate?.setErrorState(message: "Still no text in clipboard")
            return
        }
        
        PotterLogger.shared.info("text_processor", "📝 Processing \(trimmedText.count) characters")
        showNotification(title: "Processing...", message: "AI is processing your text")
        
        // Update menu bar icon to show processing state
        iconDelegate?.setProcessingState()
        
        // Process with LLM
        Task {
            do {
                // Get current prompt from UserDefaults and prompt manager
                let currentPromptName = UserDefaults.standard.string(forKey: "current_prompt") ?? "summarize"
                let prompts = PromptManager.shared.loadPrompts()
                let selectedPrompt = prompts.first { $0.name == currentPromptName }
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
                    
                    self.showNotification(
                        title: "Processing Complete",
                        message: "Text processed with '\(currentPromptName)' and copied to clipboard! Press ⌘V to paste."
                    )
                }
            } catch {
                PotterLogger.shared.error("text_processor", "❌ LLM processing failed: \(error.localizedDescription)")
                await MainActor.run {
                    // Set error state with the actual error message
                    self.iconDelegate?.setErrorState(message: "LLM Error: \(error.localizedDescription)")
                    
                    self.showNotification(
                        title: "Processing Failed",
                        message: "Failed to process text: \(error.localizedDescription)"
                    )
                }
            }
        }
    }
    
    func setPromptMode(_ mode: PromptMode) {
        currentMode = mode
        PotterLogger.shared.info("core", "🎯 Mode changed to: \(mode.displayName)")
        showNotification(title: "Mode Changed", message: "Now using: \(mode.displayName)")
    }
    
    func getLLMManager() -> LLMManager {
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
        UserDefaults.standard.set(newHotkey, forKey: "global_hotkey")
        PotterLogger.shared.info("hotkeys", "🔄 Updated hotkey to: \(newHotkey.joined(separator: "+"))")
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
        var keyCode: UInt32 = UInt32(kVK_ANSI_R) // Default to R
        
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
            default:
                break
            }
        }
        
        return (keyCode, modifiers)
    }
    
    private func showNotification(title: String, message: String) {
        // Just log the notification - don't try to show UI notifications in CLI context
        PotterLogger.shared.info("notification", "📢 \(title): \(message)")
    }
}

// Convert string to FourCharCode
private func fourCharCode(_ string: String) -> UInt32 {
    let chars = Array(string.utf8)
    return chars.indices.reduce(0) { acc, i in
        acc + (UInt32(chars[i]) << (8 * (3 - i)))
    }
}
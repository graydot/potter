import Foundation
import AppKit
import Carbon

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
        // Register Cmd+Shift+R hotkey
        var eventHotKeyRef: EventHotKeyRef?
        let hotKeyID = EventHotKeyID(signature: fourCharCode("POTR"), id: UInt32(1))
        _ = UInt32(kEventHotKeyPressed)
        
        let status = RegisterEventHotKey(
            UInt32(kVK_ANSI_R), // R key
            UInt32(cmdKey + shiftKey), // Cmd+Shift
            hotKeyID,
            GetApplicationEventTarget(),
            0,
            &eventHotKeyRef
        )
        
        if status == noErr {
            self.hotkeyEventHandler = eventHotKeyRef
            
            // Install event handler
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
            
            PotterLogger.shared.info("hotkeys", "✅ Global hotkey registered (⌘⇧R)")
        } else {
            PotterLogger.shared.error("hotkeys", "❌ Failed to register global hotkey")
        }
    }
    
    @objc private func handleHotkey() {
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
            showNotification(title: "No Text", message: "No text found in clipboard. Copy some text first.")
            return
        }
        
        PotterLogger.shared.info("text_processor", "📝 Processing \(text.count) characters")
        showNotification(title: "Processing...", message: "AI is processing your text")
        
        // Process with LLM
        Task {
            do {
                // Get current prompt from UserDefaults and prompt manager
                let currentPromptName = UserDefaults.standard.string(forKey: "current_prompt") ?? "summarize"
                let prompts = PromptManager.shared.loadPrompts()
                let selectedPrompt = prompts.first { $0.name == currentPromptName }
                let promptText = selectedPrompt?.prompt ?? currentMode.prompt
                
                PotterLogger.shared.info("text_processor", "🤖 Using prompt: \(currentPromptName)")
                PotterLogger.shared.info("text_processor", "🔄 Calling LLM API...")
                
                let processedText = try await llmManager.processText(text, prompt: promptText)
                
                PotterLogger.shared.info("text_processor", "✅ LLM processing complete")
                PotterLogger.shared.info("text_processor", "📋 Result copied to clipboard (\(processedText.count) characters)")
                
                await MainActor.run {
                    // Put result back in clipboard
                    pasteboard.clearContents()
                    pasteboard.setString(processedText, forType: .string)
                    
                    self.showNotification(
                        title: "Processing Complete",
                        message: "Text processed with '\(currentPromptName)' and copied to clipboard! Press ⌘V to paste."
                    )
                }
            } catch {
                PotterLogger.shared.error("text_processor", "❌ LLM processing failed: \(error.localizedDescription)")
                await MainActor.run {
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
    
    private func showNotification(title: String, message: String) {
        // Simple alert for now - could upgrade to UserNotifications framework later
        DispatchQueue.main.async {
            let alert = NSAlert()
            alert.messageText = title
            alert.informativeText = message
            alert.addButton(withTitle: "OK")
            alert.runModal()
        }
    }
}

// Convert string to FourCharCode
private func fourCharCode(_ string: String) -> UInt32 {
    let chars = Array(string.utf8)
    return chars.indices.reduce(0) { acc, i in
        acc + (UInt32(chars[i]) << (8 * (3 - i)))
    }
}
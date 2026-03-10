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
    private var hotkeyCoordinator: HotkeyCoordinator?

    /// The current hotkey combo, delegated to HotkeyCoordinator.
    var currentHotkeyCombo: [String] {
        return hotkeyCoordinator?.currentHotkeyCombo ?? HotkeyConstants.defaultHotkey
    }

    // Icon state delegate
    weak var iconDelegate: IconStateDelegate?

    init(llmManager: LLMManager? = nil, settings: PotterSettings? = nil) {
        self.llmManager = llmManager
        self.settings = settings ?? PotterSettings()
    }

    func setup() {
        PotterLogger.shared.info("core", "🚀 Starting Potter Core...")

        // Initialize LLM manager on main actor if not injected
        if self.llmManager == nil {
            Task { @MainActor in
                self.llmManager = LLMManager()
            }
        }

        // Setup hotkey via coordinator
        let coordinator = HotkeyCoordinator()
        coordinator.setup { [weak self] in
            self?.handleHotkey()
        }
        self.hotkeyCoordinator = coordinator

        PotterLogger.shared.info("core", "✅ Potter Core initialized")
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
        // Step 1: Validate and retrieve clipboard text
        guard let trimmedText = validateAndGetClipboardText() else {
            return
        }
        
        // Step 2: Prepare for processing
        prepareForProcessing(textLength: trimmedText.count)
        
        // Step 3: Process with LLM asynchronously
        Task {
            await processTextWithLLM(trimmedText, using: llmManager)
        }
    }
    
    // MARK: - Text Processing Steps
    
    /// Validates clipboard content and returns processed text if valid
    @MainActor
    private func validateAndGetClipboardText() -> String? {
        let pasteboard = NSPasteboard.general
        
        // Check if clipboard has text
        guard let text = pasteboard.string(forType: .string), 
              !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            handleNoTextInClipboard(pasteboard)
            return nil
        }
        
        // Check if it's our own "no text" message
        let trimmedText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedText == "No text was in clipboard" {
            handleOwnNoTextMessage()
            return nil
        }
        
        return trimmedText
    }
    
    /// Handles the case when no text is found in clipboard
    @MainActor
    private func handleNoTextInClipboard(_ pasteboard: NSPasteboard) {
        PotterLogger.shared.warning("text_processor", "⚠️ No text found in clipboard")
        // Put helpful message in clipboard instead of showing alert
        pasteboard.clearContents()
        pasteboard.setString("No text was in clipboard", forType: .string)
        iconDelegate?.setErrorState(message: "No text in clipboard")
    }
    
    /// Handles the case when clipboard contains our own "no text" message
    @MainActor
    private func handleOwnNoTextMessage() {
        PotterLogger.shared.warning("text_processor", "⚠️ Ignoring our own 'no text' message")
        iconDelegate?.setErrorState(message: "Still no text in clipboard")
    }
    
    /// Prepares the UI and logging for text processing
    @MainActor
    private func prepareForProcessing(textLength: Int) {
        PotterLogger.shared.info("text_processor", "📝 Processing \(textLength) characters")
        iconDelegate?.setProcessingState()
    }
    
    /// Main LLM processing logic
    private func processTextWithLLM(_ text: String, using llmManager: LLMManager) async {
        do {
            let promptText = getCurrentPromptText()
            logProcessingStart(promptText: promptText, inputText: text)
            
            let processedText = try await llmManager.processText(text, prompt: promptText)
            
            logProcessingSuccess(outputText: processedText)
            await handleProcessingSuccess(processedText)
            
        } catch {
            let potterError = convertToPotterError(error)
            await handleProcessingError(potterError)
        }
    }
    
    /// Gets the current prompt text from settings and prompt service
    private func getCurrentPromptText() -> String {
        return PromptService.shared.getCurrentPromptText() ?? currentMode.prompt
    }
    
    /// Helper function to truncate text for secure logging
    private func truncateTextForLogging(_ text: String) -> String {
        if text.count <= 10 {
            return text
        }
        let start = String(text.prefix(5))
        let end = String(text.suffix(5))
        return "\(start)...\(end)"
    }
    
    /// Logs the start of LLM processing
    private func logProcessingStart(promptText: String, inputText: String) {
        let currentPromptName = PromptService.shared.currentPromptName
        PotterLogger.shared.info("text_processor", "🤖 Using prompt: \(currentPromptName)")
        PotterLogger.shared.info("text_processor", "📝 Text being sent to LLM:")
        PotterLogger.shared.info("text_processor", "||||| \(truncateTextForLogging(inputText)) |||||")
        PotterLogger.shared.info("text_processor", "🔄 Calling LLM API...")
    }
    
    /// Logs successful LLM processing
    private func logProcessingSuccess(outputText: String) {
        PotterLogger.shared.info("text_processor", "✅ LLM processing complete")
        PotterLogger.shared.info("text_processor", "📝 Text returned from LLM:")
        PotterLogger.shared.info("text_processor", "||||| \(truncateTextForLogging(outputText)) |||||")
        PotterLogger.shared.info("text_processor", "📋 Result copied to clipboard (\(outputText.count) characters)")
    }
    
    /// Handles successful text processing
    @MainActor
    private func handleProcessingSuccess(_ processedText: String) {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(processedText, forType: .string)
        iconDelegate?.setSuccessState()
    }
    
    /// Converts any error to PotterError for consistent handling
    private func convertToPotterError(_ error: Error) -> PotterError {
        if let potterError = error as? PotterError {
            return potterError
        } else {
            return PotterError.system(.systemCallFailed(call: "text_processing", errno: 0))
        }
    }
    
    /// Handles processing errors
    @MainActor
    private func handleProcessingError(_ error: PotterError) {
        GlobalErrorHandler.handle(error, context: "text_processing", showUser: false)
        iconDelegate?.setErrorState(message: error.localizedDescription)
    }
    
    func setPromptMode(_ mode: PromptMode) {
        currentMode = mode
        PotterLogger.shared.info("core", "🎯 Mode changed to: \(mode.displayName)")
        // Mode change logged only
    }
    
    func getLLMManager() -> LLMManager? {
        return llmManager
    }
    
    // MARK: - Hotkey Management (delegated to HotkeyCoordinator)

    func updateHotkey(_ newHotkey: [String]) {
        hotkeyCoordinator?.updateHotkey(newHotkey)

        // Notify icon delegate to update menu with new hotkey
        DispatchQueue.main.async {
            if let appDelegate = NSApplication.shared.delegate as? AppDelegate {
                Task { @MainActor in
                    appDelegate.menuBarManager?.updateMenuForHotkeyChange()
                }
            }
        }
    }

    func disableGlobalHotkey() {
        hotkeyCoordinator?.disableGlobalHotkey()
    }

    func enableGlobalHotkey() {
        hotkeyCoordinator?.enableGlobalHotkey()
    }

}
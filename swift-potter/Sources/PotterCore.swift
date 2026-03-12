import Foundation
import AppKit
import Carbon

// MARK: - Hotkey Constants
struct HotkeyConstants {
    static let defaultHotkey: [String] = ["⌘", "⇧", "9"]
    static let userDefaultsKey = UserDefaultsKeys.globalHotkey
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
    private var hotkeyCoordinator: (any HotkeyProvider)?
    private let textProvider: AccessibilityTextProvider

    /// The current hotkey combo, delegated to HotkeyCoordinator.
    var currentHotkeyCombo: [String] {
        return hotkeyCoordinator?.currentHotkeyCombo ?? HotkeyConstants.defaultHotkey
    }

    // Icon state delegate
    weak var iconDelegate: IconStateDelegate?

    init(llmManager: LLMManager? = nil,
         settings: PotterSettings? = nil,
         hotkeyProvider: (any HotkeyProvider)? = nil,
         textProvider: AccessibilityTextProvider = AccessibilityTextProvider()) {
        self.llmManager = llmManager
        self.settings = settings ?? PotterSettings()
        self.hotkeyCoordinator = hotkeyProvider
        self.textProvider = textProvider
    }

    func setup() {
        PotterLogger.shared.info("core", "🚀 Starting Potter Core...")

        // Initialize LLM manager on main actor if not injected
        if self.llmManager == nil {
            Task { @MainActor in
                self.llmManager = LLMManager.shared
            }
        }

        // Setup hotkey via coordinator (use injected provider or default to Carbon)
        if self.hotkeyCoordinator == nil {
            self.hotkeyCoordinator = HotkeyCoordinator()
        }
        hotkeyCoordinator?.setup { [weak self] in
            self?.handleHotkey()
        }

        PotterLogger.shared.info("core", "✅ Potter Core initialized")
    }
    
    @objc private func handleHotkey() {
        PotterLogger.shared.info("hotkey", "🎯 Global hotkey callback triggered")
        // Immediate visual feedback — show processing state before any I/O
        self.iconDelegate?.setProcessingState()
        self.processClipboardText()
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
        // Step 1: Read text — try AX selection first, fall back to clipboard.
        guard let (rawText, inputSource) = textProvider.readText() else {
            handleNoTextAvailable()
            return
        }

        let trimmedText = rawText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedText.isEmpty else {
            handleNoTextAvailable()
            return
        }

        // Guard against our own "no text" sentinel appearing in the clipboard.
        if trimmedText == "No text was in clipboard" {
            PotterLogger.shared.warning("text_processor", "⚠️ Ignoring our own 'no text' message")
            iconDelegate?.setErrorState(message: "Still no text in clipboard")
            return
        }

        let sourceLabel: String
        if case .clipboard = inputSource { sourceLabel = "clipboard" } else { sourceLabel = "selection" }
        PotterLogger.shared.info("text_processor", "📥 Input source: \(sourceLabel) (\(trimmedText.count) chars)")

        // Step 2: Prepare for processing
        prepareForProcessing(textLength: trimmedText.count)

        // Step 3: Process with LLM asynchronously
        Task {
            await processTextWithLLM(trimmedText, originalText: trimmedText,
                                     inputSource: inputSource, using: llmManager)
        }
    }

    /// Handles the case where no text is available from either AX or clipboard.
    @MainActor
    private func handleNoTextAvailable() {
        PotterLogger.shared.warning("text_processor", "⚠️ No text found in selection or clipboard")
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString("No text was in clipboard", forType: .string)
        iconDelegate?.setErrorState(message: "No text in clipboard")
    }
    
    // MARK: - Text Processing Steps
    
    /// Prepares the UI and logging for text processing
    @MainActor
    private func prepareForProcessing(textLength: Int) {
        PotterLogger.shared.info("text_processor", "📝 Processing \(textLength) characters")
        iconDelegate?.setProcessingState()
    }
    
    /// Main LLM processing logic
    private func processTextWithLLM(_ text: String, originalText: String,
                                    inputSource: TextInputSource, using llmManager: LLMManager) async {
        do {
            let promptText = getCurrentPromptText()
            logProcessingStart(promptText: promptText, inputText: text)

            // Resolve the model to use based on the prompt's tier setting.
            // - Tier set: use the user's preferred model for that tier on the active provider.
            // - Tier nil: fall back to the user's preferred Standard model (sensible default).
            let currentPrompt = PromptService.shared.getCurrentPrompt()
            let tier = currentPrompt?.modelTier ?? .standard
            let outputMode = currentPrompt?.outputMode ?? .replace
            let resolvedModelName: String = await MainActor.run {
                if let tierModel = ModelRegistry.shared.preferredModel(for: tier, provider: llmManager.selectedProvider) {
                    PotterLogger.shared.info("text_processor", "Using \(tier.displayName) tier → \(tierModel.name) (\(llmManager.selectedProvider.displayName))")
                    llmManager.selectModel(tierModel)
                }
                return llmManager.selectedModel?.name ?? ""
            }

            let startTime = Date()

            // Use streaming so tokens appear progressively.
            // For append/prepend modes we accumulate and write once at the end;
            // for replace mode we write each chunk to clipboard as it arrives.
            var streamedTokens = ""
            let processedText = try await llmManager.streamText(text, prompt: promptText) { [weak self] token in
                guard let self else { return }
                streamedTokens += token
                // For replace mode: progressively update clipboard with each chunk.
                if outputMode == .replace {
                    let partial = streamedTokens
                    let src = inputSource
                    Task { @MainActor [weak self] in
                        self?.textProvider.writeResult(partial, source: src)
                    }
                }
            }
            let durationMs = Int(Date().timeIntervalSince(startTime) * 1000)

            // Apply output mode: combine original text + LLM result per the prompt's setting.
            let finalText = outputMode.apply(original: originalText, result: processedText)
            if outputMode != .replace {
                PotterLogger.shared.info("text_processor", "📎 Output mode: \(outputMode.displayName) → \(finalText.count) characters total")
            }

            logProcessingSuccess(outputText: processedText)

            // Record history entry (async, fire-and-forget)
            let providerName = await MainActor.run { llmManager.selectedProvider.displayName }
            let promptName = PromptService.shared.currentPromptName
            let entry = ProcessingHistoryEntry(
                inputText: originalText,
                outputText: processedText,
                promptName: promptName.isEmpty ? "Default" : promptName,
                modelName: resolvedModelName,
                providerName: providerName,
                durationMs: durationMs
            )
            ProcessingHistoryStore.shared.append(entry)

            await handleProcessingSuccess(finalText, inputSource: inputSource)

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
    
    /// Handles successful text processing — routes output via textProvider.
    @MainActor
    private func handleProcessingSuccess(_ processedText: String, inputSource: TextInputSource) {
        let wrote = textProvider.writeResult(processedText, source: inputSource)

        // If AX write failed, fall back to clipboard so the result isn't lost.
        if case .accessibility = inputSource, !wrote {
            PotterLogger.shared.warning("text_processor", "⚠️ AX write failed — falling back to clipboard")
            textProvider.writeResult(processedText, source: .clipboard)
        }

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
        Task { @MainActor in
            if let appDelegate = NSApplication.shared.delegate as? AppDelegate {
                appDelegate.menuBarManager?.updateMenuForHotkeyChange()
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
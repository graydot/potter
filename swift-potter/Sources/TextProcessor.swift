import Foundation

/// Processes text by combining a prompt with LLM processing.
/// Extracted from PotterCore to enable testing without Carbon Event APIs or clipboard access.
class TextProcessor {
    private let promptProvider: PromptProviding
    private let llmProcessor: LLMProcessing

    init(promptProvider: PromptProviding, llmProcessor: LLMProcessing) {
        self.promptProvider = promptProvider
        self.llmProcessor = llmProcessor
    }

    /// Process text using an explicit prompt.
    func processText(_ text: String, withPrompt prompt: String) async throws -> String {
        let result = try await llmProcessor.processText(text, prompt: prompt)
        return result.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// Process text using the current prompt from the prompt provider.
    func processText(_ text: String) async throws -> String {
        guard let prompt = promptProvider.getCurrentPromptText() else {
            throw PotterError.configuration(.missingConfiguration(key: "prompt"))
        }
        return try await processText(text, withPrompt: prompt)
    }
}

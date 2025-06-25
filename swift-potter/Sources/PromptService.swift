import Foundation

// MARK: - PromptService
/// Service class responsible for all prompt-related business logic and data operations
/// Separates prompt management from UI concerns
class PromptService: ObservableObject {
    static let shared = PromptService()
    
    // MARK: - Published Properties for UI Binding
    @Published var prompts: [PromptItem] = []
    @Published var isLoading = false
    
    // MARK: - Private Properties
    private var promptsCache: [PromptItem]?
    private var lastFileModification: Date?
    private var testFileURL: URL? // For testing support
    
    // MARK: - Initialization
    private init() {
        loadPrompts()
    }
    
    // MARK: - File Management
    private var promptsFileURL: URL {
        // Use test file URL if set (for testing)
        if let testURL = testFileURL {
            return testURL
        }
        
        // Always use Application Support to ensure consistency
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let potterDir = appSupport.appendingPathComponent("Potter")
        
        // Create directory if it doesn't exist
        try? FileManager.default.createDirectory(at: potterDir, withIntermediateDirectories: true)
        
        return potterDir.appendingPathComponent("prompts.json")
    }
    
    // MARK: - Public API
    
    /// Load prompts from storage and update published properties
    func loadPrompts() {
        isLoading = true
        
        // Check if we have valid cached data
        if let cached = promptsCache,
           let lastMod = lastFileModification,
           let fileAttributes = try? FileManager.default.attributesOfItem(atPath: promptsFileURL.path),
           let currentMod = fileAttributes[.modificationDate] as? Date,
           currentMod <= lastMod {
            // Cache is still valid, return cached data
            PotterLogger.shared.debug("prompts", "📋 Using cached prompts (\(cached.count) items)")
            updatePromptsOnMainThread(cached)
            return
        }
        
        // Check if file exists, if not create it with defaults
        if !FileManager.default.fileExists(atPath: promptsFileURL.path) {
            let defaults = createDefaultPrompts()
            savePromptsToFile(defaults)
            PotterLogger.shared.debug("prompts", "📄 Created new prompts file with \(defaults.count) default prompts")
            updatePromptsOnMainThread(defaults)
            return
        }
        
        // File exists, load from it
        do {
            let data = try Data(contentsOf: promptsFileURL)
            let loadedPrompts = try JSONDecoder().decode([PromptItem].self, from: data)
            
            // Check if loaded prompts array is empty and restore defaults
            if loadedPrompts.isEmpty {
                PotterLogger.shared.warning("prompts", "📄 Loaded prompts array is empty - recreating with defaults")
                let defaults = createDefaultPrompts()
                savePromptsToFile(defaults)
                updatePromptsOnMainThread(defaults)
                return
            }
            
            // Update cache
            promptsCache = loadedPrompts
            if let fileAttributes = try? FileManager.default.attributesOfItem(atPath: promptsFileURL.path) {
                lastFileModification = fileAttributes[.modificationDate] as? Date
            }
            
            PotterLogger.shared.debug("prompts", "📖 Loaded \(loadedPrompts.count) prompts")
            updatePromptsOnMainThread(loadedPrompts)
            
        } catch {
            PotterLogger.shared.error("prompts", "❌ Failed to load prompts: \(error)")
            
            // Fallback to defaults
            let defaults = createDefaultPrompts()
            savePromptsToFile(defaults)
            updatePromptsOnMainThread(defaults)
        }
    }
    
    /// Update prompts on main thread, handling test vs production scenarios
    private func updatePromptsOnMainThread(_ newPrompts: [PromptItem]) {
        // For testing, update synchronously to avoid timing issues
        if testFileURL != nil {
            prompts = newPrompts
            isLoading = false
        } else {
            // For production, update asynchronously to avoid blocking UI
            DispatchQueue.main.async {
                self.prompts = newPrompts
                self.isLoading = false
            }
        }
    }
    
    /// Save a new or edited prompt
    func savePrompt(_ prompt: PromptItem, at index: Int? = nil) -> Result<Void, PromptServiceError> {
        // Validate prompt
        guard !prompt.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return .failure(.invalidPromptName)
        }
        
        guard !prompt.prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return .failure(.invalidPromptContent)
        }
        
        // Check for duplicate names (excluding current prompt if editing)
        if let existingIndex = prompts.firstIndex(where: { $0.name == prompt.name }),
           existingIndex != index {
            return .failure(.duplicatePromptName)
        }
        
        // Update prompts array
        if let index = index {
            // Editing existing prompt
            prompts[index] = prompt
        } else {
            // Adding new prompt
            prompts.append(prompt)
        }
        
        // Save to file
        savePromptsToFile(prompts)
        
        PotterLogger.shared.info("prompts", "💾 Saved prompt: \(prompt.name)")
        return .success(())
    }
    
    /// Delete a prompt at the specified index
    func deletePrompt(at index: Int) -> Result<Void, PromptServiceError> {
        guard index >= 0 && index < prompts.count else {
            return .failure(.invalidIndex)
        }
        
        // Prevent deleting the last prompt
        if prompts.count <= 1 {
            return .failure(.cannotDeleteLastPrompt)
        }
        
        let deletedPrompt = prompts[index]
        prompts.remove(at: index)
        savePromptsToFile(prompts)
        
        PotterLogger.shared.info("prompts", "🗑️ Deleted prompt: \(deletedPrompt.name)")
        return .success(())
    }
    
    /// Get a prompt by name
    func getPrompt(named name: String) -> PromptItem? {
        return prompts.first { $0.name == name }
    }
    
    /// Get a prompt by index
    func getPrompt(at index: Int) -> PromptItem? {
        guard index >= 0 && index < prompts.count else { return nil }
        return prompts[index]
    }
    
    /// Check if a prompt name already exists
    func promptNameExists(_ name: String, excluding index: Int? = nil) -> Bool {
        if let existingIndex = prompts.firstIndex(where: { $0.name == name }),
           existingIndex != index {
            return true
        }
        return false
    }
    
    /// Reset all prompts to defaults
    func resetToDefaults() {
        let defaults = createDefaultPrompts()
        prompts = defaults
        savePromptsToFile(defaults)
        PotterLogger.shared.info("prompts", "🔄 Reset prompts to defaults")
    }
    
    /// Clear cache - useful for testing and external changes
    func clearCache() {
        promptsCache = nil
        lastFileModification = nil
        PotterLogger.shared.debug("prompts", "🗑️ Prompt cache cleared")
    }
    
    // MARK: - Testing Support
    func setTestFileURL(_ url: URL?) {
        testFileURL = url
        if let url = url {
            // Create parent directory if needed
            try? FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        }
        clearCache()
        // Reload prompts with new file location
        loadPrompts()
    }
    
    /// For test compatibility - save multiple prompts at once
    func savePrompts(_ newPrompts: [PromptItem]) {
        prompts = newPrompts
        savePromptsToFile(newPrompts)
    }
    
    /// For test compatibility - get current prompts array
    func getPrompts() -> [PromptItem] {
        return prompts
    }
    
    // MARK: - Private Methods
    
    private func savePromptsToFile(_ prompts: [PromptItem]) {
        do {
            let encoder = JSONEncoder()
            encoder.outputFormatting = .prettyPrinted
            let data = try encoder.encode(prompts)
            try data.write(to: promptsFileURL)
            
            // Update cache
            promptsCache = prompts
            if let fileAttributes = try? FileManager.default.attributesOfItem(atPath: promptsFileURL.path) {
                lastFileModification = fileAttributes[.modificationDate] as? Date
            }
            
            PotterLogger.shared.debug("prompts", "💾 Saved \(prompts.count) prompts to \(promptsFileURL.path)")
            
        } catch {
            PotterLogger.shared.error("prompts", "❌ Failed to save prompts: \(error)")
        }
    }
    
    private func createDefaultPrompts() -> [PromptItem] {
        return [
            PromptItem(name: "Fix Grammar", prompt: "Please fix any grammar, spelling, or punctuation errors in the following text while preserving its original meaning and tone:"),
            PromptItem(name: "Summarize", prompt: "Please provide a concise summary of the following text:"),
            PromptItem(name: "Explain", prompt: "Please explain the following text in simple, easy-to-understand terms:"),
            PromptItem(name: "Translate", prompt: "Please translate the following text to English:"),
            PromptItem(name: "Professional Tone", prompt: "Please rewrite the following text in a more professional and polished tone:")
        ]
    }
}

// MARK: - PromptServiceError
enum PromptServiceError: Error, LocalizedError {
    case invalidPromptName
    case invalidPromptContent
    case duplicatePromptName
    case invalidIndex
    case cannotDeleteLastPrompt
    case fileAccessError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidPromptName:
            return "Prompt name cannot be empty"
        case .invalidPromptContent:
            return "Prompt content cannot be empty"
        case .duplicatePromptName:
            return "A prompt with this name already exists"
        case .invalidIndex:
            return "Invalid prompt index"
        case .cannotDeleteLastPrompt:
            return "Cannot delete the last remaining prompt"
        case .fileAccessError(let error):
            return "File access error: \(error.localizedDescription)"
        }
    }
}
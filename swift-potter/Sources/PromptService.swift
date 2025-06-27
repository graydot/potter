import Foundation

// MARK: - PromptService
/// Service class responsible for all prompt-related business logic and data operations
/// Separates prompt management from UI concerns
class PromptService: ObservableObject {
    static let shared = PromptService()
    
    // MARK: - Published Properties for UI Binding
    @Published var prompts: [PromptItem] = []
    @Published var isLoading = false
    @Published var currentPromptName: String = ""
    
    // MARK: - Private Properties
    private var promptsCache: [PromptItem]?
    private var lastFileModification: Date?
    private var testFileURL: URL? // For testing support
    
    // MARK: - Initialization
    private init() {
        loadPrompts()
        loadCurrentPrompt()
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
        
        // Check if file exists, if not copy from bundle
        if !FileManager.default.fileExists(atPath: promptsFileURL.path) {
            let defaults = loadDefaultPromptsFromBundle()
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
                let defaults = loadDefaultPromptsFromBundle()
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
            let defaults = loadDefaultPromptsFromBundle()
            savePromptsToFile(defaults)
            updatePromptsOnMainThread(defaults)
        }
    }
    
    /// Update prompts on main thread, handling test vs production scenarios
    private func updatePromptsOnMainThread(_ newPrompts: [PromptItem]) {
        // Always update synchronously during initial load to ensure prompts are available immediately
        if Thread.isMainThread {
            prompts = newPrompts
            isLoading = false
        } else {
            DispatchQueue.main.sync {
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
        
        // If we deleted the current prompt, select the first remaining one
        if deletedPrompt.name == currentPromptName {
            setCurrentPromptToFirst()
        }
        
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
        let defaults = loadDefaultPromptsFromBundle()
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
    
    // MARK: - Current Prompt Management
    
    /// Get the currently selected prompt
    func getCurrentPrompt() -> PromptItem? {
        return getPrompt(named: currentPromptName)
    }
    
    /// Get the currently selected prompt text
    func getCurrentPromptText() -> String? {
        return getCurrentPrompt()?.prompt
    }
    
    /// Set the current prompt by name
    func setCurrentPrompt(_ name: String) {
        guard getPrompt(named: name) != nil else {
            PotterLogger.shared.warning("prompts", "⚠️ Attempted to set invalid prompt: \(name)")
            return
        }
        
        currentPromptName = name
        UserDefaults.standard.set(name, forKey: "current_prompt")
        PotterLogger.shared.info("prompts", "📋 Current prompt set to: \(name)")
    }
    
    /// Load the current prompt from UserDefaults, with fallback to first prompt
    private func loadCurrentPrompt() {
        let savedPromptName = UserDefaults.standard.string(forKey: "current_prompt")
        
        if let savedPromptName = savedPromptName {
            // Check if the saved prompt still exists
            if getPrompt(named: savedPromptName) != nil {
                currentPromptName = savedPromptName
                PotterLogger.shared.debug("prompts", "📋 Loaded saved prompt: \(savedPromptName)")
            } else {
                // Saved prompt no longer exists, use first and save it
                setCurrentPromptToFirst()
                PotterLogger.shared.info("prompts", "📋 Saved prompt '\(savedPromptName)' not found, defaulting to first")
            }
        } else {
            // No saved prompt, use first and save it
            setCurrentPromptToFirst()
            PotterLogger.shared.info("prompts", "📋 No saved prompt found, defaulting to first")
        }
    }
    
    /// Set current prompt to the first available prompt and save it
    private func setCurrentPromptToFirst() {
        guard let firstPrompt = prompts.first else {
            PotterLogger.shared.error("prompts", "❌ No prompts available to set as current")
            return
        }
        
        currentPromptName = firstPrompt.name
        UserDefaults.standard.set(firstPrompt.name, forKey: "current_prompt")
        PotterLogger.shared.info("prompts", "📋 Set current prompt to first: \(firstPrompt.name)")
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
    
    /// Load default prompts from the bundle's config/prompts.json file
    private func loadDefaultPromptsFromBundle() -> [PromptItem] {
        guard let bundleURL = Bundle.module.url(forResource: "prompts", withExtension: "json", subdirectory: "config") else {
            PotterLogger.shared.error("prompts", "❌ Could not find prompts.json in bundle")
            return []
        }
        
        do {
            let data = try Data(contentsOf: bundleURL)
            let prompts = try JSONDecoder().decode([PromptItem].self, from: data)
            PotterLogger.shared.debug("prompts", "📦 Loaded \(prompts.count) default prompts from bundle")
            return prompts
        } catch {
            PotterLogger.shared.error("prompts", "❌ Failed to load default prompts from bundle: \(error)")
            return []
        }
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
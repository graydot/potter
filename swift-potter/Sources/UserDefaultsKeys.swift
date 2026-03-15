import Foundation

// MARK: - UserDefaultsKeys
//
// Single source of truth for every UserDefaults key string used in the app.
// All keys are declared here as static constants so that typos are caught at
// compile time and the full set of persisted preferences is visible in one place.
//
// Naming conventions:
//   - LLM / provider settings: no prefix
//   - Per-provider API keys:    "api_key_<provider rawValue>"  (helpers below)
//   - UI layout state:          "ui_" prefix
//
// Usage:
//   UserDefaults.standard.set(value, forKey: UserDefaultsKeys.llmProvider)
//   UserDefaults.standard.string(forKey: UserDefaultsKeys.currentPrompt)

enum UserDefaultsKeys {

    // MARK: - LLM / Provider

    /// The raw value of the currently selected LLMProvider.
    static let llmProvider = "llm_provider"

    /// The model ID of the currently selected LLMModel.
    static let selectedModel = "selected_model"

    // MARK: - Prompts

    /// Name of the currently active prompt.
    static let currentPrompt = "current_prompt"

    // MARK: - Hotkey

    /// Persisted hotkey combo stored as [String] (e.g. ["⌘", "⇧", "9"]).
    static let globalHotkey = "global_hotkey"

    // MARK: - Onboarding

    /// Bool flag — true once the user has completed onboarding.
    static let onboardingCompleted = "onboarding_completed"

    // MARK: - API Keys

    /// API key for the OpenAI provider.
    static let apiKeyOpenAI = "api_key_openai"

    /// API key for the Anthropic provider.
    static let apiKeyAnthropic = "api_key_anthropic"

    /// API key for the Google provider.
    static let apiKeyGoogle = "api_key_google"

    /// Returns the UserDefaults key for the API key of any LLMProvider.
    static func apiKey(for provider: LLMProvider) -> String {
        return "api_key_\(provider.rawValue)"
    }

    // MARK: - Per-Provider Tier Config

    /// Returns the UserDefaults key for the tier-to-model mapping of a given provider.
    /// Stored as JSON-encoded ProviderTierConfig.
    static func tierConfig(for provider: LLMProvider) -> String {
        return "tier_config_\(provider.rawValue)"
    }

    // MARK: - UI State  (ui_ prefix)

    /// Which section is active in the settings sidebar (Int).
    static let uiSelectedSection = "ui_selected_section"

    /// Width of the settings sidebar in points (Double).
    static let uiSidebarWidth = "ui_sidebar_width"

    /// UUID string of the currently selected prompt row.
    static let uiSelectedPromptID = "ui_selected_prompt_id"

    /// UUID string used as the scroll anchor in the prompts list.
    static let uiScrollAnchorID = "ui_scroll_anchor_id"

    /// Height of the prompt text area in the edit dialog (Double).
    static let uiPromptTextAreaHeight = "ui_prompt_text_area_height"

    /// Raw string for the selected log filter level (nil = "All").
    static let uiLogFilterRaw = "ui_log_filter_raw"

    // MARK: - Debug

    /// Bool flag — when true, logs full clipboard/text content instead of redacting.
    static let debugLogClipboard = "debug_log_clipboard"
}

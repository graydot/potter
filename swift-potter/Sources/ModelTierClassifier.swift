import Foundation

/// Assigns model tiers based on name/ID pattern matching.
/// Used to auto-classify models fetched from provider APIs.
enum ModelTierClassifier {

    private static let fastPatterns = ["mini", "flash", "haiku", "nano", "lite", "small"]
    private static let thinkingPatterns = ["thinking", "o1", "o3", "o4", "reason"]

    /// Classify a model ID into a tier based on naming patterns.
    static func classify(_ modelId: String, provider: LLMProvider) -> ModelTier {
        let lowered = modelId.lowercased()

        var isThinking = false
        for pattern in thinkingPatterns {
            if matchesWordBoundary(lowered, pattern: pattern) {
                isThinking = true
                break
            }
        }

        var isFast = false
        for pattern in fastPatterns {
            if matchesWordBoundary(lowered, pattern: pattern) {
                isFast = true
                break
            }
        }

        if isThinking && isFast {
            // "o4-mini" → fast (mini wins over o4)
            // "gemini-2.5-flash-thinking" → thinking (thinking wins over flash)
            if matchesWordBoundary(lowered, pattern: "mini") { return .fast }
            return .thinking
        }

        if isThinking { return .thinking }
        if isFast { return .fast }

        return .standard
    }

    /// Match a pattern as a word boundary segment in a hyphen-separated model ID.
    /// "mini" matches "o4-mini" and "gpt-4o-mini-2024" but not "gemini-2.5-pro".
    /// "o1" matches "o1-preview" but not "gpt-4o-1106".
    private static func matchesWordBoundary(_ modelId: String, pattern: String) -> Bool {
        let segments = modelId.split(separator: "-").map(String.init)
        return segments.contains(pattern)
    }
}

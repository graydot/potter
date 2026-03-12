import Foundation

/// Per-provider mapping from model tier to a specific model ID.
///
/// Each configured provider (one with a saved API key) can have independent
/// Fast / Standard / Thinking model selections. When a prompt runs with a tier,
/// the active provider's config is consulted to find the right model.
///
/// - `nil` model IDs mean "use the registry's best model for this tier" (auto).
struct ProviderTierConfig: Codable, Equatable {
    var fast: String?      // model ID, or nil = auto
    var standard: String?  // model ID, or nil = auto
    var thinking: String?  // model ID, or nil = auto

    /// Returns the stored model ID for the given tier.
    func modelID(for tier: ModelTier) -> String? {
        switch tier {
        case .fast:     return fast
        case .standard: return standard
        case .thinking: return thinking
        }
    }

    /// Returns a new config with the given tier's model updated.
    func setting(_ modelID: String?, for tier: ModelTier) -> ProviderTierConfig {
        var copy = self
        switch tier {
        case .fast:     copy.fast = modelID
        case .standard: copy.standard = modelID
        case .thinking: copy.thinking = modelID
        }
        return copy
    }
}

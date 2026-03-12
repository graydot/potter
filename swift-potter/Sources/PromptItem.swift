import Foundation

/// Controls how the LLM result is combined with the original clipboard text.
enum OutputMode: String, Codable, CaseIterable {
    /// Replace clipboard with the LLM result (default — existing behaviour).
    case replace
    /// Keep original text and append the LLM result after it.
    case append
    /// Keep original text and prepend the LLM result before it.
    case prepend

    var displayName: String {
        switch self {
        case .replace: return "Replace"
        case .append:  return "Append"
        case .prepend: return "Prepend"
        }
    }

    /// Combines `original` and `result` according to this mode.
    func apply(original: String, result: String) -> String {
        switch self {
        case .replace: return result
        case .append:  return original + "\n\n" + result
        case .prepend: return result + "\n\n" + original
        }
    }
}

struct PromptItem: Identifiable, Equatable, Codable {
    let id: UUID
    var name: String
    var prompt: String
    var modelTier: ModelTier?    // nil = use global default model
    var outputMode: OutputMode   // how to combine original text + LLM result

    init(name: String, prompt: String, modelTier: ModelTier? = nil, outputMode: OutputMode = .replace) {
        self.id = UUID()
        self.name = name
        self.prompt = prompt
        self.modelTier = modelTier
        self.outputMode = outputMode
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        if let id = try? container.decode(UUID.self, forKey: .id) {
            self.id = id
        } else {
            self.id = UUID()
        }

        self.name = try container.decode(String.self, forKey: .name)
        self.prompt = try container.decode(String.self, forKey: .prompt)
        self.modelTier = try container.decodeIfPresent(ModelTier.self, forKey: .modelTier)
        // Default to .replace so existing persisted prompts without this field are unaffected.
        self.outputMode = (try? container.decodeIfPresent(OutputMode.self, forKey: .outputMode)) ?? .replace
    }

    private enum CodingKeys: String, CodingKey {
        case id, name, prompt, modelTier, outputMode
    }

    static func == (lhs: PromptItem, rhs: PromptItem) -> Bool {
        lhs.id == rhs.id
    }
}

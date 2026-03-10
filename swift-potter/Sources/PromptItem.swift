import Foundation

struct PromptItem: Identifiable, Equatable, Codable {
    let id: UUID
    var name: String
    var prompt: String
    var modelTier: ModelTier?  // nil = use global default model

    init(name: String, prompt: String, modelTier: ModelTier? = nil) {
        self.id = UUID()
        self.name = name
        self.prompt = prompt
        self.modelTier = modelTier
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
    }

    private enum CodingKeys: String, CodingKey {
        case id, name, prompt, modelTier
    }

    static func == (lhs: PromptItem, rhs: PromptItem) -> Bool {
        lhs.id == rhs.id
    }
}

import Testing
import Foundation
@testable import Potter

// MARK: - LLMProvider Tests

@Suite("LLMProvider")
struct STLLMProviderTests {

    @Test("raw values match expected strings")
    func rawValues() {
        #expect(LLMProvider.openAI.rawValue == "openai")
        #expect(LLMProvider.anthropic.rawValue == "anthropic")
        #expect(LLMProvider.google.rawValue == "google")
    }

    @Test("allCases contains exactly three providers")
    func allCasesCount() {
        #expect(LLMProvider.allCases.count == 3)
    }

    @Test("allCases contains all known providers")
    func allCasesContents() {
        let cases = LLMProvider.allCases
        #expect(cases.contains(.openAI))
        #expect(cases.contains(.anthropic))
        #expect(cases.contains(.google))
    }

    @Test("id matches rawValue")
    func idEqualsRawValue() {
        for provider in LLMProvider.allCases {
            #expect(provider.id == provider.rawValue)
        }
    }

    @Test("displayName is correct for all providers")
    func displayNames() {
        #expect(LLMProvider.openAI.displayName == "OpenAI")
        #expect(LLMProvider.anthropic.displayName == "Anthropic")
        #expect(LLMProvider.google.displayName == "Google")
    }

    @Test("apiKeyPlaceholder is non-empty for all providers")
    func apiKeyPlaceholders() {
        for provider in LLMProvider.allCases {
            #expect(!provider.apiKeyPlaceholder.isEmpty)
        }
    }

    @Test("apiKeyURL starts with https for all providers")
    func apiKeyURLs() {
        for provider in LLMProvider.allCases {
            #expect(provider.apiKeyURL.hasPrefix("https://"))
        }
    }

    @Test("Codable round-trip preserves raw value")
    func codableRoundTrip() throws {
        let encoder = JSONEncoder()
        let decoder = JSONDecoder()
        for provider in LLMProvider.allCases {
            let data = try encoder.encode(provider)
            let decoded = try decoder.decode(LLMProvider.self, from: data)
            #expect(decoded == provider)
        }
    }

    @Test("decodes from known JSON string values")
    func decodeFromJSON() throws {
        let json = #""openai""#
        let data = json.data(using: .utf8)!
        let decoded = try JSONDecoder().decode(LLMProvider.self, from: data)
        #expect(decoded == .openAI)
    }

    @Test("encodes to expected JSON string value")
    func encodeToJSON() throws {
        let data = try JSONEncoder().encode(LLMProvider.anthropic)
        let str = String(data: data, encoding: .utf8)
        #expect(str == #""anthropic""#)
    }

    @Test("Hashable — usable as Dictionary key")
    func hashableDictionaryKey() {
        var dict: [LLMProvider: String] = [:]
        for provider in LLMProvider.allCases {
            dict[provider] = provider.displayName
        }
        #expect(dict.count == 3)
        #expect(dict[.openAI] == "OpenAI")
        #expect(dict[.anthropic] == "Anthropic")
        #expect(dict[.google] == "Google")
    }

    @Test("Hashable — usable in Set, deduplicates same case")
    func hashableSet() {
        let set: Set<LLMProvider> = [.openAI, .openAI, .anthropic]
        #expect(set.count == 2)
    }

    @Test("models property returns non-empty list for each provider")
    func modelsPropertyIsNonEmpty() {
        for provider in LLMProvider.allCases {
            #expect(!provider.models.isEmpty)
        }
    }

    @Test("models property returns correctly tagged models for each provider")
    func modelsMatchProvider() {
        for provider in LLMProvider.allCases {
            for model in provider.models {
                #expect(model.provider == provider)
            }
        }
    }
}

// MARK: - ModelTier Tests

@Suite("ModelTier")
struct STModelTierTests {

    @Test("raw values match expected strings")
    func rawValues() {
        #expect(ModelTier.fast.rawValue == "fast")
        #expect(ModelTier.standard.rawValue == "standard")
        #expect(ModelTier.thinking.rawValue == "thinking")
    }

    @Test("allCases contains exactly three tiers")
    func allCasesCount() {
        #expect(ModelTier.allCases.count == 3)
    }

    @Test("id matches rawValue")
    func idEqualsRawValue() {
        for tier in ModelTier.allCases {
            #expect(tier.id == tier.rawValue)
        }
    }

    @Test("displayName values are correct")
    func displayNames() {
        #expect(ModelTier.fast.displayName == "Fast")
        #expect(ModelTier.standard.displayName == "Standard")
        #expect(ModelTier.thinking.displayName == "Thinking")
    }

    @Test("description is non-empty for all tiers")
    func descriptionsNonEmpty() {
        for tier in ModelTier.allCases {
            #expect(!tier.description.isEmpty)
        }
    }

    @Test("Codable round-trip preserves all tiers")
    func codableRoundTrip() throws {
        let encoder = JSONEncoder()
        let decoder = JSONDecoder()
        for tier in ModelTier.allCases {
            let data = try encoder.encode(tier)
            let decoded = try decoder.decode(ModelTier.self, from: data)
            #expect(decoded == tier)
        }
    }

    @Test("decodes from known JSON string value")
    func decodeFromJSON() throws {
        let json = #""thinking""#
        let data = json.data(using: .utf8)!
        let decoded = try JSONDecoder().decode(ModelTier.self, from: data)
        #expect(decoded == .thinking)
    }

    @Test("encodes to expected JSON string value")
    func encodeToJSON() throws {
        let data = try JSONEncoder().encode(ModelTier.fast)
        let str = String(data: data, encoding: .utf8)
        #expect(str == #""fast""#)
    }

    @Test("decoding an unknown raw value throws")
    func decodingUnknownRawValueThrows() {
        let json = #""ultra""#
        let data = json.data(using: .utf8)!
        #expect(throws: (any Error).self) {
            _ = try JSONDecoder().decode(ModelTier.self, from: data)
        }
    }
}

// MARK: - LLMModel Tests

@Suite("LLMModel")
struct STLLMModelTests {

    @Test("static openAI models all have expected provider")
    func openAIModelsProvider() {
        for model in LLMModel.openAIModels {
            #expect(model.provider == .openAI)
        }
    }

    @Test("static anthropic models all have expected provider")
    func anthropicModelsProvider() {
        for model in LLMModel.anthropicModels {
            #expect(model.provider == .anthropic)
        }
    }

    @Test("static google models all have expected provider")
    func googleModelsProvider() {
        for model in LLMModel.googleModels {
            #expect(model.provider == .google)
        }
    }

    @Test("static model lists are non-empty")
    func staticModelListsNonEmpty() {
        #expect(!LLMModel.openAIModels.isEmpty)
        #expect(!LLMModel.anthropicModels.isEmpty)
        #expect(!LLMModel.googleModels.isEmpty)
    }

    @Test("every static model has non-empty id, name, and description")
    func staticModelsHaveNonEmptyFields() {
        let allModels = LLMModel.openAIModels + LLMModel.anthropicModels + LLMModel.googleModels
        for model in allModels {
            #expect(!model.id.isEmpty, "Model id should not be empty: \(model.id)")
            #expect(!model.name.isEmpty, "Model name should not be empty: \(model.id)")
            #expect(!model.description.isEmpty, "Model description should not be empty: \(model.id)")
        }
    }

    @Test("every provider has at least one fast and one standard model")
    func eachProviderHasFastAndStandardModels() {
        for provider in LLMProvider.allCases {
            let tiers = Set(provider.models.map(\.tier))
            #expect(tiers.contains(.fast), "\(provider.displayName) missing fast model")
            #expect(tiers.contains(.standard), "\(provider.displayName) missing standard model")
        }
    }

    @Test("Codable round-trip preserves all fields")
    func codableRoundTrip() throws {
        let original = LLMModel(
            id: "test-model-1",
            name: "Test Model",
            description: "A test model",
            provider: .anthropic,
            tier: .standard
        )
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(LLMModel.self, from: data)
        #expect(decoded.id == original.id)
        #expect(decoded.name == original.name)
        #expect(decoded.description == original.description)
        #expect(decoded.provider == original.provider)
        #expect(decoded.tier == original.tier)
    }

    @Test("Hashable — usable in Set, deduplicates identical models")
    func hashableSetDedup() {
        let model = LLMModel(id: "gpt-4o", name: "GPT-4o", description: "test", provider: .openAI, tier: .standard)
        let set: Set<LLMModel> = [model, model]
        #expect(set.count == 1)
    }

    @Test("Hashable — two models with different ids are distinct in a Set")
    func hashableDistinctModels() {
        let a = LLMModel(id: "model-a", name: "A", description: "desc", provider: .openAI, tier: .fast)
        let b = LLMModel(id: "model-b", name: "B", description: "desc", provider: .openAI, tier: .fast)
        let set: Set<LLMModel> = [a, b]
        #expect(set.count == 2)
    }

    @Test("Hashable — usable as Dictionary key")
    func hashableDictionaryKey() {
        let model = LLMModel(id: "gemini-flash", name: "Flash", description: "fast", provider: .google, tier: .fast)
        var dict: [LLMModel: Int] = [:]
        dict[model] = 42
        #expect(dict[model] == 42)
    }

    @Test("all static models across providers have unique ids")
    func allStaticModelIdsUnique() {
        let allModels = LLMModel.openAIModels + LLMModel.anthropicModels + LLMModel.googleModels
        let ids = allModels.map(\.id)
        let uniqueIds = Set(ids)
        #expect(uniqueIds.count == ids.count, "All static model ids should be unique")
    }
}

// MARK: - OutputMode Tests

@Suite("OutputMode")
struct STOutputModeTests {

    @Test("raw values match expected strings")
    func rawValues() {
        #expect(OutputMode.replace.rawValue == "replace")
        #expect(OutputMode.append.rawValue == "append")
        #expect(OutputMode.prepend.rawValue == "prepend")
    }

    @Test("allCases contains exactly three modes")
    func allCasesCount() {
        #expect(OutputMode.allCases.count == 3)
    }

    @Test("displayName values are correct")
    func displayNames() {
        #expect(OutputMode.replace.displayName == "Replace")
        #expect(OutputMode.append.displayName == "Append")
        #expect(OutputMode.prepend.displayName == "Prepend")
    }

    @Test("Codable round-trip preserves all modes")
    func codableRoundTrip() throws {
        let encoder = JSONEncoder()
        let decoder = JSONDecoder()
        for mode in OutputMode.allCases {
            let data = try encoder.encode(mode)
            let decoded = try decoder.decode(OutputMode.self, from: data)
            #expect(decoded == mode)
        }
    }

    @Test("apply replace returns only the result")
    func applyReplace() {
        let result = OutputMode.replace.apply(original: "hello", result: "world")
        #expect(result == "world")
    }

    @Test("apply append combines original then result with double newline")
    func applyAppend() {
        let result = OutputMode.append.apply(original: "hello", result: "world")
        #expect(result == "hello\n\nworld")
    }

    @Test("apply prepend combines result then original with double newline")
    func applyPrepend() {
        let result = OutputMode.prepend.apply(original: "hello", result: "world")
        #expect(result == "world\n\nhello")
    }

    @Test("apply replace with empty original returns just the result")
    func applyReplaceEmptyOriginal() {
        let result = OutputMode.replace.apply(original: "", result: "output")
        #expect(result == "output")
    }

    @Test("apply replace with empty result returns empty string")
    func applyReplaceEmptyResult() {
        let result = OutputMode.replace.apply(original: "original", result: "")
        #expect(result == "")
    }

    @Test("apply append with empty result appends separator and empty string")
    func applyAppendEmptyResult() {
        let result = OutputMode.append.apply(original: "original", result: "")
        #expect(result == "original\n\n")
    }

    @Test("apply prepend with empty original returns result plus separator")
    func applyPrependEmptyOriginal() {
        let result = OutputMode.prepend.apply(original: "", result: "prepended")
        #expect(result == "prepended\n\n")
    }

    @Test("apply append separator is exactly two newlines")
    func appendSeparatorIsTwoNewlines() {
        let result = OutputMode.append.apply(original: "A", result: "B")
        let components = result.components(separatedBy: "\n\n")
        #expect(components.count == 2)
        #expect(components[0] == "A")
        #expect(components[1] == "B")
    }

    @Test("apply prepend separator is exactly two newlines")
    func prependSeparatorIsTwoNewlines() {
        let result = OutputMode.prepend.apply(original: "A", result: "B")
        let components = result.components(separatedBy: "\n\n")
        #expect(components.count == 2)
        #expect(components[0] == "B")
        #expect(components[1] == "A")
    }
}

// MARK: - PromptItem Tests

@Suite("PromptItem")
struct STPromptItemTests {

    @Test("init assigns a non-nil UUID id")
    func initAssignsId() {
        let item = PromptItem(name: "Test", prompt: "Do something")
        // id is always non-nil (UUID), just verify it round-trips
        let uuidStr = item.id.uuidString
        #expect(!uuidStr.isEmpty)
    }

    @Test("two independently created items have different ids")
    func twoItemsHaveDifferentIds() {
        let a = PromptItem(name: "A", prompt: "pa")
        let b = PromptItem(name: "B", prompt: "pb")
        #expect(a.id != b.id)
    }

    @Test("default modelTier is nil")
    func defaultModelTierIsNil() {
        let item = PromptItem(name: "Test", prompt: "Prompt")
        #expect(item.modelTier == nil)
    }

    @Test("default outputMode is replace")
    func defaultOutputModeIsReplace() {
        let item = PromptItem(name: "Test", prompt: "Prompt")
        #expect(item.outputMode == .replace)
    }

    @Test("explicit modelTier is stored correctly")
    func explicitModelTier() {
        let item = PromptItem(name: "Fast", prompt: "Go fast", modelTier: .fast)
        #expect(item.modelTier == .fast)
    }

    @Test("explicit outputMode is stored correctly")
    func explicitOutputMode() {
        let item = PromptItem(name: "Append", prompt: "Add more", outputMode: .append)
        #expect(item.outputMode == .append)
    }

    @Test("Codable round-trip preserves all fields")
    func codableRoundTrip() throws {
        let original = PromptItem(name: "Round Trip", prompt: "Test prompt", modelTier: .thinking, outputMode: .prepend)
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        #expect(decoded.id == original.id)
        #expect(decoded.name == original.name)
        #expect(decoded.prompt == original.prompt)
        #expect(decoded.modelTier == original.modelTier)
        #expect(decoded.outputMode == original.outputMode)
    }

    @Test("Codable round-trip with nil modelTier preserves nil")
    func codableRoundTripNilTier() throws {
        let original = PromptItem(name: "No Tier", prompt: "Default tier")
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        #expect(decoded.modelTier == nil)
    }

    @Test("decoding JSON without outputMode field defaults to replace")
    func decodingWithoutOutputModeDefaultsToReplace() throws {
        let json = """
        {"id": "00000000-0000-0000-0000-000000000001", "name": "Old", "prompt": "Old text"}
        """
        let data = json.data(using: .utf8)!
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        #expect(decoded.outputMode == .replace)
    }

    @Test("decoding JSON without id field generates a new UUID")
    func decodingWithoutIdGeneratesUUID() throws {
        let json = """
        {"name": "No ID", "prompt": "Some text"}
        """
        let data = json.data(using: .utf8)!
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        #expect(decoded.name == "No ID")
        #expect(!decoded.id.uuidString.isEmpty)
    }

    @Test("decoding JSON without modelTier gives nil tier")
    func decodingWithoutModelTierGivesNil() throws {
        let json = """
        {"id": "00000000-0000-0000-0000-000000000001", "name": "Old Prompt", "prompt": "Old text", "outputMode": "append"}
        """
        let data = json.data(using: .utf8)!
        let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
        #expect(decoded.modelTier == nil)
        #expect(decoded.outputMode == .append)
    }

    @Test("equality is based on id only — different fields, same id are equal")
    func equalityBasedOnId() {
        let item1 = PromptItem(name: "A", prompt: "pa", modelTier: .fast)
        var item2 = item1
        item2.modelTier = .thinking
        item2.name = "Different Name"
        #expect(item1 == item2)
    }

    @Test("items with different ids are not equal")
    func itemsWithDifferentIdsNotEqual() {
        let item1 = PromptItem(name: "Same", prompt: "Same")
        let item2 = PromptItem(name: "Same", prompt: "Same")
        #expect(item1 != item2)
    }

    @Test("all ModelTier values round-trip through PromptItem Codable")
    func allTiersRoundTrip() throws {
        for tier in ModelTier.allCases {
            let item = PromptItem(name: "T", prompt: "p", modelTier: tier)
            let data = try JSONEncoder().encode(item)
            let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
            #expect(decoded.modelTier == tier)
        }
    }

    @Test("all OutputMode values round-trip through PromptItem Codable")
    func allOutputModesRoundTrip() throws {
        for mode in OutputMode.allCases {
            let item = PromptItem(name: "T", prompt: "p", outputMode: mode)
            let data = try JSONEncoder().encode(item)
            let decoded = try JSONDecoder().decode(PromptItem.self, from: data)
            #expect(decoded.outputMode == mode)
        }
    }
}

// MARK: - ProviderTierConfig Tests

@Suite("ProviderTierConfig")
struct STProviderTierConfigTests {

    @Test("default init has all nil model IDs")
    func defaultInitAllNil() {
        let config = ProviderTierConfig()
        #expect(config.fast == nil)
        #expect(config.standard == nil)
        #expect(config.thinking == nil)
    }

    @Test("modelID(for:) returns nil for unconfigured tiers")
    func modelIDForUnconfiguredTiersIsNil() {
        let config = ProviderTierConfig()
        for tier in ModelTier.allCases {
            #expect(config.modelID(for: tier) == nil)
        }
    }

    @Test("setting(_:for:) updates fast tier and is non-mutating")
    func settingFastTier() {
        let config = ProviderTierConfig()
        let updated = config.setting("gpt-4o-mini", for: .fast)
        #expect(updated.fast == "gpt-4o-mini")
        #expect(updated.standard == nil)
        #expect(updated.thinking == nil)
        // original should be unchanged
        #expect(config.fast == nil)
    }

    @Test("setting(_:for:) updates standard tier")
    func settingStandardTier() {
        let config = ProviderTierConfig()
        let updated = config.setting("gpt-4o", for: .standard)
        #expect(updated.standard == "gpt-4o")
        #expect(updated.fast == nil)
        #expect(updated.thinking == nil)
    }

    @Test("setting(_:for:) updates thinking tier")
    func settingThinkingTier() {
        let config = ProviderTierConfig()
        let updated = config.setting("o4-mini", for: .thinking)
        #expect(updated.thinking == "o4-mini")
        #expect(updated.fast == nil)
        #expect(updated.standard == nil)
    }

    @Test("setting(_:for:) with nil clears a previously set model ID")
    func settingNilClearsTier() {
        let config = ProviderTierConfig(fast: "gpt-4o-mini", standard: nil, thinking: nil)
        let updated = config.setting(nil, for: .fast)
        #expect(updated.fast == nil)
    }

    @Test("modelID(for:) returns correct values after chained settings")
    func modelIDAfterChainedSettings() {
        let config = ProviderTierConfig()
            .setting("model-a", for: .fast)
            .setting("model-b", for: .standard)
            .setting("model-c", for: .thinking)
        #expect(config.modelID(for: .fast) == "model-a")
        #expect(config.modelID(for: .standard) == "model-b")
        #expect(config.modelID(for: .thinking) == "model-c")
    }

    @Test("Codable round-trip preserves partial config with nil fields")
    func codableRoundTripWithNils() throws {
        let config = ProviderTierConfig(fast: "gpt-4o-mini", standard: nil, thinking: "o4-mini")
        let data = try JSONEncoder().encode(config)
        let decoded = try JSONDecoder().decode(ProviderTierConfig.self, from: data)
        #expect(decoded.fast == "gpt-4o-mini")
        #expect(decoded.standard == nil)
        #expect(decoded.thinking == "o4-mini")
    }

    @Test("Codable round-trip preserves all-nil default config")
    func codableRoundTripAllNil() throws {
        let config = ProviderTierConfig()
        let data = try JSONEncoder().encode(config)
        let decoded = try JSONDecoder().decode(ProviderTierConfig.self, from: data)
        #expect(decoded == config)
    }

    @Test("Equatable — identical configs are equal")
    func equatableIdentical() {
        let a = ProviderTierConfig(fast: "x", standard: "y", thinking: nil)
        let b = ProviderTierConfig(fast: "x", standard: "y", thinking: nil)
        #expect(a == b)
    }

    @Test("Equatable — configs differing in one field are not equal")
    func equatableDifferentField() {
        let a = ProviderTierConfig(fast: "x", standard: "y", thinking: nil)
        let b = ProviderTierConfig(fast: "x", standard: "z", thinking: nil)
        #expect(a != b)
    }

    @Test("Equatable — nil vs non-nil field makes configs unequal")
    func equatableNilVsNonNil() {
        let a = ProviderTierConfig(fast: "x", standard: nil, thinking: nil)
        let b = ProviderTierConfig(fast: "x", standard: "y", thinking: nil)
        #expect(a != b)
    }
}

// MARK: - ProcessingHistoryEntry Tests

@Suite("ProcessingHistoryEntry")
struct STProcessingHistoryEntryTests {

    @Test("default init uses current date and stores all fields")
    func defaultInitFields() {
        let before = Date()
        let entry = ProcessingHistoryEntry(
            inputText: "in",
            outputText: "out",
            promptName: "formal",
            modelName: "gpt-4o",
            providerName: "OpenAI",
            durationMs: 500
        )
        let after = Date()
        #expect(entry.inputText == "in")
        #expect(entry.outputText == "out")
        #expect(entry.promptName == "formal")
        #expect(entry.modelName == "gpt-4o")
        #expect(entry.providerName == "OpenAI")
        #expect(entry.durationMs == 500)
        #expect(entry.timestamp >= before)
        #expect(entry.timestamp <= after)
    }

    @Test("explicit id is preserved")
    func explicitIdPreserved() {
        let id = UUID()
        let entry = ProcessingHistoryEntry(
            id: id,
            inputText: "in",
            outputText: "out",
            promptName: "p",
            modelName: "m",
            providerName: "prov",
            durationMs: 100
        )
        #expect(entry.id == id)
    }

    @Test("explicit timestamp is preserved")
    func explicitTimestampPreserved() {
        let date = Date(timeIntervalSince1970: 1_700_000_000)
        let entry = ProcessingHistoryEntry(
            timestamp: date,
            inputText: "x",
            outputText: "y",
            promptName: "p",
            modelName: "m",
            providerName: "prov",
            durationMs: 1
        )
        #expect(entry.timestamp == date)
    }

    @Test("Codable round-trip preserves all fields")
    func codableRoundTrip() throws {
        let id = UUID()
        let date = Date(timeIntervalSince1970: 1_700_000_000)
        let original = ProcessingHistoryEntry(
            id: id,
            timestamp: date,
            inputText: "hello world",
            outputText: "Hello, World!",
            promptName: "formal",
            modelName: "claude-sonnet-4",
            providerName: "Anthropic",
            durationMs: 1234
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(original)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let decoded = try decoder.decode(ProcessingHistoryEntry.self, from: data)
        #expect(decoded.id == original.id)
        // ISO8601 may drop sub-second precision; allow 1-second tolerance
        #expect(abs(decoded.timestamp.timeIntervalSince(original.timestamp)) < 1.0)
        #expect(decoded.inputText == original.inputText)
        #expect(decoded.outputText == original.outputText)
        #expect(decoded.promptName == original.promptName)
        #expect(decoded.modelName == original.modelName)
        #expect(decoded.providerName == original.providerName)
        #expect(decoded.durationMs == original.durationMs)
    }

    @Test("equality is based on id only — different content, same id are equal")
    func equalityBasedOnId() {
        let id = UUID()
        let a = ProcessingHistoryEntry(
            id: id, timestamp: Date(timeIntervalSince1970: 1000),
            inputText: "a", outputText: "A",
            promptName: "p", modelName: "m", providerName: "prov", durationMs: 10
        )
        let b = ProcessingHistoryEntry(
            id: id, timestamp: Date(timeIntervalSince1970: 2000),
            inputText: "b", outputText: "B",
            promptName: "q", modelName: "n", providerName: "prov2", durationMs: 99
        )
        #expect(a == b)
    }

    @Test("entries with different ids are not equal")
    func differentIdsNotEqual() {
        let a = ProcessingHistoryEntry(
            inputText: "x", outputText: "y",
            promptName: "p", modelName: "m", providerName: "prov", durationMs: 1
        )
        let b = ProcessingHistoryEntry(
            inputText: "x", outputText: "y",
            promptName: "p", modelName: "m", providerName: "prov", durationMs: 1
        )
        #expect(a != b)
    }

    @Test("durationMs of zero is valid")
    func durationMsZero() {
        let entry = ProcessingHistoryEntry(
            inputText: "", outputText: "",
            promptName: "", modelName: "", providerName: "", durationMs: 0
        )
        #expect(entry.durationMs == 0)
    }

    @Test("large durationMs value is stored accurately")
    func largeDurationMs() {
        let entry = ProcessingHistoryEntry(
            inputText: "x", outputText: "y",
            promptName: "p", modelName: "m", providerName: "prov", durationMs: 999_999
        )
        #expect(entry.durationMs == 999_999)
    }
}

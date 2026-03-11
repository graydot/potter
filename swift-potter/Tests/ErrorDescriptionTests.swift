import Testing
import Foundation
@testable import Potter

// MARK: - PromptServiceError Tests

@Suite("ED.PromptServiceError")
struct EDPromptServiceErrorTests {

    @Test("invalidPromptName errorDescription is non-empty")
    func invalidPromptNameErrorDescription() {
        let err = PromptServiceError.invalidPromptName
        #expect(err.errorDescription?.isEmpty == false)
    }

    @Test("invalidPromptName errorDescription mentions 'empty'")
    func invalidPromptNameMentionsEmpty() {
        let err = PromptServiceError.invalidPromptName
        let desc = err.errorDescription ?? ""
        #expect(desc.lowercased().contains("empty"))
    }

    @Test("invalidPromptContent errorDescription is non-empty")
    func invalidPromptContentErrorDescription() {
        let err = PromptServiceError.invalidPromptContent
        #expect(err.errorDescription?.isEmpty == false)
    }

    @Test("invalidPromptContent errorDescription mentions 'empty'")
    func invalidPromptContentMentionsEmpty() {
        let err = PromptServiceError.invalidPromptContent
        let desc = err.errorDescription ?? ""
        #expect(desc.lowercased().contains("empty"))
    }

    @Test("duplicatePromptName errorDescription is non-empty")
    func duplicatePromptNameErrorDescription() {
        let err = PromptServiceError.duplicatePromptName
        #expect(err.errorDescription?.isEmpty == false)
    }

    @Test("duplicatePromptName errorDescription mentions 'already exists'")
    func duplicatePromptNameMentionsAlreadyExists() {
        let err = PromptServiceError.duplicatePromptName
        let desc = err.errorDescription ?? ""
        #expect(desc.lowercased().contains("already exists"))
    }

    @Test("invalidIndex errorDescription is non-empty")
    func invalidIndexErrorDescription() {
        let err = PromptServiceError.invalidIndex
        #expect(err.errorDescription?.isEmpty == false)
    }

    @Test("cannotDeleteLastPrompt errorDescription is non-empty")
    func cannotDeleteLastPromptErrorDescription() {
        let err = PromptServiceError.cannotDeleteLastPrompt
        #expect(err.errorDescription?.isEmpty == false)
    }

    @Test("cannotDeleteLastPrompt errorDescription mentions 'last'")
    func cannotDeleteLastPromptMentionsLast() {
        let err = PromptServiceError.cannotDeleteLastPrompt
        let desc = err.errorDescription ?? ""
        #expect(desc.lowercased().contains("last"))
    }

    @Test("fileAccessError errorDescription contains underlying error description")
    func fileAccessErrorContainsUnderlying() {
        struct FakeError: LocalizedError {
            var errorDescription: String? { "disk quota exceeded" }
        }
        let err = PromptServiceError.fileAccessError(FakeError())
        let desc = err.errorDescription ?? ""
        #expect(desc.contains("disk quota exceeded"))
    }

    @Test("fileAccessError errorDescription mentions 'file access'")
    func fileAccessErrorMentionsFileAccess() {
        struct FakeError: Error {}
        let err = PromptServiceError.fileAccessError(FakeError())
        let desc = (err.errorDescription ?? "").lowercased()
        #expect(desc.contains("file") || desc.contains("access") || desc.contains("error"))
    }

    @Test("all non-fileAccessError cases produce distinct errorDescriptions")
    func allStaticCasesHaveDistinctDescriptions() {
        let cases: [PromptServiceError] = [
            .invalidPromptName,
            .invalidPromptContent,
            .duplicatePromptName,
            .invalidIndex,
            .cannotDeleteLastPrompt,
        ]
        let descriptions = cases.compactMap { $0.errorDescription }
        let uniqueDescriptions = Set(descriptions)
        #expect(uniqueDescriptions.count == descriptions.count,
                "Each PromptServiceError case should have a unique errorDescription")
    }

    @Test("PromptServiceError conforms to LocalizedError")
    func conformsToLocalizedError() {
        let err: any LocalizedError = PromptServiceError.invalidPromptName
        #expect(err.errorDescription != nil)
    }
}

// MARK: - ModelRegistryError Tests

@Suite("ED.ModelRegistryError")
struct EDModelRegistryErrorTests {

    @Test("fetchFailed errorDescription mentions provider displayName")
    func fetchFailedMentionsProvider() {
        for provider in LLMProvider.allCases {
            let err = ModelRegistryError.fetchFailed(provider: provider)
            let desc = err.errorDescription ?? ""
            #expect(desc.contains(provider.displayName),
                    "fetchFailed errorDescription should mention \(provider.displayName)")
        }
    }

    @Test("fetchFailed errorDescription is non-empty for all providers")
    func fetchFailedNonEmptyForAllProviders() {
        for provider in LLMProvider.allCases {
            let err = ModelRegistryError.fetchFailed(provider: provider)
            #expect(err.errorDescription?.isEmpty == false)
        }
    }

    @Test("multipleFetchesFailed errorDescription contains all description strings")
    func multipleFetchesFailedContainsDescriptions() {
        let descriptions = ["OpenAI: timeout", "Google: unauthorized"]
        let err = ModelRegistryError.multipleFetchesFailed(descriptions: descriptions)
        let desc = err.errorDescription ?? ""
        #expect(desc.contains("OpenAI: timeout"))
        #expect(desc.contains("Google: unauthorized"))
    }

    @Test("multipleFetchesFailed errorDescription with empty list is non-empty")
    func multipleFetchesFailedEmptyList() {
        let err = ModelRegistryError.multipleFetchesFailed(descriptions: [])
        #expect(err.errorDescription?.isEmpty == false)
    }

    @Test("multipleFetchesFailed errorDescription with single description contains it")
    func multipleFetchesFailedSingleDescription() {
        let err = ModelRegistryError.multipleFetchesFailed(descriptions: ["Anthropic: rate limited"])
        let desc = err.errorDescription ?? ""
        #expect(desc.contains("Anthropic: rate limited"))
    }

    @Test("fetchFailed and multipleFetchesFailed have distinct error descriptions")
    func distinctDescriptions() {
        let single = ModelRegistryError.fetchFailed(provider: .openAI).errorDescription
        let multi = ModelRegistryError.multipleFetchesFailed(descriptions: ["x"]).errorDescription
        #expect(single != multi)
    }

    @Test("ModelRegistryError conforms to LocalizedError")
    func conformsToLocalizedError() {
        let err: any LocalizedError = ModelRegistryError.fetchFailed(provider: .anthropic)
        #expect(err.errorDescription != nil)
    }

    @Test("fetchFailed for openAI errorDescription does not mention anthropic")
    func fetchFailedOpenAIDoesNotMentionAnthropic() {
        let err = ModelRegistryError.fetchFailed(provider: .openAI)
        let desc = err.errorDescription ?? ""
        #expect(!desc.contains("Anthropic"))
    }
}

// MARK: - ModelTier.sortOrder Tests
// (sortOrder values confirmed individually — the ordering is tested in ModelRegistryTests.
//  These tests pin the specific numeric values, which are not tested anywhere.)

@Suite("ED.ModelTierSortOrder")
struct EDModelTierSortOrderTests {

    @Test("fast has sortOrder 0")
    func fastSortOrderIsZero() {
        #expect(ModelTier.fast.sortOrder == 0)
    }

    @Test("standard has sortOrder 1")
    func standardSortOrderIsOne() {
        #expect(ModelTier.standard.sortOrder == 1)
    }

    @Test("thinking has sortOrder 2")
    func thinkingSortOrderIsTwo() {
        #expect(ModelTier.thinking.sortOrder == 2)
    }

    @Test("sortOrder values are all distinct")
    func sortOrderValuesDistinct() {
        let orders = ModelTier.allCases.map(\.sortOrder)
        #expect(Set(orders).count == ModelTier.allCases.count)
    }

    @Test("allCases sorted by sortOrder yields fast standard thinking")
    func allCasesSortedBySortOrder() {
        let sorted = ModelTier.allCases.sorted { $0.sortOrder < $1.sortOrder }
        #expect(sorted == [.fast, .standard, .thinking])
    }
}

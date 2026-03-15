import Testing
import Foundation
@testable import Potter

// MARK: - ErrorSeverity Tests

@Suite("PE.ErrorSeverity")
struct PEErrorSeverityTests {

    @Test("allCases contains exactly four severities")
    func allCasesCount() {
        #expect(ErrorSeverity.allCases.count == 4)
    }

    @Test("raw values are correct strings")
    func rawValues() {
        #expect(ErrorSeverity.critical.rawValue == "critical")
        #expect(ErrorSeverity.high.rawValue == "high")
        #expect(ErrorSeverity.medium.rawValue == "medium")
        #expect(ErrorSeverity.low.rawValue == "low")
    }

    @Test("shouldShowAlert is true only for critical and high")
    func shouldShowAlert() {
        #expect(ErrorSeverity.critical.shouldShowAlert == true)
        #expect(ErrorSeverity.high.shouldShowAlert == true)
        #expect(ErrorSeverity.medium.shouldShowAlert == false)
        #expect(ErrorSeverity.low.shouldShowAlert == false)
    }
}

// MARK: - ConfigurationError Tests

@Suite("PE.ConfigurationError")
struct PEConfigurationErrorTests {

    @Test("invalidAPIKey userMessage mentions provider")
    func invalidAPIKeyUserMessage() {
        let err = ConfigurationError.invalidAPIKey(provider: "Anthropic")
        #expect(err.userMessage.contains("Anthropic"))
    }

    @Test("missingAPIKey userMessage mentions provider")
    func missingAPIKeyUserMessage() {
        let err = ConfigurationError.missingAPIKey(provider: "Anthropic")
        #expect(err.userMessage.contains("Anthropic"))
    }

    @Test("missingConfiguration userMessage mentions key")
    func missingConfigurationUserMessage() {
        let err = ConfigurationError.missingConfiguration(key: "llm_provider")
        #expect(err.userMessage.contains("llm_provider"))
    }

    @Test("invalidFormat userMessage mentions field and expected")
    func invalidFormatUserMessage() {
        let err = ConfigurationError.invalidFormat(field: "apiKey", expected: "sk-...")
        #expect(err.userMessage.contains("apiKey"))
        #expect(err.userMessage.contains("sk-..."))
    }

    @Test("unsupportedProvider userMessage mentions provider name")
    func unsupportedProviderUserMessage() {
        let err = ConfigurationError.unsupportedProvider(provider: "cohere")
        #expect(err.userMessage.contains("cohere"))
    }

    @Test("invalidModel userMessage mentions modelId and provider")
    func invalidModelUserMessage() {
        let err = ConfigurationError.invalidModel(modelId: "claude-99", provider: "Anthropic")
        #expect(err.userMessage.contains("claude-99"))
        #expect(err.userMessage.contains("Anthropic"))
    }

    @Test("corruptedSettings userMessage mentions reason")
    func corruptedSettingsUserMessage() {
        let err = ConfigurationError.corruptedSettings(reason: "bad JSON")
        #expect(err.userMessage.contains("bad JSON"))
    }

    @Test("technicalDescription is non-empty for all cases")
    func technicalDescriptionsNonEmpty() {
        let cases: [ConfigurationError] = [
            .invalidAPIKey(provider: "X"),
            .missingAPIKey(provider: "X"),
            .missingConfiguration(key: "k"),
            .invalidFormat(field: "f", expected: "e"),
            .unsupportedProvider(provider: "p"),
            .invalidModel(modelId: "m", provider: "p"),
            .corruptedSettings(reason: "r"),
        ]
        for err in cases {
            #expect(!err.technicalDescription.isEmpty)
        }
    }

    @Test("severity — missingAPIKey is critical")
    func missingAPIKeyIsCritical() {
        #expect(ConfigurationError.missingAPIKey(provider: "X").severity == .critical)
    }

    @Test("severity — invalidAPIKey is high")
    func invalidAPIKeyIsHigh() {
        #expect(ConfigurationError.invalidAPIKey(provider: "X").severity == .high)
    }

    @Test("severity — corruptedSettings is high")
    func corruptedSettingsIsHigh() {
        #expect(ConfigurationError.corruptedSettings(reason: "r").severity == .high)
    }

    @Test("severity — unsupportedProvider and invalidModel are medium")
    func unsupportedProviderAndInvalidModelAreMedium() {
        #expect(ConfigurationError.unsupportedProvider(provider: "p").severity == .medium)
        #expect(ConfigurationError.invalidModel(modelId: "m", provider: "p").severity == .medium)
    }

    @Test("severity — missingConfiguration and invalidFormat are medium")
    func missingConfigAndInvalidFormatAreMedium() {
        #expect(ConfigurationError.missingConfiguration(key: "k").severity == .medium)
        #expect(ConfigurationError.invalidFormat(field: "f", expected: "e").severity == .medium)
    }

    @Test("Equatable — identical cases are equal")
    func equatableIdentical() {
        let a = ConfigurationError.invalidAPIKey(provider: "Anthropic")
        let b = ConfigurationError.invalidAPIKey(provider: "Anthropic")
        #expect(a == b)
    }

    @Test("Equatable — different providers make cases unequal")
    func equatableDifferentProvider() {
        let a = ConfigurationError.invalidAPIKey(provider: "Anthropic")
        let b = ConfigurationError.invalidAPIKey(provider: "Google")
        #expect(a != b)
    }
}

// MARK: - NetworkError Tests

@Suite("PE.NetworkError")
struct PENetworkErrorTests {

    @Test("noInternetConnection userMessage is non-empty")
    func noInternetConnectionUserMessage() {
        #expect(!NetworkError.noInternetConnection.userMessage.isEmpty)
    }

    @Test("timeout userMessage contains duration")
    func timeoutUserMessageContainsDuration() {
        let err = NetworkError.timeout(duration: 30)
        #expect(err.userMessage.contains("30"))
    }

    @Test("serverError userMessage contains statusCode and message when message is non-nil")
    func serverErrorUserMessageWithMessage() {
        let err = NetworkError.serverError(statusCode: 503, message: "Service Unavailable")
        #expect(err.userMessage.contains("503"))
        #expect(err.userMessage.contains("Service Unavailable"))
    }

    @Test("serverError userMessage with nil message mentions statusCode")
    func serverErrorUserMessageWithNilMessage() {
        let err = NetworkError.serverError(statusCode: 502, message: nil)
        #expect(err.userMessage.contains("502"))
    }

    @Test("rateLimited userMessage with retryAfter contains duration")
    func rateLimitedUserMessageWithRetryAfter() {
        let err = NetworkError.rateLimited(retryAfter: 60)
        #expect(err.userMessage.contains("60"))
    }

    @Test("rateLimited userMessage with nil retryAfter is non-empty")
    func rateLimitedUserMessageNoRetryAfter() {
        let err = NetworkError.rateLimited(retryAfter: nil)
        #expect(!err.userMessage.isEmpty)
    }

    @Test("unauthorized userMessage mentions provider")
    func unauthorizedUserMessageMentionsProvider() {
        let err = NetworkError.unauthorized(provider: "Anthropic")
        #expect(err.userMessage.contains("Anthropic"))
    }

    @Test("invalidURL userMessage is non-empty")
    func invalidURLUserMessageNonEmpty() {
        let err = NetworkError.invalidURL(urlString: "not-a-url")
        #expect(!err.userMessage.isEmpty)
    }

    @Test("requestFailed userMessage contains underlying reason")
    func requestFailedUserMessageContainsReason() {
        let err = NetworkError.requestFailed(underlying: "connection reset")
        #expect(err.userMessage.contains("connection reset"))
    }

    @Test("technicalDescription is non-empty for all cases")
    func allTechnicalDescriptionsNonEmpty() {
        let cases: [NetworkError] = [
            .noInternetConnection,
            .timeout(duration: 10),
            .serverError(statusCode: 500, message: "err"),
            .invalidResponse(reason: "bad json"),
            .rateLimited(retryAfter: 5),
            .unauthorized(provider: "X"),
            .invalidURL(urlString: "bad"),
            .requestFailed(underlying: "reset"),
        ]
        for err in cases {
            #expect(!err.technicalDescription.isEmpty)
        }
    }

    @Test("severity — noInternetConnection is critical")
    func noInternetIsCritical() {
        #expect(NetworkError.noInternetConnection.severity == .critical)
    }

    @Test("severity — unauthorized is high")
    func unauthorizedIsHigh() {
        #expect(NetworkError.unauthorized(provider: "X").severity == .high)
    }

    @Test("severity — serverError is high")
    func serverErrorIsHigh() {
        #expect(NetworkError.serverError(statusCode: 500, message: nil).severity == .high)
    }

    @Test("severity — timeout and rateLimited are medium")
    func timeoutAndRateLimitedAreMedium() {
        #expect(NetworkError.timeout(duration: 30).severity == .medium)
        #expect(NetworkError.rateLimited(retryAfter: nil).severity == .medium)
    }

    @Test("severity — invalidResponse invalidURL requestFailed are medium")
    func invalidResponseAndRequestFailedAreMedium() {
        #expect(NetworkError.invalidResponse(reason: "r").severity == .medium)
        #expect(NetworkError.invalidURL(urlString: "u").severity == .medium)
        #expect(NetworkError.requestFailed(underlying: "r").severity == .medium)
    }

    @Test("Equatable — same cases with same params are equal")
    func equatableIdentical() {
        let a = NetworkError.unauthorized(provider: "Google")
        let b = NetworkError.unauthorized(provider: "Google")
        #expect(a == b)
    }

    @Test("Equatable — different providers make unauthorized unequal")
    func equatableDifferentProvider() {
        let a = NetworkError.unauthorized(provider: "Google")
        let b = NetworkError.unauthorized(provider: "Anthropic")
        #expect(a != b)
    }
}

// MARK: - StorageError Tests

@Suite("PE.StorageError")
struct PEStorageErrorTests {

    @Test("userMessage is non-empty for all cases")
    func allUserMessagesNonEmpty() {
        let cases: [StorageError] = [
            .keyNotFound(key: "k"),
            .saveFailed(key: "k", reason: "disk full"),
            .loadFailed(key: "k", reason: "corrupt"),
            .deleteFailed(key: "k", reason: "locked"),
            .keychainUnavailable,
            .migrationFailed(from: "v1", to: "v2", reason: "schema change"),
            .corruptedData(key: "k"),
            .insufficientSpace,
            .permissionDenied(operation: "write"),
        ]
        for err in cases {
            #expect(!err.userMessage.isEmpty)
        }
    }

    @Test("saveFailed technicalDescription mentions key and reason")
    func saveFailedTechnicalDescription() {
        let err = StorageError.saveFailed(key: "myKey", reason: "disk full")
        #expect(err.technicalDescription.contains("myKey"))
        #expect(err.technicalDescription.contains("disk full"))
    }

    @Test("migrationFailed technicalDescription mentions from and to versions")
    func migrationFailedTechnicalDescription() {
        let err = StorageError.migrationFailed(from: "v1", to: "v2", reason: "bad schema")
        #expect(err.technicalDescription.contains("v1"))
        #expect(err.technicalDescription.contains("v2"))
    }

    @Test("severity — migrationFailed and corruptedData are high")
    func migrationAndCorruptedDataAreHigh() {
        #expect(StorageError.migrationFailed(from: "a", to: "b", reason: "r").severity == .high)
        #expect(StorageError.corruptedData(key: "k").severity == .high)
    }

    @Test("severity — keyNotFound and deleteFailed are low")
    func keyNotFoundAndDeleteFailedAreLow() {
        #expect(StorageError.keyNotFound(key: "k").severity == .low)
        #expect(StorageError.deleteFailed(key: "k", reason: "r").severity == .low)
    }

    @Test("Equatable — keychainUnavailable equals itself")
    func keychainUnavailableEquality() {
        #expect(StorageError.keychainUnavailable == StorageError.keychainUnavailable)
    }

    @Test("Equatable — different keys make saveFailed unequal")
    func saveFailedDifferentKeys() {
        let a = StorageError.saveFailed(key: "key1", reason: "r")
        let b = StorageError.saveFailed(key: "key2", reason: "r")
        #expect(a != b)
    }
}

// MARK: - PermissionError Tests

@Suite("PE.PermissionError")
struct PEPermissionErrorTests {

    @Test("userMessage is non-empty for all cases")
    func allUserMessagesNonEmpty() {
        let cases: [PermissionError] = [
            .accessibilityDenied,
            .notificationsDenied,
            .fileSystemDenied(path: "/tmp"),
            .networkDenied,
            .microphoneDenied,
            .cameraDenied,
            .unknownPermission(permission: "contacts"),
        ]
        for err in cases {
            #expect(!err.userMessage.isEmpty)
        }
    }

    @Test("fileSystemDenied userMessage mentions path")
    func fileSystemDeniedMentionsPath() {
        let err = PermissionError.fileSystemDenied(path: "/Users/foo/secret")
        #expect(err.userMessage.contains("/Users/foo/secret"))
    }

    @Test("unknownPermission userMessage mentions permission")
    func unknownPermissionMentionsPermission() {
        let err = PermissionError.unknownPermission(permission: "bluetooth")
        #expect(err.userMessage.contains("bluetooth"))
    }

    @Test("severity — accessibilityDenied is critical")
    func accessibilityDeniedIsCritical() {
        #expect(PermissionError.accessibilityDenied.severity == .critical)
    }

    @Test("severity — notificationsDenied microphoneDenied cameraDenied are low")
    func notificationsAndMediaAreнизкий() {
        #expect(PermissionError.notificationsDenied.severity == .low)
        #expect(PermissionError.microphoneDenied.severity == .low)
        #expect(PermissionError.cameraDenied.severity == .low)
    }

    @Test("severity — fileSystemDenied networkDenied unknownPermission are medium")
    func fileNetworkUnknownAreMedium() {
        #expect(PermissionError.fileSystemDenied(path: "/").severity == .medium)
        #expect(PermissionError.networkDenied.severity == .medium)
        #expect(PermissionError.unknownPermission(permission: "x").severity == .medium)
    }

    @Test("Equatable — accessibilityDenied equals itself")
    func accessibilityDeniedEquality() {
        #expect(PermissionError.accessibilityDenied == PermissionError.accessibilityDenied)
    }

    @Test("Equatable — different paths make fileSystemDenied unequal")
    func fileSystemDeniedDifferentPaths() {
        let a = PermissionError.fileSystemDenied(path: "/a")
        let b = PermissionError.fileSystemDenied(path: "/b")
        #expect(a != b)
    }
}

// MARK: - ValidationError Tests

@Suite("PE.ValidationError")
struct PEValidationErrorTests {

    @Test("emptyInput userMessage mentions field")
    func emptyInputMentionsField() {
        let err = ValidationError.emptyInput(field: "promptName")
        #expect(err.userMessage.contains("promptName"))
    }

    @Test("invalidLength userMessage with both bounds mentions both")
    func invalidLengthBothBounds() {
        let err = ValidationError.invalidLength(field: "password", min: 8, max: 64)
        #expect(err.userMessage.contains("8"))
        #expect(err.userMessage.contains("64"))
    }

    @Test("invalidLength userMessage with only min mentions min")
    func invalidLengthMinOnly() {
        let err = ValidationError.invalidLength(field: "bio", min: 10, max: nil)
        #expect(err.userMessage.contains("10"))
    }

    @Test("invalidLength userMessage with only max mentions max")
    func invalidLengthMaxOnly() {
        let err = ValidationError.invalidLength(field: "name", min: nil, max: 50)
        #expect(err.userMessage.contains("50"))
    }

    @Test("invalidLength userMessage with no bounds is non-empty")
    func invalidLengthNoBounds() {
        let err = ValidationError.invalidLength(field: "field", min: nil, max: nil)
        #expect(!err.userMessage.isEmpty)
    }

    @Test("invalidFormat userMessage mentions field and pattern")
    func invalidFormatMentionsFieldAndPattern() {
        let err = ValidationError.invalidFormat(field: "email", pattern: "x@y.z")
        #expect(err.userMessage.contains("email"))
        #expect(err.userMessage.contains("x@y.z"))
    }

    @Test("invalidCharacters userMessage mentions field and allowed characters")
    func invalidCharactersMentionsAllowed() {
        let err = ValidationError.invalidCharacters(field: "tag", allowedCharacters: "a-z0-9")
        #expect(err.userMessage.contains("tag"))
        #expect(err.userMessage.contains("a-z0-9"))
    }

    @Test("valueOutOfRange userMessage with both bounds mentions both")
    func valueOutOfRangeBothBounds() {
        let err = ValidationError.valueOutOfRange(field: "temperature", min: 0, max: 1)
        #expect(err.userMessage.contains("0.0") || err.userMessage.contains("0"))
        #expect(err.userMessage.contains("1.0") || err.userMessage.contains("1"))
    }

    @Test("valueOutOfRange userMessage with no bounds is non-empty")
    func valueOutOfRangeNoBounds() {
        let err = ValidationError.valueOutOfRange(field: "score", min: nil, max: nil)
        #expect(!err.userMessage.isEmpty)
    }

    @Test("duplicateValue userMessage mentions field and value")
    func duplicateValueMentionsFieldAndValue() {
        let err = ValidationError.duplicateValue(field: "promptName", value: "formal")
        #expect(err.userMessage.contains("promptName"))
        #expect(err.userMessage.contains("formal"))
    }

    @Test("dependencyMissing userMessage mentions field and dependency")
    func dependencyMissingMentionsFieldAndDependency() {
        let err = ValidationError.dependencyMissing(field: "model", dependency: "provider")
        #expect(err.userMessage.contains("model"))
        #expect(err.userMessage.contains("provider"))
    }

    @Test("all cases have non-empty technicalDescription")
    func allTechnicalDescriptionsNonEmpty() {
        let cases: [ValidationError] = [
            .emptyInput(field: "f"),
            .invalidLength(field: "f", min: 1, max: 10),
            .invalidFormat(field: "f", pattern: "p"),
            .invalidCharacters(field: "f", allowedCharacters: "abc"),
            .valueOutOfRange(field: "f", min: 0, max: 100),
            .duplicateValue(field: "f", value: "v"),
            .dependencyMissing(field: "f", dependency: "d"),
        ]
        for err in cases {
            #expect(!err.technicalDescription.isEmpty)
        }
    }

    @Test("severity — emptyInput and dependencyMissing are medium")
    func emptyInputAndDependencyAreMedium() {
        #expect(ValidationError.emptyInput(field: "f").severity == .medium)
        #expect(ValidationError.dependencyMissing(field: "f", dependency: "d").severity == .medium)
    }

    @Test("severity — invalidLength invalidFormat invalidCharacters valueOutOfRange duplicateValue are low")
    func lengthFormatCharactersRangeDuplicateAreLow() {
        #expect(ValidationError.invalidLength(field: "f", min: nil, max: nil).severity == .low)
        #expect(ValidationError.invalidFormat(field: "f", pattern: "p").severity == .low)
        #expect(ValidationError.invalidCharacters(field: "f", allowedCharacters: "abc").severity == .low)
        #expect(ValidationError.valueOutOfRange(field: "f", min: nil, max: nil).severity == .low)
        #expect(ValidationError.duplicateValue(field: "f", value: "v").severity == .low)
    }

    @Test("Equatable — identical cases are equal")
    func equatableIdentical() {
        let a = ValidationError.emptyInput(field: "name")
        let b = ValidationError.emptyInput(field: "name")
        #expect(a == b)
    }

    @Test("Equatable — different fields make emptyInput unequal")
    func equatableDifferentField() {
        let a = ValidationError.emptyInput(field: "name")
        let b = ValidationError.emptyInput(field: "prompt")
        #expect(a != b)
    }
}

// MARK: - SystemError Tests

@Suite("PE.SystemError")
struct PESystemErrorTests {

    @Test("userMessage is non-empty for all cases")
    func allUserMessagesNonEmpty() {
        let cases: [SystemError] = [
            .insufficientMemory,
            .diskSpaceLow,
            .processLimitReached,
            .systemCallFailed(call: "fork", errno: 12),
            .unsupportedVersion(current: "13.0", required: "14.0"),
            .resourceUnavailable(resource: "GPU"),
            .threadingError(reason: "deadlock"),
        ]
        for err in cases {
            #expect(!err.userMessage.isEmpty)
        }
    }

    @Test("systemCallFailed technicalDescription mentions call name and errno")
    func systemCallFailedMentionsCallAndErrno() {
        let err = SystemError.systemCallFailed(call: "mmap", errno: 22)
        #expect(err.technicalDescription.contains("mmap"))
        #expect(err.technicalDescription.contains("22"))
    }

    @Test("unsupportedVersion userMessage mentions both versions")
    func unsupportedVersionMentionsBothVersions() {
        let err = SystemError.unsupportedVersion(current: "12.0", required: "14.0")
        #expect(err.userMessage.contains("12.0"))
        #expect(err.userMessage.contains("14.0"))
    }

    @Test("resourceUnavailable userMessage mentions resource")
    func resourceUnavailableMentionsResource() {
        let err = SystemError.resourceUnavailable(resource: "camera")
        #expect(err.userMessage.contains("camera"))
    }

    @Test("severity — insufficientMemory and processLimitReached are critical")
    func insufficientMemoryAndProcessLimitAreCritical() {
        #expect(SystemError.insufficientMemory.severity == .critical)
        #expect(SystemError.processLimitReached.severity == .critical)
    }

    @Test("severity — diskSpaceLow and unsupportedVersion are high")
    func diskSpaceAndUnsupportedVersionAreHigh() {
        #expect(SystemError.diskSpaceLow.severity == .high)
        #expect(SystemError.unsupportedVersion(current: "a", required: "b").severity == .high)
    }

    @Test("severity — threadingError is high")
    func threadingErrorIsHigh() {
        #expect(SystemError.threadingError(reason: "r").severity == .high)
    }

    @Test("severity — systemCallFailed and resourceUnavailable are medium")
    func systemCallAndResourceAreMedium() {
        #expect(SystemError.systemCallFailed(call: "c", errno: 1).severity == .medium)
        #expect(SystemError.resourceUnavailable(resource: "r").severity == .medium)
    }

    @Test("Equatable — insufficientMemory equals itself")
    func insufficientMemoryEquality() {
        #expect(SystemError.insufficientMemory == SystemError.insufficientMemory)
    }

    @Test("Equatable — different reasons make threadingError unequal")
    func threadingErrorDifferentReasons() {
        let a = SystemError.threadingError(reason: "deadlock")
        let b = SystemError.threadingError(reason: "race condition")
        #expect(a != b)
    }
}

// MARK: - PotterError Top-Level Tests

@Suite("PE.PotterError")
struct PEPotterErrorTests {

    @Test("errorDescription delegates to each sub-error userMessage")
    func errorDescriptionDelegates() {
        let configErr = PotterError.configuration(.missingAPIKey(provider: "Anthropic"))
        #expect(configErr.errorDescription?.contains("Anthropic") == true)

        let netErr = PotterError.network(.unauthorized(provider: "Anthropic"))
        #expect(netErr.errorDescription?.contains("Anthropic") == true)

        let storageErr = PotterError.storage(.keychainUnavailable)
        #expect(storageErr.errorDescription?.isEmpty == false)

        let permErr = PotterError.permission(.accessibilityDenied)
        #expect(permErr.errorDescription?.isEmpty == false)

        let valErr = PotterError.validation(.emptyInput(field: "name"))
        #expect(valErr.errorDescription?.contains("name") == true)

        let sysErr = PotterError.system(.diskSpaceLow)
        #expect(sysErr.errorDescription?.isEmpty == false)
    }

    @Test("technicalDescription is non-empty for each error family")
    func technicalDescriptionNonEmpty() {
        let errors: [PotterError] = [
            .configuration(.invalidAPIKey(provider: "X")),
            .network(.noInternetConnection),
            .storage(.insufficientSpace),
            .permission(.networkDenied),
            .validation(.emptyInput(field: "f")),
            .system(.processLimitReached),
        ]
        for err in errors {
            #expect(!err.technicalDescription.isEmpty)
        }
    }

    @Test("severity delegates to each sub-error severity")
    func severityDelegates() {
        // critical chain
        #expect(PotterError.configuration(.missingAPIKey(provider: "X")).severity == .critical)
        #expect(PotterError.network(.noInternetConnection).severity == .critical)
        #expect(PotterError.permission(.accessibilityDenied).severity == .critical)
        #expect(PotterError.system(.insufficientMemory).severity == .critical)

        // high chain
        #expect(PotterError.configuration(.invalidAPIKey(provider: "X")).severity == .high)
        #expect(PotterError.network(.unauthorized(provider: "X")).severity == .high)

        // low chain
        #expect(PotterError.storage(.keyNotFound(key: "k")).severity == .low)
        #expect(PotterError.validation(.duplicateValue(field: "f", value: "v")).severity == .low)
    }

    @Test("Equatable — same wrapped error is equal")
    func equatableIdentical() {
        let a = PotterError.network(.noInternetConnection)
        let b = PotterError.network(.noInternetConnection)
        #expect(a == b)
    }

    @Test("Equatable — different families are not equal")
    func equatableDifferentFamilies() {
        let a = PotterError.network(.noInternetConnection)
        let b = PotterError.system(.diskSpaceLow)
        #expect(a != b)
    }
}

// MARK: - Result<_, PotterError> Extension Tests

@Suite("PE.Result+PotterError")
struct PEResultExtensionTests {

    @Test("configurationError factory produces correct failure")
    func configurationErrorFactory() {
        let result: Result<Int, PotterError> = .configurationError(.invalidAPIKey(provider: "Anthropic"))
        #expect(result.isFailure)
        if case .failure(.configuration(.invalidAPIKey(let provider))) = result {
            #expect(provider == "Anthropic")
        } else {
            Issue.record("Expected .failure(.configuration(.invalidAPIKey))")
        }
    }

    @Test("networkError factory produces correct failure")
    func networkErrorFactory() {
        let result: Result<String, PotterError> = .networkError(.noInternetConnection)
        #expect(result.isFailure)
        if case .failure(.network(.noInternetConnection)) = result {
            // correct
        } else {
            Issue.record("Expected .failure(.network(.noInternetConnection))")
        }
    }

    @Test("storageError factory produces correct failure")
    func storageErrorFactory() {
        let result: Result<Void, PotterError> = .storageError(.keychainUnavailable)
        #expect(result.isFailure)
        if case .failure(.storage(.keychainUnavailable)) = result {
            // correct
        } else {
            Issue.record("Expected .failure(.storage(.keychainUnavailable))")
        }
    }

    @Test("permissionError factory produces correct failure")
    func permissionErrorFactory() {
        let result: Result<Bool, PotterError> = .permissionError(.accessibilityDenied)
        #expect(result.isFailure)
        if case .failure(.permission(.accessibilityDenied)) = result {
            // correct
        } else {
            Issue.record("Expected .failure(.permission(.accessibilityDenied))")
        }
    }

    @Test("validationError factory produces correct failure")
    func validationErrorFactory() {
        let result: Result<[String], PotterError> = .validationError(.emptyInput(field: "name"))
        #expect(result.isFailure)
        if case .failure(.validation(.emptyInput(let field))) = result {
            #expect(field == "name")
        } else {
            Issue.record("Expected .failure(.validation(.emptyInput))")
        }
    }

    @Test("systemError factory produces correct failure")
    func systemErrorFactory() {
        let result: Result<Data, PotterError> = .systemError(.diskSpaceLow)
        #expect(result.isFailure)
        if case .failure(.system(.diskSpaceLow)) = result {
            // correct
        } else {
            Issue.record("Expected .failure(.system(.diskSpaceLow))")
        }
    }

    @Test("isSuccess is true for .success case")
    func isSuccessForSuccess() {
        let result: Result<Int, PotterError> = .success(42)
        #expect(result.isSuccess == true)
        #expect(result.isFailure == false)
    }

    @Test("isFailure is true for .failure case")
    func isFailureForFailure() {
        let result: Result<Int, PotterError> = .failure(.network(.noInternetConnection))
        #expect(result.isFailure == true)
        #expect(result.isSuccess == false)
    }

    @Test("isSuccess and isFailure are mutually exclusive")
    func isSuccessAndIsFailureMutuallyExclusive() {
        let success: Result<Int, PotterError> = .success(1)
        let failure: Result<Int, PotterError> = .failure(.network(.noInternetConnection))
        #expect(success.isSuccess != success.isFailure)
        #expect(failure.isSuccess != failure.isFailure)
    }
}

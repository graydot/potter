# Potter Test Infrastructure

This document describes the comprehensive automated testing infrastructure for the Potter Swift application.

## Overview

The Potter project includes 600+ automated tests covering every aspect of the application, organized into 8 comprehensive test suites that mirror the manual test scenarios from `manualtests.md`.

## Test Suites

### 1. FirstLaunchTests (T1.x)
- **Purpose**: Initial setup and configuration testing
- **Coverage**: Clean launches, permission handling, API key setup, default settings
- **Key Tests**: First time user experience, settings persistence, provider configuration

### 2. CoreFunctionalityTests (T2.x)  
- **Purpose**: Text processing and LLM integration
- **Coverage**: Clipboard operations, LLM provider switching, prompt management
- **Key Tests**: Basic text processing, multiple providers, custom prompts

### 3. SettingsConfigurationTests (T3.x)
- **Purpose**: Settings management and persistence
- **Coverage**: Hotkey configuration, secure storage, settings persistence  
- **Key Tests**: API key storage methods, hotkey parsing, concurrent access

### 4. ErrorHandlingEdgeCasesTests (T4.x)
- **Purpose**: Error scenarios and edge cases
- **Coverage**: Network issues, invalid keys, large text, clipboard edge cases
- **Key Tests**: Comprehensive error handling validation and recovery

### 5. SystemIntegrationTests (T5.x)
- **Purpose**: Process management and system interaction
- **Coverage**: File system operations, UserDefaults, process ID validation
- **Key Tests**: Multiple instance prevention, menu bar integration, app lifecycle

### 6. AdvancedFeaturesTests (T6.x)
- **Purpose**: Prompt management and diagnostics
- **Coverage**: Large dataset handling, prompt validation, build info consistency
- **Key Tests**: Advanced prompt management, build diagnostics

### 7. PerformanceReliabilityTests (T7.x)
- **Purpose**: Performance and stress testing
- **Coverage**: Memory usage, CPU performance, reliability
- **Key Tests**: Performance benchmarks using XCTest measure blocks

### 8. SecurityPrivacyTests (T8.x)
- **Purpose**: API key security and data protection
- **Coverage**: Secure storage, input sanitization, concurrent security operations
- **Key Tests**: API key security, network security validation

## Running Tests

### Make Targets

```bash
# Run all automated tests (default)
make test

# Run tests with verbose output
make test-verbose

# Clean build artifacts and run tests
make test-clean

# Fast test run for pre-commit checks
make test-fast

# Run only critical tests for quick feedback
make test-critical

# Show all available targets
make help
```

### Direct Swift Commands

```bash
# Run all tests with parallel execution
swift test --parallel

# Run specific test suite
swift test --filter "FirstLaunchTests"

# Run with verbose output
swift test --parallel --verbose

# Run quietly (minimal output)
swift test --quiet
```

### Scripts

```bash
# Quick test runner (critical tests only)
./scripts/quick_test.sh

# Legacy test runner with detailed output
./scripts/run_tests.sh

# Emergency commit without tests (development only)
./scripts/commit_no_verify.sh "commit message"
```

## Pre-commit Hook Integration

### Automatic Test Execution

The pre-commit hook automatically runs the full test suite before allowing commits:

1. **Mandatory Testing**: All tests must pass before commits are allowed
2. **Comprehensive Coverage**: Runs all 8 test suites (600+ individual test methods)
3. **Clear Feedback**: Provides detailed error messages and debugging information
4. **Timeout Protection**: 180-second timeout prevents hanging commits
5. **Helpful Guidance**: Shows commands to debug and fix test failures

### Hook Configuration

The pre-commit hook is located at `.git/hooks/pre-commit` and delegates to `scripts/pre_commit_hook.sh`. Key features:

- **Automatic**: Runs on every `git commit` 
- **Blocking**: Prevents commits when tests fail
- **Informative**: Shows which test suites are being executed
- **Recoverable**: Provides clear instructions for fixing failures

### Bypassing Tests (Development)

For work-in-progress commits or emergencies:

```bash
# Bypass all hooks (use sparingly)
git commit --no-verify -m "WIP: description"

# Use convenience script
./scripts/commit_no_verify.sh "WIP: description"
```

## Test Infrastructure Components

### TestBase.swift
- **Purpose**: Base test class for all test suites
- **Features**: 
  - Automatic keychain access prevention during tests
  - Consistent test setup and cleanup
  - UserDefaults isolation for testing

### Key Testing Patterns

1. **Security Testing**: All tests use `forceUserDefaultsForTesting = true` to prevent keychain prompts
2. **Isolation**: Each test creates temporary directories and cleans up after itself
3. **Performance**: Uses XCTest's `measure` blocks for timing validation
4. **Concurrency**: Tests async/await patterns and concurrent operations
5. **Comprehensive Coverage**: Every manual test scenario has corresponding automated tests

### Test Environment Setup

```swift
class TestBase: XCTestCase {
    override class func setUp() {
        super.setUp()
        SecureAPIKeyStorage.shared.forceUserDefaultsForTesting = true
    }
    
    override func setUp() {
        super.setUp()
        SecureAPIKeyStorage.shared.forceUserDefaultsForTesting = true
        clearTestUserDefaults()
    }
}
```

## Development Workflow

### Recommended Workflow

1. **Development**: Use `make test-critical` for quick feedback during development
2. **Pre-commit**: Full test suite runs automatically via pre-commit hook
3. **Debugging**: Use `make test-verbose` for detailed test output
4. **CI/CD**: Use `make test` in continuous integration pipelines

### Test-Driven Development

1. Write failing test first
2. Implement minimum code to pass
3. Run `make test-critical` for quick validation
4. Refactor with confidence
5. Full test suite validates on commit

### Performance Considerations

- **Full Test Suite**: ~3 minutes (600+ tests across 8 suites)
- **Critical Tests**: ~30 seconds (3 essential test suites)
- **Fast Tests**: ~1 minute (quiet mode, no parallel execution)

## Troubleshooting

### Common Issues

1. **Keychain Prompts**: Ensure `TestBase` is inherited and `forceUserDefaultsForTesting` is set
2. **File Permissions**: Some tests require temporary file creation
3. **Process Management**: System integration tests may have platform-specific limitations
4. **UserNotifications**: Framework crashes in test environment (expected limitation)

### Debugging Failed Tests

```bash
# Run specific failing test with verbose output
swift test --filter "FailingTestName" --verbose

# Check full test output from pre-commit hook
cat /tmp/swift_test_output.log

# Run tests in Xcode for debugging
swift package generate-xcodeproj
open Potter.xcodeproj
```

## Metrics

- **Total Test Methods**: 600+
- **Test Suites**: 8 comprehensive suites
- **Coverage Areas**: All manual test scenarios from T1.x through T8.x
- **Execution Time**: ~3 minutes for full suite
- **Success Rate**: 95%+ (some system integration limitations expected)

## Maintenance

### Adding New Tests

1. Identify appropriate test suite based on functionality
2. Inherit from `TestBase` for proper setup
3. Follow existing naming conventions (`testFeatureDescription`)
4. Include setup/teardown as needed
5. Add to relevant manual test documentation

### Updating Tests

1. Keep tests synchronized with code changes
2. Update test documentation when test scenarios change
3. Maintain consistent testing patterns across suites
4. Review performance impact of new tests

## Integration with CLAUDE.md

The testing infrastructure is integrated with the project's CLAUDE.md instructions:

- **Run tests**: `python run_tests.py` (legacy) or `cd swift-potter && swift test`
- **Swift tests**: `cd swift-potter && swift test --parallel`
- **Make targets**: All test commands available via Makefile

This comprehensive testing infrastructure ensures Potter maintains high quality and reliability across all features and use cases.
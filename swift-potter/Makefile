# Potter Swift App Makefile
# Provides convenient build and test targets

.PHONY: test test-verbose test-clean test-fast test-critical build clean help

# Default target
all: build

# Run all automated tests
test:
	@echo "🧪 Running automated test suites..."
	@swift test --parallel

# Run tests with verbose output
test-verbose:
	@echo "🧪 Running automated test suites (verbose)..."
	@swift test --parallel --verbose

# Clean and run tests
test-clean:
	@echo "🧹 Cleaning and running tests..."
	@swift package clean
	@swift test --parallel

# Fast test run (no parallel, minimal output) for pre-commit hooks
test-fast:
	@echo "⚡ Running fast test check..."
	@swift test --quiet

# Run only critical tests for quick development workflow
test-critical:
	@echo "⚡ Running critical tests only..."
	@../scripts/quick_test.sh

# Run tests using the shell script (legacy)
test-script:
	@chmod +x run_tests.sh
	@./run_tests.sh

# Build the project
build:
	@echo "🔨 Building Potter..."
	@swift build

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@swift package clean

# Generate Xcode project (if needed)
xcode:
	@echo "📱 Generating Xcode project..."
	@swift package generate-xcodeproj

# Show available targets
help:
	@echo "Potter Swift App - Available Make targets:"
	@echo ""
	@echo "  test         - Run all automated tests (default test target)"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  test-clean   - Clean build artifacts and run tests"
	@echo "  test-fast    - Fast test run for pre-commit checks"
	@echo "  test-critical- Run only critical tests for quick feedback"
	@echo "  test-script  - Run tests using legacy shell script"
	@echo "  build        - Build the project"
	@echo "  clean        - Clean build artifacts"
	@echo "  xcode        - Generate Xcode project"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Test Coverage:"
	@echo "  • FirstLaunchTests - Initial setup and configuration"
	@echo "  • CoreFunctionalityTests - Text processing and LLM integration"
	@echo "  • SettingsConfigurationTests - Settings management and persistence"
	@echo "  • ErrorHandlingEdgeCasesTests - Error scenarios and edge cases"
	@echo "  • SystemIntegrationTests - Process management and system interaction"
	@echo "  • AdvancedFeaturesTests - Prompt management and diagnostics"
	@echo "  • PerformanceReliabilityTests - Performance and stress testing"
	@echo "  • SecurityPrivacyTests - API key security and data protection"
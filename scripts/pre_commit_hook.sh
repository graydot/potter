#!/bin/bash
# Potter Pre-commit Hook Script
# This script runs comprehensive tests before allowing commits

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

echo "$(blue '🔍 Potter Pre-commit Hook')"
echo "Running comprehensive tests..."

# Track test results
TESTS_PASSED=true

# Check if we're in Swift potter directory
if [[ -f "swift-potter/Package.swift" ]]; then
    echo "$(blue '🧪 Running Swift automated test suites...')"
    cd swift-potter
    
    # Run tests with timeout and capture output
    echo "$(yellow 'Testing 8 comprehensive test suites:')"
    echo "• FirstLaunchTests - Initial setup and configuration"
    echo "• CoreFunctionalityTests - Text processing and LLM integration"
    echo "• SettingsConfigurationTests - Settings management and persistence"
    echo "• ErrorHandlingEdgeCasesTests - Error scenarios and edge cases"
    echo "• SystemIntegrationTests - Process management and system interaction"
    echo "• AdvancedFeaturesTests - Prompt management and diagnostics"
    echo "• PerformanceReliabilityTests - Performance and stress testing"
    echo "• SecurityPrivacyTests - API key security and data protection"
    echo ""
    
    # Use make test for consistency with developer workflow
    if timeout 180 make test > /tmp/swift_test_output.log 2>&1; then
        echo "$(green '✅ All Swift tests passed!')"
        
        # Show test summary
        TOTAL_TESTS=$(grep -o "Testing PotterTests\." /tmp/swift_test_output.log | wc -l)
        if [[ $TOTAL_TESTS -gt 0 ]]; then
            echo "$(green "📊 Executed $TOTAL_TESTS individual test methods across 8 test suites")"
        fi
    else
        echo "$(red '❌ Swift tests failed!')"
        echo "$(red 'Cannot proceed with commit until tests pass.')"
        echo ""
        echo "$(yellow 'Test output:')"
        tail -n 20 /tmp/swift_test_output.log
        echo ""
        echo "$(yellow 'To see full test output:')"
        echo "$(yellow 'cat /tmp/swift_test_output.log')"
        echo ""
        echo "$(yellow 'To run tests manually:')"
        echo "$(yellow 'make test')"
        
        TESTS_PASSED=false
    fi
    
    cd ..
    
    # Clean up log file
    rm -f /tmp/swift_test_output.log
else
    echo "$(yellow '⚠️ Swift Potter directory not found, skipping Swift tests')"
fi

# Exit with error if tests failed
if [[ "$TESTS_PASSED" != "true" ]]; then
    echo "$(red '❌ Pre-commit hook failed due to test failures')"
    echo "$(red 'Fix the failing tests before committing')"
    exit 1
fi

# Check for Swift file changes to offer release creation
SWIFT_CHANGED=$(git diff --cached --name-only | grep -E '\.(swift)$' | wc -l)

if [[ $SWIFT_CHANGED -gt 0 ]]; then
    echo "$(yellow '📦 Swift files changed.')"
    read -p "$(yellow 'Create a GitHub release? (y/N): ')" CREATE_RELEASE
    
    if [[ "$CREATE_RELEASE" =~ ^[Yy]$ ]]; then
        echo "$(blue '🚀 Creating GitHub release...')"
        if ./scripts/create_github_release.sh; then
            echo "$(green '✅ Release created successfully!')"
        else
            echo "$(red '❌ Release creation failed')"
            echo "Commit will proceed, but please check the release manually"
        fi
    fi
fi

echo "$(green '✅ Pre-commit hook completed successfully')" 
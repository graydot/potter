#!/bin/bash
# Quick Test Runner
# Runs only the most critical tests for faster development workflow

# Color output functions
red() { echo -e "\033[31m$1\033[0m"; }
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
blue() { echo -e "\033[34m$1\033[0m"; }

echo "$(blue '⚡ Quick Test Runner')"
echo "Running essential tests only..."

cd swift-potter

# Run specific test suites that are most likely to catch critical issues
CRITICAL_TESTS=(
    "FirstLaunchTests"
    "CoreFunctionalityTests" 
    "ErrorHandlingEdgeCasesTests"
)

echo "$(yellow 'Testing critical components:')"
for test in "${CRITICAL_TESTS[@]}"; do
    echo "• $test"
done
echo ""

TESTS_PASSED=true

for test in "${CRITICAL_TESTS[@]}"; do
    echo "$(blue "Testing $test...")"
    if swift test --filter "$test" --quiet; then
        echo "$(green "✅ $test passed")"
    else
        echo "$(red "❌ $test failed")"
        TESTS_PASSED=false
    fi
done

echo ""
if [[ "$TESTS_PASSED" == "true" ]]; then
    echo "$(green '✅ All critical tests passed!')"
    echo "$(yellow 'To run full test suite: make test')"
    exit 0
else
    echo "$(red '❌ Critical tests failed!')"
    echo "$(yellow 'Run full test suite for details: make test')"
    exit 1
fi
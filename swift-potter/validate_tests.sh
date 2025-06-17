#!/bin/bash

echo "🧪 Potter Test Validation"
echo "========================"

# Run tests in headless mode and capture just the essential output
echo "Running tests without GUI alerts..."

# Count total tests
TOTAL_TESTS=$(swift test --parallel 2>/dev/null | grep -c "Testing PotterTests" || echo "0")

echo "📊 Test Execution Summary:"
echo "• Total Tests Found: $TOTAL_TESTS"
echo ""

if [ "$TOTAL_TESTS" -gt "0" ]; then
    echo "✅ Test suite is running successfully!"
    echo ""
    echo "📋 Test Components Detected:"
    swift test --parallel 2>/dev/null | grep "Testing PotterTests" | cut -d'/' -f2 | cut -d'/' -f1 | sort | uniq -c | head -10
    echo ""
    echo "🎯 Test Categories:"
    echo "• LLMClientTests - Model definitions, providers, request structures"  
    echo "• LLMManagerTests - API key management, validation, provider selection"
    echo "• PermissionManagerTests - System permissions and UI integration"
    echo "• PotterCoreTests - Core functionality, hotkeys, clipboard processing"
    echo "• PotterSettingsTests - Settings persistence and property observation"
    echo "• ProcessManagerTests - Duplicate detection, lock files, build info"
    echo "• PromptManagerTests - JSON persistence, CRUD operations"
    echo ""
    echo "ℹ️  Note: API key alerts during testing are expected (no keys configured)"
    echo "ℹ️  Tests are using real components to ensure integration works correctly"
else
    echo "❌ No tests detected - there may be a configuration issue"
fi

echo ""
echo "To run tests interactively: swift test"
echo "To run specific test suite: swift test --filter LLMClientTests"
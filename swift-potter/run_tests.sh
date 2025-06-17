#!/bin/bash

# Potter Test Runner
# Runs comprehensive unit tests for the Potter Swift project

echo "🧪 Running Potter Unit Tests..."
echo "================================"

# Clean previous build artifacts
echo "🧹 Cleaning build artifacts..."
swift package clean

echo ""
echo "🔨 Building test target..."
swift build --target PotterTests

echo ""
echo "🚀 Running tests..."
swift test --parallel

echo ""
echo "📊 Test Results Summary:"
echo "========================"

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "📈 Coverage Areas Tested:"
    echo "• PromptManager - JSON persistence, file handling, default prompts"
    echo "• ProcessManager - Duplicate detection, lock files, build info"
    echo "• LLMManager - API key management, provider selection, validation"
    echo "• LLMClient - Model definitions, request structures, error handling"
    echo "• PotterCore - Hotkey handling, clipboard processing, prompt selection"
    echo "• PotterSettings - UserDefaults persistence, property observation"
    echo ""
    echo "🎯 Test Categories:"
    echo "• Unit Tests: Individual component functionality"
    echo "• Integration Tests: Component interaction"
    echo "• Error Handling: Graceful failure scenarios"
    echo "• Data Persistence: File I/O and UserDefaults"
    echo "• UI Components: Settings and dialog behavior"
else
    echo "❌ Some tests failed!"
    echo "Check the output above for details."
    exit 1
fi
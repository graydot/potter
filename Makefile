# Potter - AI Text Processing Tool for macOS
# Makefile for building, testing, and distributing Potter

.PHONY: help run build test clean install publish-github publish-appstore swift-test

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Help target
help: ## Show this help message
	@echo "Potter Build System"
	@echo "=================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make run          # Run the Swift app in development mode"
	@echo "  make build        # Build signed app bundle and DMG"
	@echo "  make test         # Run all tests (Swift)"
	@echo "  make publish      # Publish to GitHub releases"

# Development
run: ## Run the Swift Potter app in development mode
	@echo "$(GREEN)🚀 Running Swift Potter in development mode...$(NC)"
	cd swift-potter && swift run

debug: ## Run the Swift app with verbose logging
	@echo "$(GREEN)🐛 Running Swift Potter with debug logging...$(NC)"
	cd swift-potter && swift run --verbose

# Building
build: ## Build signed Potter.app bundle with DMG (local distribution)
	@echo "$(GREEN)🔨 Building Potter.app with code signing and DMG...$(NC)"
	python3 scripts/build_app.py --target local

build-unsigned: ## Build unsigned Potter.app (for testing without certificates)
	@echo "$(YELLOW)⚠️  Building unsigned Potter.app (testing only)...$(NC)"
	python3 scripts/build_app.py --target local --skip-tests

# Testing
test: swift-test ## Run all tests

swift-test: ## Run Swift test suite
	@echo "$(GREEN)🧪 Running Swift tests...$(NC)"
	cd swift-potter && swift test --parallel

swift-test-verbose: ## Run Swift tests with verbose output
	@echo "$(GREEN)🧪 Running Swift tests (verbose)...$(NC)"
	cd swift-potter && swift test --parallel --verbose

swift-test-clean: ## Clean and run Swift tests
	@echo "$(GREEN)🧹 Cleaning and running Swift tests...$(NC)"
	cd swift-potter && swift package clean && swift test --parallel

swift-test-fast: ## Fast Swift test run for pre-commit checks
	@echo "$(GREEN)⚡ Running fast Swift test check...$(NC)"
	cd swift-potter && swift test --quiet

# Publishing
publish: publish-github ## Alias for GitHub publish

publish-github: build ## Build and publish to GitHub releases
	@echo "$(GREEN)📦 Publishing to GitHub releases...$(NC)"
	./scripts/create_github_release.sh

publish-appstore: ## Build and submit to Mac App Store
	@echo "$(GREEN)🍎 Building for Mac App Store...$(NC)"
	python3 scripts/build_app.py --target appstore
	@echo "$(YELLOW)📤 Please manually upload to App Store Connect$(NC)"

# Installation and cleanup
install: build ## Build and install Potter.app to /Applications
	@echo "$(GREEN)📲 Installing Potter.app to /Applications...$(NC)"
	@if [ -d "dist/Potter.app" ]; then \
		sudo cp -r dist/Potter.app /Applications/; \
		echo "$(GREEN)✅ Potter.app installed successfully$(NC)"; \
	else \
		echo "$(RED)❌ Potter.app not found. Run 'make build' first.$(NC)"; \
		exit 1; \
	fi

uninstall: ## Remove Potter.app from /Applications
	@echo "$(YELLOW)🗑️  Removing Potter.app from /Applications...$(NC)"
	@if [ -d "/Applications/Potter.app" ]; then \
		sudo rm -rf /Applications/Potter.app; \
		echo "$(GREEN)✅ Potter.app uninstalled$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Potter.app not found in /Applications$(NC)"; \
	fi

clean: ## Clean build artifacts and temporary files
	@echo "$(GREEN)🧹 Cleaning build artifacts...$(NC)"
	rm -rf dist/
	rm -rf swift-potter/.build/
	rm -rf build/
	rm -f *.dmg
	rm -f *.zip
	rm -f dmg_background*.png
	rm -f entitlements_*.plist
	@echo "$(GREEN)✅ Clean complete$(NC)"

# Development utilities
deps: ## Check and install dependencies
	@echo "$(GREEN)📦 Checking dependencies...$(NC)"
	@which python3 >/dev/null || (echo "$(RED)❌ Python 3 not found$(NC)" && exit 1)
	@which swift >/dev/null || (echo "$(RED)❌ Swift not found$(NC)" && exit 1)
	@echo "$(GREEN)✅ All dependencies found$(NC)"

setup: deps ## Setup development environment
	@echo "$(GREEN)⚙️  Setting up development environment...$(NC)"
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		echo "$(GREEN)📦 Created virtual environment$(NC)"; \
	fi
	@echo "$(YELLOW)💡 Run 'source .venv/bin/activate' to activate virtual environment$(NC)"

dmg: build ## Create DMG from existing build (requires prior build)
	@echo "$(GREEN)💿 Creating DMG...$(NC)"
	@if [ -d "dist/Potter.app" ]; then \
		echo "$(GREEN)📦 DMG should have been created during build$(NC)"; \
		ls -la dist/*.dmg 2>/dev/null || echo "$(YELLOW)⚠️  No DMG found, rebuilding...$(NC)"; \
	else \
		echo "$(RED)❌ No Potter.app found. Run 'make build' first.$(NC)"; \
		exit 1; \
	fi

# Information
info: ## Show build and system information
	@echo "Potter Build Information"
	@echo "======================="
	@echo "Swift version: $$(swift --version | head -1)"
	@echo "Python version: $$(python3 --version)"
	@echo "macOS version: $$(sw_vers -productVersion)"
	@echo "Build target: Swift Potter"
	@echo ""
	@echo "Build artifacts:"
	@ls -la dist/ 2>/dev/null || echo "  No build artifacts found"

status: ## Show git status and recent changes
	@echo "$(GREEN)📊 Repository Status$(NC)"
	@echo "==================="
	@git status --short
	@echo ""
	@echo "$(GREEN)📝 Recent commits:$(NC)"
	@git log --oneline -5

# Release preparation
version: ## Show current version information
	@echo "$(GREEN)📋 Version Information$(NC)"
	@echo "====================="
	@grep -n "version.*2\.0" scripts/build_app.py swift-potter/Sources/ProcessManager.swift || echo "Version strings found"
	@echo ""
	@echo "DMG name will be: Potter-2.0.dmg"

# Continuous Integration helpers
ci-test: ## Run tests suitable for CI environment
	@echo "$(GREEN)🤖 Running CI tests...$(NC)"
	cd swift-potter && swift test

ci-build: ## Build without code signing (for CI)
	@echo "$(GREEN)🤖 Building for CI (no signing)...$(NC)"
	python3 scripts/build_app.py --target local --skip-tests

# Advanced targets
lint: ## Run code style checks
	@echo "$(GREEN)📝 Running code style checks...$(NC)"
	@echo "$(YELLOW)💡 Swift formatting check:$(NC)"
	cd swift-potter && swift format --lint Sources/ Tests/ || echo "Consider running: swift format --in-place Sources/ Tests/"

format: ## Format Swift code
	@echo "$(GREEN)✨ Formatting Swift code...$(NC)"
	cd swift-potter && swift format --in-place Sources/ Tests/

# Documentation
docs: ## Open relevant documentation
	@echo "$(GREEN)📚 Opening documentation...$(NC)"
	@echo "Build documentation: file://$(PWD)/docs/"
	@open docs/ 2>/dev/null || echo "$(YELLOW)💡 Documentation available in docs/ directory$(NC)"

# Quick commands for common workflows
dev: run ## Alias for run (development mode)
all: clean build test ## Clean, build, and test everything
release: ## Create a new release with auto-update support (with version bump)
	@echo "$(GREEN)🚀 Creating new Potter release...$(NC)"
	python3 scripts/release_manager.py

old-release: clean build publish ## Complete release workflow (legacy)
quick: build-unsigned ## Quick build without signing (for testing)

# Auto-update testing
test-autoupdate: ## Set up auto-update testing environment
	@echo "$(GREEN)🧪 Setting up auto-update testing...$(NC)"
	python3 scripts/test_autoupdate.py

test-release: ## Test release process without GitHub upload
	@echo "$(GREEN)🧪 Testing release process...$(NC)"
	python3 scripts/release_manager.py --skip-github --version 2.0.1 --notes "Test release"
# Potter - AI Text Processing Tool for macOS

.PHONY: help run build dmg release test clean install version
.DEFAULT_GOAL := help

GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

help: ## Show this help message
	@echo "Potter Build System"
	@echo "=================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make run              # Run in development mode"
	@echo "  make dmg              # Build unsigned DMG for sharing"
	@echo "  make build            # Build signed app (requires certs)"
	@echo "  make release          # Full release to GitHub"

# ── Development ────────────────────────────────────────────────

run: ## Run the app in development mode
	@echo "$(GREEN)🚀 Running Potter...$(NC)"
	cd swift-potter && swift run

debug: ## Run with verbose logging
	@echo "$(GREEN)🐛 Running Potter (debug)...$(NC)"
	cd swift-potter && swift run --verbose

# ── Testing ────────────────────────────────────────────────────

test: ## Run all tests
	@echo "$(GREEN)🧪 Running tests...$(NC)"
	cd swift-potter && swift test --parallel

test-verbose: ## Run tests with verbose output
	cd swift-potter && swift test --parallel --verbose

test-clean: ## Clean build cache and run tests
	cd swift-potter && swift package clean && swift test --parallel

# ── Building ───────────────────────────────────────────────────

build: ## Build signed Potter.app + DMG (requires Developer ID certs)
	@echo "$(GREEN)🔨 Building signed Potter.app + DMG...$(NC)"
	python3 scripts/build_app.py --target local --skip-tests

build-unsigned: ## Build unsigned Potter.app (no certs needed)
	@echo "$(YELLOW)⚠️  Building unsigned Potter.app...$(NC)"
	python3 scripts/build_app.py --target local --unsigned --skip-tests --no-dmg

dmg: ## Build unsigned DMG for local sharing (no certs needed)
	@echo "$(GREEN)💿 Building unsigned DMG...$(NC)"
	python3 scripts/build_app.py --target local --unsigned --skip-tests

build-appstore: ## Build for Mac App Store (requires App Store certs)
	@echo "$(GREEN)🍎 Building for App Store...$(NC)"
	python3 scripts/build_app.py --target appstore --skip-tests

# ── Release ────────────────────────────────────────────────────

release: ## Create GitHub release (bump version, build, sign, notarize, upload)
	@echo "$(GREEN)🚀 Creating new release...$(NC)"
	python3 scripts/release_manager.py --bump patch

release-appstore: build-appstore ## Build and prepare for App Store submission
	@echo "$(GREEN)🍎 App Store build ready!$(NC)"
	@echo "$(YELLOW)📤 Upload to App Store Connect using Xcode or Transporter$(NC)"

# ── Version ────────────────────────────────────────────────────

version: ## Show current version
	@python3 scripts/version_manager.py --get

version-set: ## Set version (usage: make version-set VERSION=X.Y.Z)
	@if [ -z "$(VERSION)" ]; then echo "$(RED)Usage: make version-set VERSION=X.Y.Z$(NC)"; exit 1; fi
	@python3 scripts/version_manager.py --set $(VERSION)

version-bump-major: ## Bump major version (X.0.0)
	@python3 scripts/version_manager.py --bump major

version-bump-minor: ## Bump minor version (X.Y.0)
	@python3 scripts/version_manager.py --bump minor

version-bump-patch: ## Bump patch version (X.Y.Z)
	@python3 scripts/version_manager.py --bump patch

# ── Utilities ──────────────────────────────────────────────────

install: build ## Build and install to /Applications
	@echo "$(GREEN)📲 Installing Potter.app...$(NC)"
	@if [ -d "dist/Potter.app" ]; then \
		sudo cp -r dist/Potter.app /Applications/; \
		echo "$(GREEN)✅ Installed to /Applications$(NC)"; \
	else \
		echo "$(RED)❌ dist/Potter.app not found$(NC)"; exit 1; \
	fi

uninstall: ## Remove from /Applications
	@sudo rm -rf /Applications/Potter.app && echo "$(GREEN)✅ Uninstalled$(NC)" || echo "$(YELLOW)Not found$(NC)"

clean: ## Remove all build artifacts
	rm -rf dist/ build/ swift-potter/.build/ *.dmg *.zip

info: ## Show build environment info
	@echo "Swift: $$(swift --version | head -1)"
	@echo "Python: $$(python3 --version)"
	@echo "macOS: $$(sw_vers -productVersion)"
	@python3 scripts/version_manager.py --get
	@ls -la dist/ 2>/dev/null || echo "No build artifacts"

check-signing: ## Diagnose code signing certificate setup
	@bash scripts/test_codesigning.sh

lint: ## Check Swift code style
	cd swift-potter && swift format --lint Sources/ Tests/ || echo "Run 'make format' to fix"

format: ## Format Swift code
	cd swift-potter && swift format --in-place Sources/ Tests/

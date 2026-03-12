# CLAUDE.md

## Commands

### Development
- **Run app**: `cd swift-potter && swift run` or `make run`
- **Run tests**: `cd swift-potter && swift test --parallel` or `make test`

### Building
- **Build .app (unsigned)**: `make build` — builds Potter.app to `dist/`
- **Build signed .app**: `make build` (requires `DEVELOPER_ID_APPLICATION` + `APPLE_TEAM_ID` env vars)
- **Create DMG**: `make dmg` — builds app + creates distributable DMG in `dist/`
- **App Store build**: `make build-appstore` — sandboxed build with App Store entitlements

### Release
- **GitHub release**: `make release` — bump version, build, sign, notarize, create DMG, upload to GitHub
- **App Store release**: `make release-appstore` — build + prepare for App Store Connect upload

### Version Management
- `make version` / `make version-set VERSION=x.y.z`
- `make version-bump-major` / `make version-bump-minor` / `make version-bump-patch`

## Project Overview

Potter is a macOS menu bar app for AI-powered text processing via global hotkeys (Cmd+Shift+9). Captures selected text system-wide, sends it to an LLM (OpenAI/Anthropic/Gemini), and replaces with the result.

- **Platform**: macOS 13+, Swift 5.9, SwiftUI + AppKit
- **Build**: Swift Package Manager, single executable target
- **Dependencies**: Sparkle 2.6.0 (auto-updates)
- **Distribution**: Direct (Developer ID signed) + Mac App Store

## Architecture

```
swift-potter/
├── Package.swift
├── Sources/
│   ├── main.swift                    # Entry point, AppDelegate, menu bar setup
│   ├── Protocols.swift               # Protocol definitions for DI
│   ├── PotterCore.swift              # Thin coordinator (DI-enabled)
│   ├── TextProcessor.swift           # Text processing pipeline (testable)
│   ├── HotkeyCoordinator.swift       # Carbon Event API hotkey (direct distribution)
│   ├── NSEventHotkeyProvider.swift   # NSEvent hotkey (App Store / sandbox)
│   ├── HotkeyKeyMapping.swift        # Shared key code/modifier mapping
│   ├── LLMManager.swift              # Multi-provider LLM orchestration
│   ├── LLMClient.swift               # LLMClient protocol + 3 implementations
│   ├── APIKeyService.swift           # API key validation and state tracking
│   ├── StorageAdapter.swift          # Abstract storage with StorageBackend protocol
│   ├── PromptService.swift           # Prompt CRUD with JSON persistence + caching
│   ├── MenuBarManager.swift          # NSStatusBar icon, menu, icon state machine
│   ├── ModernSettingsWindow.swift    # Settings window shell + sidebar navigation
│   ├── PromptItem.swift              # Prompt data model (shared across app + tests)
│   ├── SettingsHelpers.swift         # App-wide settings utilities (menu update, data reset)
│   ├── GeneralSettingsView.swift     # General settings tab
│   ├── PromptsSettingsView.swift     # Prompts tab with CRUD
│   ├── UpdatesSettingsView.swift     # Updates tab (Sparkle integration)
│   ├── AboutSettingsView.swift       # About tab + data management
│   ├── LogsSettingsView.swift        # Log viewer tab
│   ├── HotkeySettingsView.swift      # Hotkey capture/configuration view
│   ├── PromptEditDialog.swift        # Modal prompt editor
│   ├── LLMProviderView.swift         # Provider selection UI
│   ├── LLMProviderViewModel.swift    # Provider view model
│   ├── PermissionsView.swift         # Permissions + HotkeyView wrapper
│   ├── PermissionManager.swift       # Accessibility permission monitoring
│   ├── ProcessManager.swift          # Duplicate instance detection via lock files
│   ├── AutoUpdateManager.swift       # Auto-update via Sparkle
│   ├── OnboardingWindow.swift        # First-run experience
│   ├── SecuritySanitizer.swift       # Log sanitization (API keys, PII)
│   ├── SecureAPIKeyStorage.swift     # Keychain integration
│   ├── PotterSettings.swift          # UserDefaults wrapper
│   ├── PotterLogger.swift            # Structured file logging
│   ├── PotterErrors.swift            # 44-case error taxonomy
│   └── Resources/
│       ├── config/prompts.json       # Default prompts
│       └── AppIcon/
└── Tests/                            # 21 test files, 258 tests
    ├── TestBase.swift                # Shared test utilities + storage isolation
    ├── PotterCoreTests.swift
    ├── PotterCoreDITests.swift       # Dependency injection tests
    ├── TextProcessorTests.swift      # Text processing with mocks
    ├── HotkeyCoordinatorTests.swift  # Hotkey parsing + registration
    ├── PipelineIntegrationTests.swift # End-to-end pipeline tests
    ├── ProtocolConformanceTests.swift # Protocol existence + conformance
    ├── ProtocolAdapterTests.swift    # Real→protocol adapter verification
    ├── LLMManagerTests.swift
    └── ...
```

### Core Flow
1. **main.swift** → AppDelegate creates MenuBarManager + PotterCore
2. **PotterCore** → creates **HotkeyCoordinator** (Carbon Event API)
3. Hotkey fires → captures clipboard → **TextProcessor** processes via LLM
4. **LLMManager** (conforms to `LLMProcessing`) → creates `LLMClient` → API call
5. Result replaces clipboard → notifies user via `IconStateDelegate`

### Key Protocols (Protocols.swift)
- `PromptRepository` — prompt CRUD (implemented by PromptService)
- `PromptProviding` — current prompt access (implemented by PromptService)
- `KeyValidationService` — API key management (implemented by APIKeyService)
- `PermissionChecker` — permission checks (implemented by PermissionManager)
- `LLMProcessing` — text processing (implemented by LLMManager)
- `HotkeyProvider` — hotkey registration (implemented by HotkeyCoordinator)
- `LLMClient` — provider-specific LLM calls (OpenAI, Anthropic, Google)
- `StorageBackend` — storage abstraction (UserDefaults)
- `IconStateDelegate` — PotterCore → MenuBarManager communication

### Dependency Injection
- **PotterCore** accepts `init(llmManager:settings:)` — backward compatible defaults
- **TextProcessor** accepts `init(promptProvider:llmProcessor:)` — fully mockable
- **HotkeyCoordinator** extracted from PotterCore — testable without Carbon APIs
- All services have protocol abstractions for test doubles

### Patterns Used
- **DI**: Constructor injection for PotterCore, TextProcessor
- **Protocol**: Every service boundary has a protocol for mocking
- **Adapter**: StorageAdapter wraps storage backends
- **Factory**: LLMManager creates provider-specific clients
- **Observer**: Weak delegate for icon state changes
- **Coordinator**: HotkeyCoordinator manages Carbon Event lifecycle

### Error Handling
`PotterError` enum with 6 categories × 7 cases each (44 total). Each error has user message, technical description, severity, and alert policy. Flow: LLMClient → PotterError → IconState → MenuBarManager display.

## Testing
- **Framework**: XCTest with async/await
- **362 tests** across 21+ files
- **Test isolation**: TestBase provides UserDefaults suite isolation
- **Mock infrastructure**: MockPromptRepository, MockKeyValidationService, MockPermissionChecker, StubLLMProcessor, SpyIconDelegate
- **Integration tests**: Full pipeline tests with mock dependencies
- **Run**: `swift test` or `make test`

## File Locations
- **Dev logs**: `swift-potter/potter_debug.log`
- **Prod logs**: `~/Library/Logs/potter.log`
- **Crash reports**: `~/Library/Logs/DiagnosticReports/Potter*`
- **Settings**: UserDefaults + `~/Library/Application Support/Potter/`
- **Lock file**: `~/.potter.pid`

## Build & Distribution

### Scripts (in `scripts/`)
- `build_app.py` — Core build pipeline: swift build → app bundle → sign → notarize → DMG
- `version_manager.py` — Version get/set/bump (source of truth: Info.plist)
- `release_manager.py` — Release orchestration: version bump, build, GitHub release, appcast
- `release_utils.py` — Git analysis + AI-powered release notes (OpenAI)
- `codename_utils.py` — Deterministic creative version names
- `test_codesigning.sh` — Diagnostic tool for certificate setup

### Code Signing
- **Direct distribution**: `DEVELOPER_ID_APPLICATION`, `DEVELOPER_ID_INSTALLER`, `APPLE_TEAM_ID`
- **Notarization** (optional): `APPLE_ID`, `APPLE_APP_PASSWORD`
- **App Store**: `MAC_APP_STORE_CERTIFICATE`, `MAC_INSTALLER_CERTIFICATE`
- **Entitlements**: `entitlements-direct.plist` (no sandbox) / `entitlements-appstore.plist` (sandboxed)

### Distribution Channels
- **Direct (GitHub)**: Developer ID signed + notarized DMG, Sparkle auto-updates
- **Mac App Store**: Sandboxed build, NSEvent hotkey (no Carbon), no Sparkle

### CI/CD
- GitHub Actions (`.github/workflows/release.yml`): triggered on `v*` tags or manual dispatch
- Imports P12 certs from GitHub Secrets, builds, creates DMG, uploads release

### Requirements
- Python 3.8+ for build scripts
- GitHub CLI (`gh`) for releases
- Xcode Command Line Tools + Swift 5.9+

# Potter Architecture Analysis & Improvement Plan

## Current State Assessment

| Area | Score | Notes |
|------|-------|-------|
| Error Handling | 8/10 | Comprehensive 44-case error taxonomy, good flow |
| Core Services | 7/10 | Good protocols for LLM, storage; well-isolated |
| Code Reuse | 7/10 | LLMClient protocol enables clean provider swap |
| Separation of Concerns | 7/10 | PotterCore split, settings split into focused views |
| Testability | 7/10 | Protocol-based DI, 288 tests, integration tests |
| Dependency Injection | 6/10 | Constructor injection for core services, some singletons remain |
| UI Architecture | 7/10 | Settings split into 9 focused files, no god objects |

**Overall: 7.5/10** — Solid core, good separation, singletons remain.

### What's Working Well
- **LLMClient protocol** — Clean abstraction, 3 implementations swap seamlessly
- **StorageAdapter** — Proper Adapter pattern with `StorageBackend` protocol, test-injectable
- **PotterError** — 44-case taxonomy with severity, user messages, alert policies
- **PromptService** — Focused responsibility, caching with file mod tracking, test file injection
- **SecuritySanitizer** — Composition of specialized sanitizers for log safety
- **Settings UI** — Split into 9 focused files (shell + 5 tab views + model + helpers + hotkey config)
- **Protocol abstractions** — 6 protocols covering all service boundaries
- **TextProcessor + HotkeyCoordinator** — Extracted, testable, DI-enabled

### What Needs Work
- **Remaining singletons** accessed via `.shared` — PotterLogger, LoginItemsManager, AutoUpdateManager
- **Carbon Event API** in HotkeyCoordinator — blocks App Store submission

---

## P0: Critical (Do First)

### 1. ~~Break Up ModernSettingsWindow.swift~~ ✅ DONE

Split 1408-line god object into 9 focused files:

```
ModernSettingsWindow.swift (185 loc) — Shell: window, controller, sidebar navigation
PromptItem.swift            (34 loc) — Data model shared by 15+ files
SettingsHelpers.swift       (46 loc) — App-wide utilities (menu update, data reset)
GeneralSettingsView.swift   (63 loc) — General tab (composes LLMProviderView + HotkeyView)
PromptsSettingsView.swift  (199 loc) — Prompts tab + CRUD (uses stable ID selection)
AboutSettingsView.swift    (299 loc) — About tab + data management
UpdatesSettingsView.swift   (83 loc) — Updates tab
LogsSettingsView.swift     (151 loc) — Log viewer tab
HotkeySettingsView.swift   (328 loc) — Hotkey capture/configuration
```

### 2. Protocol-ize Singletons for Dependency Injection

**Problem**: 8 singletons accessed via `.shared` throughout. Tests can't substitute mocks. Services are tightly coupled to concrete implementations.

```swift
// Before (scattered everywhere)
let service = PromptService.shared
let keys = APIKeyService.shared

// After
protocol PromptRepository {
    func loadPrompts() async throws -> [Prompt]
    func savePrompt(_ prompt: Prompt) async throws
    func deletePrompt(_ id: String) async throws
}

protocol KeyValidationService {
    func validateKey(for provider: LLMProvider) async throws -> Bool
    func getKey(for provider: LLMProvider) -> String?
}

// Inject at construction
class PotterCore {
    init(prompts: PromptRepository, keys: KeyValidationService, ...) { }
}
```

**Priority singletons to protocol-ize**:
1. `PromptService` → `PromptRepository`
2. `APIKeyService` → `KeyValidationService`
3. `PermissionManager` → `PermissionChecker`
4. `PotterLogger` → `Logger` (or use Swift's `os.Logger`)

**Keep as singletons** (truly app-global): `StorageAdapter`, `ProcessManager`

### 3. Split PotterCore.swift (428 loc → 3 files)

**Problem**: Orchestrates hotkeys, text processing, LLM calls, clipboard ops, and state management. Too many reasons to change.

```
PotterCore.swift (428 loc)
  ↓ split into:
├── HotkeyCoordinator.swift    (~120 loc) Carbon Event API, key registration
├── TextProcessor.swift         (~150 loc) Clipboard capture → LLM → paste back
└── PotterCore.swift            (~100 loc) Thin coordinator wiring the above
```

**Benefit**: Can test text processing without Carbon Event APIs. Can swap hotkey implementation for App Store sandbox.

---

## P1: High Priority

### 4. Extract Hotkey Platform Abstraction

**Problem**: Carbon Event API calls directly in PotterCore. 40+ `case` statements for key codes. Impossible to test. Blocks App Store submission.

```swift
protocol HotkeyProvider {
    func register(hotkey: HotkeyCombo, handler: @escaping () -> Void) throws
    func unregister()
}

class CarbonHotkeyProvider: HotkeyProvider { /* current Carbon code */ }
class CGEventHotkeyProvider: HotkeyProvider { /* App Store compatible */ }
class MockHotkeyProvider: HotkeyProvider { /* for tests */ }
```

### 5. Consistent Async/Await

**Problem**: Mix of `async`/`await` and closure callbacks. 16+ `@MainActor` boundaries in PotterCore create confusion about thread safety.

**Solution**:
- All service methods → `async throws`
- Remove closure-based callbacks
- Mark clear `@MainActor` boundaries (UI layer only)
- Use `Task { @MainActor in }` only at UI boundary

### 6. Add Integration Test Layer

**Problem**: ~82 unit tests but no end-to-end workflow tests. UI is completely untested.

```swift
// Test the full pipeline with mock LLM
func testHotkeyToClipboardFlow() async throws {
    let mockLLM = MockLLMClient(response: "improved text")
    let core = PotterCore(
        hotkeys: MockHotkeyProvider(),
        llm: mockLLM,
        prompts: InMemoryPromptRepository()
    )
    core.simulateHotkeyWithClipboard("rough text")
    XCTAssertEqual(mockLLM.lastInput, "rough text")
}
```

### 7. Consolidate Settings UI Files

**Problem**: Three settings windows: `ModernSettingsWindow.swift`, `SettingsWindow.swift`, `SimpleSettingsWindow.swift`. Unclear which is canonical.

**Solution**: Keep Modern (after P0 split), delete the others.

---

## P2: Medium Priority

### 8. Cache Invalidation Strategy
LLMManager caches clients forever. PromptService checks file mod times. No consistent pattern. Define TTL or event-based invalidation.

### 9. Reduce LLMClient.swift Duplication
OpenAI, Anthropic, Google clients share HTTP request/response patterns. Extract `BaseLLMClient` with shared request logic.

### 10. Structured Logging with os.Logger
Replace custom PotterLogger with Apple's `os.Logger` — built-in level filtering, automatic rotation, Console.app integration. Keep file logging as optional debug supplement.

### 11. Extract Icon/Animation Drawing
MenuBarManager (408 loc) mixes icon pixel drawing with menu construction and state management. Split into `IconFactory`, `MenuBuilder`, thin `MenuBarManager`.

---

## Phased Execution

```
Phase 1 (Foundation) ✅ DONE:
  ├── ✅ Define protocols for top 4 singletons
  ├── ✅ Add constructor injection to PotterCore
  └── ✅ Split ModernSettingsWindow into 9 components

Phase 2 (Testability) ✅ DONE:
  ├── ✅ Extract HotkeyCoordinator with protocol
  ├── ✅ Split PotterCore → TextProcessor + Coordinator
  ├── ✅ Add integration tests with mock providers
  └── ✅ Delete redundant settings UI files

Phase 3 (Polish) ✅ DONE:
  ├── ✅ Extract IconFactory + MenuBuilder
  ├── ✅ Reduce LLMClient duplication (BaseLLMClient)
  └── Threading model documented with tests

Remaining:
  ├── Async/await consistency pass
  ├── Protocol-ize PotterLogger (→ os.Logger)
  └── Reduce remaining singletons (LoginItemsManager, AutoUpdateManager)
```

---

## Target Architecture

```
┌─────────────────────────────────────────────┐
│              AppDelegate (main.swift)         │
│  Creates DI container, wires dependencies     │
└──────────┬──────────────┬───────────────────┘
           │              │
    ┌──────▼──────┐ ┌────▼──────────────┐
    │ PotterCore  │ │ MenuBarManager    │
    │ (thin glue) │ │ ├─ IconFactory    │
    └──┬──────┬───┘ │ └─ MenuBuilder    │
       │      │     └───────────────────┘
  ┌────▼──┐ ┌─▼────────────┐
  │Hotkey │ │TextProcessor  │
  │Coord. │ │(clipboard→LLM)│
  └───────┘ └──────┬────────┘
                   │
         ┌─────────▼──────────┐
         │    LLMManager      │
         │ ┌────────────────┐ │
         │ │ «LLMClient»    │ │
         │ │ OpenAI/Claude/ │ │
         │ │ Gemini         │ │
         │ └────────────────┘ │
         └─────────┬──────────┘
                   │
    ┌──────────────▼──────────────┐
    │        Services Layer        │
    │ «PromptRepository»          │
    │ «KeyValidationService»      │
    │ «PermissionChecker»         │
    │ «StorageBackend»            │
    └─────────────────────────────┘
```

All arrows point downward. No cycles. Every boundary is a protocol. Every component testable in isolation.

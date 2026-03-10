# Potter Architecture Analysis & Improvement Plan

## Current State Assessment

| Area | Score | Notes |
|------|-------|-------|
| Error Handling | 8/10 | Comprehensive 44-case error taxonomy, good flow |
| Core Services | 7/10 | Good protocols for LLM, storage; well-isolated |
| Code Reuse | 7/10 | LLMClient protocol enables clean provider swap |
| Separation of Concerns | 5/10 | UI/logic mixing, PotterCore too broad |
| Testability | 5/10 | UI untestable, singletons block mocking |
| Dependency Injection | 4/10 | 8 singletons, hardcoded `.shared` references |
| UI Architecture | 3/10 | 1408-line god object, no component extraction |

**Overall: 6.5/10** — Solid core, weak edges.

### What's Working Well
- **LLMClient protocol** — Clean abstraction, 3 implementations swap seamlessly
- **StorageAdapter** — Proper Adapter pattern with `StorageBackend` protocol, test-injectable
- **PotterError** — 44-case taxonomy with severity, user messages, alert policies
- **PromptService** — Focused responsibility, caching with file mod tracking, test file injection
- **SecuritySanitizer** — Composition of specialized sanitizers for log safety

### What Needs Work
- **ModernSettingsWindow.swift** (1408 lines) — God object handling 5+ concerns
- **8 singletons** accessed via `.shared` — blocks mocking and test isolation
- **PotterCore.swift** (428 lines) — Orchestrates hotkeys + text processing + state
- **3 redundant settings UIs** — ModernSettingsWindow, SettingsWindow, SimpleSettingsWindow
- **Carbon Event API** directly in PotterCore — untestable, blocks App Store

---

## P0: Critical (Do First)

### 1. Break Up ModernSettingsWindow.swift (1408 → ~6 files)

**Problem**: Single file handles API key input, prompt editing, hotkey config, provider selection, log viewing, and settings persistence. Untestable, unmaintainable.

```
ModernSettingsWindow.swift (1408 loc)
  ↓ split into:
├── SettingsWindow.swift          (~100 loc) Shell/navigation only
├── SettingsViewModel.swift       (~150 loc) Business logic, persistence
├── APIKeySettingsView.swift      (~150 loc) Key input + validation UI
├── PromptSettingsView.swift      (~200 loc) Prompt list + CRUD
├── HotkeySettingsView.swift      (~100 loc) Hotkey picker
├── ProviderSettingsView.swift    (~150 loc) LLM provider selection
└── LogViewerView.swift           (~100 loc) Log display + filtering
```

**Benefit**: Each component testable via its view model. Changes to prompt UI don't risk breaking hotkey config.

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
Phase 1 (Foundation) — unblocks everything else:
  ├── Define protocols for top 4 singletons
  ├── Add constructor injection to PotterCore
  └── Split ModernSettingsWindow into components

Phase 2 (Testability):
  ├── Extract HotkeyCoordinator with protocol
  ├── Split PotterCore → TextProcessor + Coordinator
  ├── Add integration tests with mock providers
  └── Delete redundant settings UI files

Phase 3 (Polish):
  ├── Async/await consistency pass
  ├── Extract IconFactory + MenuBuilder
  ├── Reduce LLMClient duplication
  └── Migrate to os.Logger
```

Each phase is independently shippable. Phase 1 unblocks all later work.

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

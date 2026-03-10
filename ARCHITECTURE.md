# Potter Architecture Analysis & Improvement Plan

## Current State Assessment

| Area | Score | Notes |
|------|-------|-------|
| Error Handling | 8/10 | Comprehensive 44-case error taxonomy, good flow |
| Core Services | 8/10 | Full protocol abstractions, platform-abstracted hotkeys |
| Code Reuse | 8/10 | LLMClient protocol, shared HotkeyKeyMapping, BaseLLMClient |
| Separation of Concerns | 8/10 | PotterCore split, settings split, hotkey providers extracted |
| Testability | 8/10 | Protocol-based DI, 315 tests, integration tests, mock providers |
| Dependency Injection | 7/10 | Constructor injection for core + hotkeys, acceptable singletons |
| UI Architecture | 7/10 | Settings split into 9 focused files, no god objects |
| Caching | 7/10 | Event-based invalidation for LLM clients, file mod tracking for prompts |
| Logging | 8/10 | Dual logging: per-component os.Logger + in-memory UI |

**Overall: 8/10** — All planned improvements complete. Only low-ROI singletons remain.

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
- **Remaining singletons** accessed via `.shared` — PotterLogger, LoginItemsManager, AutoUpdateManager (documented as acceptable, low ROI to change)

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

### ~~4. Extract Hotkey Platform Abstraction~~ ✅ DONE

Extracted shared key mapping into `HotkeyKeyMapping` utility. Created `NSEventHotkeyProvider` as sandbox/App Store compatible alternative to Carbon-based `HotkeyCoordinator`. Expanded `HotkeyProvider` protocol with full lifecycle methods. `PotterCore` now accepts any `HotkeyProvider` via constructor injection (defaults to Carbon).

```
HotkeyKeyMapping.swift    — Shared key code/modifier parsing (Carbon + CGEvent)
NSEventHotkeyProvider.swift — NSEvent.addGlobalMonitorForEvents (sandbox compatible)
HotkeyCoordinator.swift   — Carbon Event API (direct distribution, existing)
MockHotkeyProvider         — In tests, for DI verification
```

### ~~5. Consistent Async/Await~~ ✅ DONE

Cleaned up async/await patterns:
- Removed redundant `DispatchQueue.main.async { Task { @MainActor } }` nesting (3 locations)
- Removed unnecessary dispatch in `@MainActor` contexts (PermissionManager)
- Replaced `DispatchQueue.main.sync` with async in PromptService (deadlock fix)
- No callback-based patterns remain — all async operations use async/await

### ~~6. Add Integration Test Layer~~ ✅ DONE (Phase 2)

288 tests including pipeline integration tests with mock dependencies.

### ~~7. Consolidate Settings UI Files~~ ✅ DONE (Phase 2 + P0 #1)

Deleted SettingsWindow.swift and SimpleSettingsWindow.swift. ModernSettingsWindow split into 9 focused files.

---

## P2: Medium Priority

### ~~8. Cache Invalidation Strategy~~ ✅ DONE
LLMManager now invalidates cached LLMClient on API key change (`setAPIKey`) and provider switch (`selectProvider`). PromptService already checks file mod times. Event-based invalidation is now consistent across both.

### ~~9. Reduce LLMClient.swift Duplication~~ ✅ DONE (Phase 3)
Extracted `BaseLLMClient` with shared HTTP utilities.

### ~~10. Structured Logging with os.Logger~~ ✅ DONE (incremental)
PotterLogger now uses per-component os.Logger categories (cached) alongside the existing in-memory log UI. Each component (e.g. "hotkeys", "llm_manager", "core") gets its own `Logger(subsystem:category:)` for Console.app filtering. Existing API unchanged — `ObservableObject` + `logEntries` still drive the Logs UI.

### ~~11. Extract Icon/Animation Drawing~~ ✅ DONE (Phase 3)
Extracted `IconFactory` and `MenuBuilder` from MenuBarManager.

### 12. Remaining Singletons
8 singletons without protocols remain. Analysis shows low ROI for most:
- **PotterLogger** (19 files, ObservableObject) — too invasive to protocol-ize
- **AutoUpdateManager** (dual compile-time implementations) — protocol would make it worse
- **LoginItemsManager, ProcessManager, SecuritySanitizer** — 1 caller each, low impact
Keep as-is; architecture is sound without full DI for these.

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

Phase 4 (Async/Await + Settings Split) ✅ DONE:
  ├── ✅ Split ModernSettingsWindow (1408 loc → 9 files)
  ├── ✅ Clean up redundant dispatch nesting (3 locations)
  ├── ✅ Replace DispatchQueue.main.sync with async (deadlock fix)
  └── ✅ Replace DispatchQueue.main.asyncAfter with Task.sleep in @MainActor contexts

Phase 5 (Platform Abstraction) ✅ DONE:
  ├── ✅ Extract HotkeyKeyMapping shared utility (key codes + modifiers)
  ├── ✅ Create NSEventHotkeyProvider (sandbox/App Store compatible)
  ├── ✅ Expand HotkeyProvider protocol with full lifecycle
  └── ✅ PotterCore accepts injected HotkeyProvider via constructor

Phase 6 (Polish) ✅ DONE:
  ├── ✅ Cache invalidation — LLMManager invalidates on key change + provider switch
  └── ✅ os.Logger — per-component categories, existing API preserved

Remaining (documented as acceptable):
  └── Remaining singletons (P2 #12) — low ROI, architecture is sound
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

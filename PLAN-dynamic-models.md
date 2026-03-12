# Plan: Dynamic Model Selection & Auto-Tiering

## Goal

Replace hardcoded static model lists with runtime model discovery from provider APIs. Add model tiering (Fast/Standard/Thinking) and per-prompt tier configuration. Handle deprecated models gracefully.

## Current State

- **LLMModel** — struct with `id`, `name`, `description`, `provider`. 6 hardcoded models across 3 providers.
- **LLMProvider.models** — returns static arrays (`LLMModel.openAIModels`, etc.)
- **LLMManager** — stores `selectedProvider` + `selectedModel`, passes `model.id` to clients
- **PromptItem** — `id`, `name`, `prompt` only. No model/tier reference.
- **LLMProviderView** — picker iterates `selectedProvider.models` (static)
- **LLMProviderViewModel** — delegates to LLMManager for selection

## Architecture Decisions

1. **ModelRegistry** as new service — fetches, caches, and tiers models. Separate from LLMManager.
2. **LLMProvider.models** becomes dynamic — backed by ModelRegistry cache, falls back to static list.
3. **ModelTier** enum on LLMModel — not a separate entity. Each model has a tier.
4. **Per-prompt tier** — add `modelTier: ModelTier?` to PromptItem (nil = use global default).
5. **No new dependencies** — use URLSession directly for model listing APIs.

## Implementation Steps

### Step 1: ModelTier enum + LLMModel changes

**Files**: `LLMClient.swift`

Add `ModelTier` enum:
```swift
enum ModelTier: String, Codable, CaseIterable {
    case fast      // Small/cheap models for quick transforms
    case standard  // Balanced models
    case thinking  // Reasoning models for complex prompts

    var displayName: String { ... }
    var description: String { ... }
}
```

Add `tier` field to `LLMModel`:
```swift
struct LLMModel: Identifiable, Hashable, Codable {
    let id: String
    let name: String
    let description: String
    let provider: LLMProvider
    let tier: ModelTier
}
```

Update static model lists to include tier. Keep static lists as fallbacks.

**Tests**: Verify all static models have tiers assigned. Verify tier display names.

### Step 2: Model Tiering Heuristic

**Files**: New `ModelTierClassifier.swift`

Create a classifier that auto-assigns tiers to unknown models based on name patterns:
```swift
enum ModelTierClassifier {
    static func classify(_ modelId: String, provider: LLMProvider) -> ModelTier
}
```

Rules:
- **Fast**: contains "mini", "flash", "haiku", "nano", "lite", "small"
- **Thinking**: contains "thinking", "o1", "o3", "o4", "reason"
- **Standard**: everything else (default)

**Tests**: Test classification of known models. Test unknown model defaults to standard.

### Step 3: ModelRegistry service

**Files**: New `ModelRegistry.swift`

```swift
@MainActor
class ModelRegistry: ObservableObject {
    @Published var models: [LLMProvider: [LLMModel]] = [:]
    @Published var lastFetched: [LLMProvider: Date] = [:]
    @Published var isFetching: Bool = false

    private let cacheTTL: TimeInterval = 86400 // 24h

    func getModels(for provider: LLMProvider) -> [LLMModel]
    func refreshModels(for provider: LLMProvider) async
    func refreshAllModels() async
    func modelsForTier(_ tier: ModelTier, provider: LLMProvider) -> [LLMModel]
    func bestModel(for tier: ModelTier, provider: LLMProvider) -> LLMModel?
}
```

**API endpoints** (list models):
- OpenAI: `GET https://api.openai.com/v1/models` → filter chat models
- Anthropic: No list endpoint — use curated list, refresh from known model patterns
- Google: `GET https://generativelanguage.googleapis.com/v1/models?key=KEY` → filter generateContent models

**Cache**: Persist fetched models to `~/Library/Application Support/Potter/model_cache.json` with timestamps.

**Fallback**: On fetch failure, use cached list. If no cache, use static fallback lists from Step 1.

**Tests**:
- Test cache TTL logic (fresh vs stale)
- Test fallback to static models when fetch fails
- Test model filtering (only chat-capable models)
- Test tier assignment for fetched models

### Step 4: Wire ModelRegistry into LLMManager

**Files**: `LLMManager.swift`, `LLMClient.swift`

- `LLMProvider.models` → delegate to `ModelRegistry.shared.getModels(for:)` with static fallback
- `LLMManager.init()` → trigger background model refresh
- `LLMManager.selectProvider()` → refresh models for that provider if stale
- Remove `LLMModel.openAIModels` etc. static arrays (move to `ModelRegistry` as fallbacks)

**Tests**: Verify LLMManager uses registry models. Verify fallback when registry empty.

### Step 5: Per-prompt model tier

**Files**: `PromptItem.swift`, `PromptService.swift`, `PromptEditDialog.swift`

Add to PromptItem:
```swift
struct PromptItem: Identifiable, Equatable, Codable {
    let id: UUID
    var name: String
    var prompt: String
    var modelTier: ModelTier?  // nil = use global default
}
```

Update `PromptEditDialog` — add tier picker (Fast/Standard/Thinking/Default).

Update `TextProcessor.processText()` or `PotterCore.processTextWithLLM()`:
- Check current prompt's `modelTier`
- If set, resolve to best model in that tier via ModelRegistry
- If nil, use LLMManager's globally selected model

**Migration**: Existing prompts decode with `modelTier: nil` (backward compatible via optional).

**Tests**:
- Verify PromptItem encodes/decodes with tier
- Verify backward compat (old prompts without tier decode fine)
- Verify tier resolution in text processing

### Step 6: Update Settings UI

**Files**: `LLMProviderView.swift`, `LLMProviderViewModel.swift`

Changes to LLMProviderView:
- Model picker grouped by tier (Fast / Standard / Thinking sections)
- "Refresh Models" button with last-fetched timestamp
- Loading indicator during refresh
- Show tier badge next to model name

Changes to LLMProviderViewModel:
- Add `refreshModels()` method
- Add `modelsByTier` computed property
- Add `lastFetchedText` computed property

**Tests**: Verify view model exposes grouped models correctly.

### Step 7: Graceful model fallback (in processText)

**Files**: `LLMManager.swift`

In `processText()`, if the selected model returns 404/deprecated:
1. Catch the error
2. Find next best model in same tier from same provider via ModelRegistry
3. Retry with fallback model
4. Log: "Model X unavailable, using Y instead"
5. Update `selectedModel` to the fallback

Note: this is the ONE place where a fallback is appropriate — the user explicitly requested it in FUTURE_PLANS.md.

**Tests**:
- Mock a 404 response, verify fallback model selected
- Verify fallback stays in same tier + provider

## File Change Summary

| File | Change |
|------|--------|
| `LLMClient.swift` | Add `ModelTier` enum, add `tier` to `LLMModel`, update static lists |
| `ModelTierClassifier.swift` | **NEW** — tier classification heuristic |
| `ModelRegistry.swift` | **NEW** — fetch, cache, tier models from provider APIs |
| `LLMManager.swift` | Wire ModelRegistry, add fallback in processText |
| `PromptItem.swift` | Add `modelTier: ModelTier?` field |
| `PromptService.swift` | Handle tier in prompt CRUD (minimal) |
| `PromptEditDialog.swift` | Add tier picker to prompt editor |
| `PotterCore.swift` | Resolve per-prompt tier before calling LLM |
| `LLMProviderView.swift` | Grouped model picker, refresh button, tier badges |
| `LLMProviderViewModel.swift` | Refresh, grouped models, last-fetched |
| Tests (multiple) | New test files for ModelTierClassifier, ModelRegistry, PromptItem tier |

## Execution Order

Steps 1–2 can be done first (pure data model, no API calls).
Step 3 is the core — most complex, requires API testing.
Steps 4–5 wire it in.
Steps 6–7 are the UI and resilience layer.

Each step should compile and pass tests independently.

## Risk Notes

- **Anthropic has no list-models API** — must maintain a curated list or scrape docs. Start with static + classify new ones by pattern.
- **OpenAI returns ALL models** including embeddings, TTS, etc. — need to filter to only chat-completion capable models.
- **Google API key in URL** — model listing also needs the key in the URL path.
- **Per-prompt tier changes PromptItem's Codable** — must be backward compatible (optional field).

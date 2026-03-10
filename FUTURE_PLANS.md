# Potter — Future Plans

## Backlog

### Dynamic Model Selection & Auto-Tiering

**Priority**: HIGH — core UX improvement

**Problem**: Potter maintains static model lists that go stale when providers deprecate or rename models. When a cached model disappears, Potter enters an error state with no recovery path. Individual model names don't matter to most users — they care about speed vs quality.

**Proposed Design**:

1. **Fetch models from provider APIs at runtime**
   - Each provider (OpenAI, Anthropic, Google) has a list-models endpoint
   - Cache the fetched list locally with a TTL (e.g., 24h)
   - On cache miss or expired, fetch fresh; on fetch failure, fall back to cached list
   - Settings UI: "Refresh Models" button to force re-fetch

2. **Auto-tier models into categories**
   - **Fast** — smaller/cheaper models for quick transforms (e.g., GPT-4o-mini, Claude Haiku, Gemini Flash)
   - **Standard** — balanced models (e.g., GPT-4o, Claude Sonnet, Gemini Pro)
   - **Thinking** — reasoning models for complex prompts (e.g., o3, Claude with extended thinking)
   - Tiering heuristic: match on model name patterns or use provider metadata
   - New prompts default to "Fast" tier

3. **Per-prompt model tier config**
   - In the prompt editor, add a tier selector (Fast / Standard / Thinking)
   - "Use thinking models" checkbox as a shortcut for Thinking tier
   - Tier selection stored with the prompt in prompts.json

4. **Graceful model fallback**
   - If the selected model is unavailable (404/deprecated), auto-select the next best model in the same tier from the same provider
   - Show a non-blocking notification: "Model X unavailable, using Y instead"
   - Log the fallback for debugging

5. **Settings UI changes**
   - Remove static model dropdowns
   - Show current tier + resolved model name per provider
   - "Refresh Models" button with last-fetched timestamp
   - Model list viewer (expandable) showing all available models per provider with tier tags

**Files likely affected**: LLMManager.swift, LLMClient.swift, LLMProviderView.swift, LLMProviderViewModel.swift, PromptItem.swift, PromptService.swift, PromptsSettingsView.swift, PromptEditDialog.swift

---

### Remaining Refactoring (Low Priority)

From ARCHITECTURE.md — documented as acceptable to defer:

- **Cache invalidation strategy** — LLMManager caches clients forever, PromptService checks file mod times. Define consistent TTL or event-based invalidation.
- **os.Logger migration** — Replace custom PotterLogger internals with Apple's os.Logger for Console.app integration. Keep existing API surface. High effort (19 files use PotterLogger).
- **Remaining singletons** — PotterLogger (19 files, ObservableObject), AutoUpdateManager (dual compile-time impl), LoginItemsManager, ProcessManager, SecuritySanitizer. Analysis shows low ROI for protocol-ization.

---

### App Store Submission

- **CGEvent hotkey provider** — Current Carbon Event API blocks App Store. Need CGEventHotkeyProvider implementing existing HotkeyProvider protocol.
- **Sandbox compliance** — Audit file access, keychain usage, accessibility APIs for sandbox.

---

### UI Improvements

- **ModernSettingsWindow** — Consider migrating from HSplitView to NavigationSplitView (macOS 13+) for better sidebar behavior.
- **Prompt editor** — Syntax highlighting or preview for prompt text.
- **Dark mode polish** — Audit all views for proper dark mode contrast.

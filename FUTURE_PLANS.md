# Potter — Future Plans

## Completed This Session

### ~~Dynamic Model Selection & Auto-Tiering~~ ✅ DONE (prior session)

Already fully implemented: live API fetch with 24h TTL cache, `ModelTierClassifier` (name-pattern heuristics), per-prompt tier selector in `PromptEditDialog`, tier pickers + "Refresh Models" button in `LLMProviderView`.

---

### ~~Per-Prompt Output Mode (Replace / Append / Prepend)~~ ✅ DONE

`OutputMode` enum on `PromptItem` (.replace / .append / .prepend). Applied in `PotterCore` after streaming completes. Segmented control in `PromptEditDialog`. Backward-compatible decoder. 20 tests.

---

### ~~Processing History Log~~ ✅ DONE

`ProcessingHistoryEntry` + `ProcessingHistoryStore` (serial queue, 500-entry cap, atomic JSON). Written in `PotterCore` after every successful run. "History" Settings tab (`HistorySettingsView`) with split-pane list + detail + Copy + Clear All. 12 tests.

---

### ~~In-Place Selection Processing (Accessibility API)~~ ✅ DONE

`AccessibilityTextProvider` reads selected text via `kAXFocusedUIElementAttribute` + `kAXSelectedTextAttribute`, falls back to clipboard. `writeResult` routes back to AX or clipboard. Integrated into `PotterCore` replacing direct `NSPasteboard` calls. AX write failures silently fall back to clipboard. 9 tests.

---

### ~~Low-Latency UX + Streaming Output~~ ✅ DONE

`streamText` added to `LLMClient` protocol + implemented in all 3 clients (SSE parsing for OpenAI/Anthropic, `alt=sse` for Google). `LLMManager.streamText` exposed. `PotterCore` uses streaming: immediate `setProcessingState()` on hotkey press, progressive clipboard writes for replace mode, accumulate-then-write for append/prepend. 10 tests.

---

### ~~Remaining Refactoring~~ ✅ DONE (prior session)

- ~~Cache invalidation strategy~~ — LLMManager now invalidates on key change + provider switch
- ~~os.Logger migration~~ — Per-component os.Logger categories, existing API preserved
- **Remaining singletons** — Documented as acceptable, low ROI

---

## Backlog

### App Store Submission

- ~~CGEvent hotkey provider~~ ✅ — Created `NSEventHotkeyProvider` (sandbox compatible), `HotkeyKeyMapping` shared utility, PotterCore accepts injected provider
- **Sandbox compliance** — Audit file access, keychain usage, accessibility APIs for sandbox.
  - File access: `ProcessingHistoryStore`, `ProcessingHistory` both write to `~/Library/Application Support/Potter/` — allowed in sandbox with `com.apple.security.files.user-selected.read-write` or App Container entitlement
  - Keychain: `APIKeyService` uses `SecItem*` — allowed in sandbox with `com.apple.security.keychain-access-groups` or standard keychain entitlement
  - Accessibility: `kAXFocusedUIElementAttribute` + `kAXSelectedTextAttribute` — **not allowed in Mac App Store sandbox** (requires `com.apple.security.automation.apple-events` which is rejected). AX provider already falls back to clipboard silently — this is the correct behaviour for sandboxed distribution.
  - Carbon hotkeys (`HotkeyCoordinator`): use `NSEventHotkeyProvider` for App Store build.

---

### UI Improvements

- **ModernSettingsWindow** — Consider migrating from HSplitView to NavigationSplitView (macOS 13+) for better sidebar behavior.
- **Prompt editor** — Syntax highlighting or preview for prompt text.
- **Dark mode polish** — Audit all views for proper dark mode contrast.

---

### Streaming Overlay Window (future enhancement)

The streaming output currently writes directly to clipboard. A floating overlay window would allow users to review and accept/reject the result before it replaces their text. Deferred — current progressive clipboard approach is functional and simpler.

**Proposed**:
- `OverlayWindow.swift` — floating NSPanel near cursor position
- Shows streaming text as it arrives
- ⌘+C to copy, ⌘+V to paste, Esc to dismiss
- Auto-dismiss 2s after last token

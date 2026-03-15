# Potter Bug Audit — March 2026

Proactive audit of issues users would report in the next 3 months.

## Fixed (on `fix/proactive-bug-fixes` branch, not yet merged)

### Race condition on rapid hotkey presses — HIGH
**File:** PotterCore.swift
**Bug:** No guard against concurrent processing. Pressing hotkey twice quickly starts two API calls that compete to write to clipboard.
**Fix:** Added `isProcessing` flag that blocks re-entry until the current request completes or errors.

### No text size limit — HIGH
**File:** PotterCore.swift
**Bug:** Text of any size sent to LLM API. 100k+ chars would get a cryptic 400 error.
**Fix:** Rejects text over 100k chars with a clear error message before sending.

### No explicit request timeouts — MEDIUM
**File:** BaseLLMClient.swift, LLMClient.swift
**Bug:** URLSession uses default timeout. If a provider hangs, the spinner could run for a very long time.
**Fix:** Set `timeoutInterval = 60` on all URLRequest objects.

### Google API key leaked in URL logs — MEDIUM
**File:** LLMClient.swift (GoogleClient.streamText)
**Bug:** Google streaming endpoint had `?key=<apiKey>` in the URL. If logged, the key is exposed.
**Fix:** Moved key to `x-goog-api-key` header.

### `isProcessing` flag stuck forever after "no text" sentinel — CRITICAL
**File:** PotterCore.swift
**Bug:** When the sentinel string "No text was in clipboard" was detected, the function returned without resetting `isProcessing = false`, permanently locking out the hotkey.
**Fix:** Removed the sentinel check entirely (see clipboard sentinel fix below).

### Google API key leaked in ModelRegistry URL — MEDIUM
**File:** ModelRegistry.swift
**Bug:** `fetchGoogleModels()` passed API key as `?key=` in the URL query string. Same issue that was fixed in GoogleClient but missed here.
**Fix:** Moved key to `x-goog-api-key` header.

### Onboarding `resetToFirstStep()` mutated a struct copy — MEDIUM
**File:** OnboardingWindow.swift
**Bug:** `hostingView.rootView.resetToFirstStep()` mutated a copy of the SwiftUI struct. The `@State` `currentStep` was never actually reset.
**Fix:** Replace rootView with a fresh `OnboardingView()` instance. Removed dead `resetToFirstStep()` method.

### Hotkey permanently disabled if settings window closed during capture — HIGH
**File:** HotkeySettingsView.swift
**Bug:** `startHotkeyCapture()` disabled the global hotkey. If the window was closed before capture completed, `enableGlobalHotkey()` was never called.
**Fix:** Added `.onDisappear` to cancel capture and re-enable hotkey.

### `MainActor.assumeIsolated` crash risk in Timer callbacks — HIGH
**File:** PermissionManager.swift
**Bug:** Timer callbacks used `MainActor.assumeIsolated` which calls `fatalError` if not on main thread.
**Fix:** Changed to `Task { @MainActor in }`.

### Delete prompt confirmation dialog bypassed — MEDIUM
**File:** PromptsSettingsView.swift
**Bug:** The `-` button called `deleteSelectedPrompt()` directly instead of showing the existing confirmation dialog.
**Fix:** Button now sets `showingDeleteConfirmation = true`.

### PotterLogger `loggers` dict race condition — MEDIUM
**File:** PotterLogger.swift
**Bug:** The per-component Logger cache was read/written from multiple threads without synchronization.
**Fix:** Added `NSLock` around `loggers` dictionary access.

### Clipboard destroyed on no-text + sentinel pattern removed — MEDIUM
**File:** PotterCore.swift
**Bug:** `handleNoTextAvailable()` cleared the entire pasteboard (including images/files) and wrote a sentinel string. Destructive to non-text clipboard items.
**Fix:** Removed clipboard clearing and sentinel writing. Error state shown without touching pasteboard. Removed the now-unnecessary sentinel check.

## Fixed (already on master)

### Deprecated Anthropic model ID breaks validation — HIGH
**File:** LLMClient.swift, APIKeyService.swift
**Bug:** `claude-3-5-haiku-20241022` was removed by Anthropic. Validation used this hardcoded ID.
**Fix:** Updated static fallback to `claude-haiku-4-5-20251001`. Also changed `performValidation` to fetch live models before validating, so hardcoded IDs are never used for API calls.

## Not yet fixed

### Icon stuck spinning if API call hangs — CRITICAL
**File:** MenuBarManager.swift
**Bug:** No timeout on the processing icon state. If API hangs past the URLRequest timeout (now 60s), the spinner stops because the error handler fires. But if something else blocks (e.g., thread starvation), the spinner could theoretically run forever.
**Suggested fix:** Add a safety timeout in `setProcessingState()` that auto-transitions to error after 90s.

### Streaming returns partial text on network failure — CRITICAL
**File:** LLMClient.swift (all streaming methods)
**Bug:** If the network drops mid-stream, the `for try await` loop throws. The partially assembled text in `assembled` is lost — the throw propagates and the error handler runs. However, in replace mode, partial tokens were already written to clipboard via `onToken`. So the user could end up with a half-written result in their clipboard.
**Suggested fix:** In replace mode, restore the original clipboard text on stream error. Or track whether any tokens were emitted and warn the user.

### Anthropic API version hardcoded to 2023-06-01 — MEDIUM
**File:** LLMClient.swift (lines 228, 264, 298)
**Bug:** If Anthropic deprecates this API version, all Anthropic calls fail.
**Suggested fix:** Update to latest stable version. Consider making it configurable or fetching the supported version from Anthropic's docs.

### Clipboard access not error-checked — MEDIUM
**File:** AccessibilityTextProvider.swift
**Bug:** `NSPasteboard.general.string(forType:)` can fail silently. On future macOS with stricter sandboxing, clipboard access might be denied without warning.
**Suggested fix:** Distinguish between "no text" and "access denied."

### Spinner timer edge case — LOW
**File:** MenuBarManager.swift
**Bug:** If `stopSpinnerAnimation()` is never called (edge case), the 0.1s repeating timer fires forever. `[weak self]` prevents retain cycle but wastes CPU.
**Suggested fix:** Guard in timer callback to invalidate if no longer processing.

### Whitespace-only prompt names allowed — LOW
**File:** PromptService.swift
**Bug:** User can create a prompt with name "   " which displays as blank in the menu.
**Suggested fix:** Trim whitespace before validation.

### AX element validity not checked on write-back — LOW
**File:** AccessibilityTextProvider.swift, PotterCore.swift
**Bug:** If the user switches apps between hotkey press and LLM response, the AXUIElement may be invalid. Write fails silently. (Currently falls back to clipboard, so impact is limited.)

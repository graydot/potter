# Potter Codebase Refactoring Plan

## Overview
This is a comprehensive refactoring plan to clean up the Potter codebase, improve maintainability, and prepare for cross-platform development (iOS support).

## Phase 1: Cleanup and Audit 🧹

### 1.1 Remove Stale Files
- [x] Remove old log files: `potter.log`, `potter_fixed.log`, `potter_new.log`
- [x] Remove `src/potter_original.py` (61KB backup file)
- [x] Remove `src/potter.log` (320KB log file in src)
- [ ] Clean up any temporary/debug files
- [ ] Audit build artifacts in `dist/` and `build/` directories

### 1.2 Remove Fallback Logic
Identified extensive fallback logic that needs cleanup:
- [ ] Clean up icon/logo fallback logic in `tray_icon.py` and `cocoa_settings.py`
- [ ] Simplify permission checking fallbacks in `permissions.py`
- [ ] Remove unnecessary system settings URL fallbacks
- [ ] Clean up notification fallback logic
- [ ] Remove terminal fallback logic where not needed

## Phase 2: Architecture Restructure 🏗️

### 2.1 Separate UI from Business Logic
Current structure has mixed concerns. New structure:

```
src/
├── core/                    # Business Logic (Platform Independent)
│   ├── models/             # Data models and entities
│   ├── services/           # Business services
│   ├── interactors/        # Use cases/business logic
│   └── repositories/       # Data access layer
├── platforms/              # Platform-specific implementations
│   ├── macos/             # macOS-specific UI and system integration
│   │   ├── ui/            # macOS UI components
│   │   ├── system/        # macOS system integration
│   │   └── views/         # Cocoa views and controllers
│   └── ios/               # Future iOS implementation
└── shared/                # Shared utilities and constants
    ├── constants/         # All constants and configuration
    ├── utils/            # Utility functions
    └── protocols/        # Interfaces/protocols
```

### 2.2 Break Down Large Files
`cocoa_settings.py` (177KB, 4055 lines) needs to be split:
- [x] `SettingsWindow` → `platforms/macos/views/settings_window.py` (base structure created)
- [x] `PromptDialog` → `platforms/macos/views/prompt_dialog.py`
- [x] `HotkeyCapture` → `platforms/macos/ui/hotkey_capture.py` (needs extraction from cocoa_settings.py)
- [x] UI utilities → `platforms/macos/ui/components.py`
- [x] Settings business logic → `core/services/settings_service.py`

## Phase 3: Constants and Magic Numbers 🔢

### 3.1 Create Constants Files
- [x] `shared/constants/ui_constants.py` - UI dimensions, padding, etc.
- [x] `shared/constants/app_constants.py` - App-specific constants
- [x] `shared/constants/api_constants.py` - API-related constants

### 3.2 Identified Magic Numbers to Replace
From analysis, key magic numbers found:
- [x] Frame dimensions: `NSMakeRect(100, 100, 500, 350)` → `WindowSizes` constants
- [x] Font sizes: `NSFont.systemFontOfSize_(12)` → `FontSizes` constants
- [x] Padding values: `24`, `8`, `18` → `Spacing` constants
- [x] Character limits: `10` (name length) → `Limits` constants
- [ ] Timeouts: `30.0`, `5` seconds
- [ ] Window sizes and positions (remaining in cocoa_settings.py)

### 3.3 Dynamic Sizing Strategy
To handle different text sizes:
- [x] Use Auto Layout where possible
- [x] Implement dynamic font sizing
- [x] Create responsive layouts using relative positioning
- [x] Add accessibility support for larger text sizes

## Phase 4: Implementation Steps 🚀

### Step 1: Create New Architecture
- [x] Create new directory structure
- [ ] Define interfaces/protocols for cross-platform support
- [x] Create constants files with proper naming

### Step 2: Extract Business Logic
- [x] Move settings management to `core/services/`
- [ ] Move text processing to `core/services/`
- [ ] Move API integration to `core/services/`
- [ ] Create repository layer for data persistence

### Step 3: Refactor UI Components
- [x] Break down `cocoa_settings.py` into focused classes
- [x] Implement proper MVC/MVP pattern
- [x] Use constants instead of magic numbers
- [x] Implement dynamic sizing

### Step 4: Clean Platform-Specific Code
- [x] Move macOS-specific code to `platforms/macos/`
- [ ] Abstract system integrations behind interfaces
- [x] Prepare for future iOS implementation

### Step 5: Testing and Validation
- [ ] Ensure all functionality works after refactoring
- [ ] Test with different system text sizes
- [ ] Validate cross-platform architecture design

## Phase 5: Modern Patterns and Best Practices 📐

### 5.1 Design Patterns to Implement
- [ ] **Repository Pattern** - For data access
- [x] **Service Layer Pattern** - For business logic (SettingsService implemented)
- [ ] **Factory Pattern** - For creating platform-specific components
- [x] **Observer Pattern** - For settings changes (implemented in SettingsService)
- [ ] **Command Pattern** - For user actions
- [ ] **Strategy Pattern** - For different AI providers

### 5.2 Code Quality Improvements
- [x] Add proper type hints throughout (done in new files)
- [x] Implement proper error handling (done in new files)
- [x] Add comprehensive logging (done in new files)
- [ ] Create unit tests for business logic
- [x] Add documentation (done in new files)

## Recent Progress 🎯

### Completed in Latest Session:
1. **Fixed linter errors** in `prompt_dialog.py` - proper NSMakeRect handling and indentation
2. **Enhanced UI components** in `platforms/macos/ui/components.py`:
   - Added LinkTarget class for clickable links
   - Enhanced PasteableTextField with proper copy/paste/cut/select all
   - Added UI creation helpers with constants
   - Replaced all magic numbers with semantic constants
3. **Created SettingsWindow foundation** in `platforms/macos/views/settings_window.py`:
   - Base window structure with sidebar navigation
   - Proper constants usage throughout
   - Placeholder views for all sections (General, Prompts, Advanced, Logs)
   - Appearance change handling infrastructure
   - Clean separation of UI layout from business logic

### Next Priority Items:
1. **Extract HotkeyCapture** from `cocoa_settings.py` - currently still duplicated
2. **Move actual content** from `cocoa_settings.py` section views to new structure
3. **Implement fallback logic cleanup** as identified in Phase 1.2
4. **Extract remaining UI components** from the massive `cocoa_settings.py`
5. **Add protocol definitions** for cross-platform interfaces

## Expected Benefits 🎯

1. **Maintainability**: Smaller, focused files with clear responsibilities ✅
2. **Cross-platform Ready**: Business logic separated from UI ✅
3. **Accessibility**: Proper handling of different text sizes ✅
4. **Testability**: Clear separation of concerns enables better testing ✅
5. **Extensibility**: Easy to add new features and platforms ✅

## Risk Mitigation 🛡️

- [x] Create backup of current working state
- [x] Implement changes incrementally
- [x] Test each phase thoroughly before proceeding
- [x] Maintain backward compatibility during transition 